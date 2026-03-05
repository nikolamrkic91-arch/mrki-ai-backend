#!/usr/bin/env python3
"""
Mrki Git Operations Module
Handles version control automation, branching, commits, and repository management
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json


class GitError(Exception):
    """Custom exception for Git operations"""
    pass


class BranchType(Enum):
    """Standard branch types following GitFlow"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    RELEASE = "release"
    DEVELOP = "develop"
    MAIN = "main"


@dataclass
class CommitMessage:
    """Structured commit message"""
    type: str  # feat, fix, docs, style, refactor, test, chore
    scope: Optional[str]
    description: str
    body: Optional[str] = None
    footer: Optional[str] = None
    breaking: bool = False
    
    def __str__(self) -> str:
        scope_str = f"({self.scope})" if self.scope else ""
        breaking_str = "!" if self.breaking else ""
        msg = f"{self.type}{scope_str}{breaking_str}: {self.description}"
        if self.body:
            msg += f"\n\n{self.body}"
        if self.footer:
            msg += f"\n\n{self.footer}"
        return msg


@dataclass
class RepositoryInfo:
    """Repository metadata"""
    name: str
    remote_url: Optional[str]
    current_branch: str
    branches: List[str]
    commits_ahead: int
    commits_behind: int
    is_clean: bool
    modified_files: List[str]
    untracked_files: List[str]


class GitOps:
    """Git operations manager"""
    
    # Conventional commit types
    COMMIT_TYPES = [
        "feat",      # New feature
        "fix",       # Bug fix
        "docs",      # Documentation
        "style",     # Code style (formatting)
        "refactor",  # Code refactoring
        "perf",      # Performance improvements
        "test",      # Tests
        "chore",     # Maintenance tasks
        "ci",        # CI/CD changes
        "build",     # Build system
        "revert",    # Revert changes
    ]
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self._ensure_git_repo()
    
    def _ensure_git_repo(self):
        """Ensure we're in a git repository"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise GitError(f"Not a git repository: {self.repo_path}")
    
    def _run_git(self, args: List[str], check: bool = True) -> Tuple[int, str, str]:
        """Run a git command and return (returncode, stdout, stderr)"""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            if check:
                raise GitError(f"Git command failed: {e.stderr}")
            return e.returncode, e.stdout, e.stderr
    
    # Repository initialization
    def init(self, bare: bool = False) -> Dict[str, Any]:
        """Initialize a new git repository"""
        args = ["init"]
        if bare:
            args.append("--bare")
        
        returncode, stdout, stderr = self._run_git(args)
        
        return {
            "success": returncode == 0,
            "message": stdout.strip(),
            "path": str(self.repo_path)
        }
    
    def clone(self, url: str, target_dir: Optional[str] = None, 
              branch: Optional[str] = None, depth: Optional[int] = None) -> Dict[str, Any]:
        """Clone a repository"""
        args = ["clone"]
        
        if branch:
            args.extend(["-b", branch])
        if depth:
            args.extend(["--depth", str(depth)])
        
        args.append(url)
        if target_dir:
            args.append(target_dir)
        
        returncode, stdout, stderr = self._run_git(args)
        
        return {
            "success": returncode == 0,
            "message": stdout.strip() or stderr.strip(),
            "url": url,
            "target": target_dir or url.split("/")[-1].replace(".git", "")
        }
    
    # Branch operations
    def create_branch(self, name: str, from_branch: Optional[str] = None,
                      branch_type: Optional[BranchType] = None) -> Dict[str, Any]:
        """Create a new branch"""
        # Format branch name with type prefix
        if branch_type and not name.startswith(branch_type.value):
            full_name = f"{branch_type.value}/{name}"
        else:
            full_name = name
        
        args = ["checkout", "-b", full_name]
        if from_branch:
            args.append(from_branch)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "branch": full_name,
            "from": from_branch or "current",
            "message": stdout.strip() or stderr.strip()
        }
    
    def switch_branch(self, name: str, create: bool = False) -> Dict[str, Any]:
        """Switch to a branch"""
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(name)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "branch": name,
            "message": stdout.strip() or stderr.strip()
        }
    
    def list_branches(self, remote: bool = False, merged: bool = False,
                      no_merged: bool = False) -> List[Dict[str, str]]:
        """List branches"""
        args = ["branch", "-vv"]
        
        if remote:
            args.append("-r")
        if merged:
            args.append("--merged")
        if no_merged:
            args.append("--no-merged")
        
        _, stdout, _ = self._run_git(args)
        
        branches = []
        for line in stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            # Parse branch line
            current = line.startswith("*")
            parts = line.replace("*", "").strip().split()
            
            if parts:
                branches.append({
                    "name": parts[0],
                    "current": current,
                    "commit": parts[1] if len(parts) > 1 else "",
                    "message": " ".join(parts[2:]) if len(parts) > 2 else ""
                })
        
        return branches
    
    def delete_branch(self, name: str, force: bool = False, remote: bool = False) -> Dict[str, Any]:
        """Delete a branch"""
        if remote:
            args = ["push", "origin", "--delete", name]
        else:
            args = ["branch", "-D" if force else "-d", name]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "branch": name,
            "remote": remote,
            "message": stdout.strip() or stderr.strip()
        }
    
    def merge_branch(self, source: str, target: Optional[str] = None,
                     no_ff: bool = False, squash: bool = False) -> Dict[str, Any]:
        """Merge a branch"""
        # Switch to target if specified
        if target:
            self.switch_branch(target)
        
        args = ["merge"]
        if no_ff:
            args.append("--no-ff")
        if squash:
            args.append("--squash")
        args.append(source)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "source": source,
            "target": target or self.get_current_branch(),
            "message": stdout.strip() or stderr.strip()
        }
    
    def rebase_branch(self, onto: str, interactive: bool = False) -> Dict[str, Any]:
        """Rebase current branch"""
        args = ["rebase"]
        if interactive:
            args.append("-i")
        args.append(onto)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "onto": onto,
            "message": stdout.strip() or stderr.strip()
        }
    
    # Commit operations
    def commit(self, message: str, files: Optional[List[str]] = None,
               amend: bool = False, no_verify: bool = False) -> Dict[str, Any]:
        """Create a commit"""
        # Stage files if specified
        if files:
            self.add(files)
        
        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")
        if no_verify:
            args.append("--no-verify")
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "message": message,
            "amend": amend,
            "output": stdout.strip() or stderr.strip()
        }
    
    def commit_conventional(self, commit_msg: CommitMessage, 
                           files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a conventional commit"""
        return self.commit(str(commit_msg), files)
    
    def add(self, files: List[str], all_files: bool = False) -> Dict[str, Any]:
        """Stage files"""
        args = ["add"]
        
        if all_files:
            args.append(".")
        else:
            args.extend(files)
        
        returncode, stdout, stderr = self._run_git(args)
        
        return {
            "success": returncode == 0,
            "files": files if not all_files else ["all"],
            "message": stdout.strip() or stderr.strip()
        }
    
    def unstage(self, files: List[str]) -> Dict[str, Any]:
        """Unstage files"""
        args = ["reset", "HEAD"] + files
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "files": files,
            "message": stdout.strip() or stderr.strip()
        }
    
    def reset(self, mode: str = "soft", commit: str = "HEAD~1") -> Dict[str, Any]:
        """Reset to a commit"""
        args = ["reset", f"--{mode}", commit]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "mode": mode,
            "commit": commit,
            "message": stdout.strip() or stderr.strip()
        }
    
    def stash(self, message: Optional[str] = None, include_untracked: bool = False) -> Dict[str, Any]:
        """Stash changes"""
        args = ["stash", "push"]
        
        if message:
            args.extend(["-m", message])
        if include_untracked:
            args.append("-u")
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "message": message or "WIP",
            "output": stdout.strip() or stderr.strip()
        }
    
    def stash_pop(self, index: Optional[int] = None) -> Dict[str, Any]:
        """Pop stash"""
        args = ["stash", "pop"]
        if index is not None:
            args.append(f"stash@{{{index}}}")
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "index": index,
            "output": stdout.strip() or stderr.strip()
        }
    
    def stash_list(self) -> List[Dict[str, str]]:
        """List stashes"""
        args = ["stash", "list"]
        
        _, stdout, _ = self._run_git(args, check=False)
        
        stashes = []
        for line in stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    stashes.append({
                        "index": parts[0].strip(),
                        "branch": parts[1].strip() if len(parts) > 1 else "",
                        "message": parts[2].strip() if len(parts) > 2 else ""
                    })
        
        return stashes
    
    # Remote operations
    def add_remote(self, name: str, url: str) -> Dict[str, Any]:
        """Add a remote"""
        args = ["remote", "add", name, url]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "name": name,
            "url": url,
            "message": stdout.strip() or stderr.strip()
        }
    
    def remove_remote(self, name: str) -> Dict[str, Any]:
        """Remove a remote"""
        args = ["remote", "remove", name]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "name": name,
            "message": stdout.strip() or stderr.strip()
        }
    
    def list_remotes(self) -> List[Dict[str, str]]:
        """List remotes"""
        args = ["remote", "-v"]
        
        _, stdout, _ = self._run_git(args)
        
        remotes = {}
        for line in stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                url = parts[1]
                remote_type = "fetch" if "(fetch)" in line else "push"
                
                if name not in remotes:
                    remotes[name] = {"name": name}
                remotes[name][remote_type] = url
        
        return list(remotes.values())
    
    def fetch(self, remote: Optional[str] = None, 
              prune: bool = False, all_remotes: bool = False) -> Dict[str, Any]:
        """Fetch from remote"""
        args = ["fetch"]
        
        if prune:
            args.append("--prune")
        if all_remotes:
            args.append("--all")
        if remote:
            args.append(remote)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "remote": remote or "all",
            "message": stdout.strip() or stderr.strip()
        }
    
    def pull(self, remote: str = "origin", branch: Optional[str] = None,
             rebase: bool = False) -> Dict[str, Any]:
        """Pull from remote"""
        args = ["pull"]
        
        if rebase:
            args.append("--rebase")
        
        args.append(remote)
        if branch:
            args.append(branch)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "remote": remote,
            "branch": branch or "current",
            "message": stdout.strip() or stderr.strip()
        }
    
    def push(self, remote: str = "origin", branch: Optional[str] = None,
             force: bool = False, set_upstream: bool = False) -> Dict[str, Any]:
        """Push to remote"""
        args = ["push"]
        
        if force:
            args.append("--force-with-lease")
        if set_upstream:
            args.append("-u")
        
        args.append(remote)
        if branch:
            args.append(branch)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "remote": remote,
            "branch": branch or "current",
            "message": stdout.strip() or stderr.strip()
        }
    
    # Information operations
    def get_status(self) -> Dict[str, Any]:
        """Get repository status"""
        args = ["status", "--porcelain", "-b"]
        
        _, stdout, _ = self._run_git(args)
        
        lines = stdout.strip().split("\n")
        
        # Parse branch info from first line
        branch_line = lines[0] if lines else ""
        branch_match = re.search(r'## (.+?)(?:\.\.\.|$)', branch_line)
        current_branch = branch_match.group(1) if branch_match else "unknown"
        
        # Parse file statuses
        staged = []
        unstaged = []
        untracked = []
        
        for line in lines[1:]:
            if not line.strip():
                continue
            
            status = line[:2]
            filename = line[3:].strip()
            
            if status[0] != ' ' and status[0] != '?':
                staged.append({"file": filename, "status": status[0]})
            if status[1] != ' ':
                unstaged.append({"file": filename, "status": status[1]})
            if status == '??':
                untracked.append(filename)
        
        return {
            "branch": current_branch,
            "is_clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked
        }
    
    def get_current_branch(self) -> str:
        """Get current branch name"""
        args = ["rev-parse", "--abbrev-ref", "HEAD"]
        
        _, stdout, _ = self._run_git(args)
        return stdout.strip()
    
    def get_log(self, count: int = 10, oneline: bool = True,
                branch: Optional[str] = None, author: Optional[str] = None,
                since: Optional[str] = None, until: Optional[str] = None) -> List[Dict[str, str]]:
        """Get commit log"""
        args = ["log"]
        
        if oneline:
            args.append("--oneline")
        
        format_str = "%H|%an|%ae|%ad|%s"
        args.extend([f"--format={format_str}", f"-n", str(count)])
        
        if author:
            args.extend(["--author", author])
        if since:
            args.extend(["--since", since])
        if until:
            args.extend(["--until", until])
        if branch:
            args.append(branch)
        
        _, stdout, _ = self._run_git(args)
        
        commits = []
        for line in stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            parts = line.split("|", 4)
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0][:7] if oneline else parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                })
        
        return commits
    
    def get_info(self) -> RepositoryInfo:
        """Get comprehensive repository info"""
        status = self.get_status()
        
        # Get remote URL
        remotes = self.list_remotes()
        remote_url = remotes[0].get("fetch") if remotes else None
        
        # Get branch list
        branches = self.list_branches()
        branch_names = [b["name"] for b in branches]
        
        # Get ahead/behind count
        args = ["rev-list", "--left-right", "--count", f"{status['branch']}...origin/{status['branch']}"]
        _, stdout, _ = self._run_git(args, check=False)
        
        ahead, behind = 0, 0
        if stdout.strip():
            counts = stdout.strip().split()
            if len(counts) == 2:
                ahead, behind = int(counts[0]), int(counts[1])
        
        return RepositoryInfo(
            name=self.repo_path.name,
            remote_url=remote_url,
            current_branch=status["branch"],
            branches=branch_names,
            commits_ahead=ahead,
            commits_behind=behind,
            is_clean=status["is_clean"],
            modified_files=[f["file"] for f in status["unstaged"]],
            untracked_files=status["untracked"]
        )
    
    def get_diff(self, staged: bool = False, file: Optional[str] = None) -> str:
        """Get diff"""
        args = ["diff"]
        
        if staged:
            args.append("--staged")
        if file:
            args.append(file)
        
        _, stdout, _ = self._run_git(args, check=False)
        return stdout
    
    def get_blame(self, file: str, lines: Optional[Tuple[int, int]] = None) -> List[Dict[str, str]]:
        """Get blame for a file"""
        args = ["blame", "--porcelain", file]
        
        if lines:
            args.extend(["-L", f"{lines[0]},{lines[1]}"])
        
        _, stdout, _ = self._run_git(args, check=False)
        
        blame_info = []
        current_commit = {}
        
        for line in stdout.strip().split("\n"):
            if line.startswith("\t"):
                # Code line
                if current_commit:
                    current_commit["code"] = line[1:]
                    blame_info.append(current_commit)
                    current_commit = {}
            elif line.startswith("author "):
                current_commit["author"] = line[7:]
            elif line.startswith("author-time "):
                import datetime
                timestamp = int(line[12:])
                current_commit["date"] = datetime.datetime.fromtimestamp(timestamp).isoformat()
            elif line.startswith("summary "):
                current_commit["message"] = line[8:]
        
        return blame_info
    
    # Tag operations
    def create_tag(self, name: str, message: Optional[str] = None,
                   annotated: bool = False) -> Dict[str, Any]:
        """Create a tag"""
        args = ["tag"]
        
        if annotated or message:
            args.append("-a")
        if message:
            args.extend(["-m", message])
        
        args.append(name)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "tag": name,
            "message": message,
            "output": stdout.strip() or stderr.strip()
        }
    
    def delete_tag(self, name: str, remote: bool = False) -> Dict[str, Any]:
        """Delete a tag"""
        if remote:
            args = ["push", "--delete", "origin", name]
        else:
            args = ["tag", "-d", name]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "tag": name,
            "remote": remote,
            "output": stdout.strip() or stderr.strip()
        }
    
    def list_tags(self, pattern: Optional[str] = None) -> List[Dict[str, str]]:
        """List tags"""
        args = ["tag", "-l", "-n1"]
        
        if pattern:
            args.append(pattern)
        
        _, stdout, _ = self._run_git(args, check=False)
        
        tags = []
        for line in stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            parts = line.split(None, 1)
            if parts:
                tags.append({
                    "name": parts[0],
                    "message": parts[1] if len(parts) > 1 else ""
                })
        
        return tags
    
    def push_tags(self, remote: str = "origin") -> Dict[str, Any]:
        """Push tags to remote"""
        args = ["push", remote, "--tags"]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "remote": remote,
            "output": stdout.strip() or stderr.strip()
        }
    
    # Configuration
    def config_get(self, key: str, global_config: bool = False) -> Optional[str]:
        """Get config value"""
        args = ["config"]
        if global_config:
            args.append("--global")
        args.append(key)
        
        _, stdout, _ = self._run_git(args, check=False)
        return stdout.strip() or None
    
    def config_set(self, key: str, value: str, global_config: bool = False) -> Dict[str, Any]:
        """Set config value"""
        args = ["config"]
        if global_config:
            args.append("--global")
        args.extend([key, value])
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "key": key,
            "value": value,
            "global": global_config
        }
    
    # Hooks
    def install_hook(self, hook_name: str, script: str) -> Dict[str, Any]:
        """Install a git hook"""
        hooks_dir = self.repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        hook_file = hooks_dir / hook_name
        hook_content = f"#!/bin/sh\n{script}"
        hook_file.write_text(hook_content)
        hook_file.chmod(0o755)
        
        return {
            "success": True,
            "hook": hook_name,
            "path": str(hook_file)
        }
    
    def setup_conventional_commits_hook(self) -> Dict[str, Any]:
        """Setup commit-msg hook for conventional commits"""
        script = '''
commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# Conventional commit pattern
pattern="^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\\(.+\\))?!?: .+"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "Error: Commit message does not follow conventional commits format."
    echo "Format: <type>[(scope)]: <description>"
    echo "Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert"
    exit 1
fi
'''
        return self.install_hook("commit-msg", script)
    
    # Advanced operations
    def cherry_pick(self, commits: List[str], no_commit: bool = False) -> Dict[str, Any]:
        """Cherry-pick commits"""
        args = ["cherry-pick"]
        
        if no_commit:
            args.append("-n")
        
        args.extend(commits)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "commits": commits,
            "output": stdout.strip() or stderr.strip()
        }
    
    def bisect_start(self, bad_commit: str, good_commit: str) -> Dict[str, Any]:
        """Start bisect"""
        self._run_git(["bisect", "start"])
        self._run_git(["bisect", "bad", bad_commit])
        self._run_git(["bisect", "good", good_commit])
        
        return {
            "success": True,
            "bad": bad_commit,
            "good": good_commit
        }
    
    def bisect_good(self) -> Dict[str, Any]:
        """Mark current commit as good in bisect"""
        _, stdout, _ = self._run_git(["bisect", "good"])
        return {"success": True, "output": stdout.strip()}
    
    def bisect_bad(self) -> Dict[str, Any]:
        """Mark current commit as bad in bisect"""
        _, stdout, _ = self._run_git(["bisect", "bad"])
        return {"success": True, "output": stdout.strip()}
    
    def bisect_reset(self) -> Dict[str, Any]:
        """Reset bisect"""
        self._run_git(["bisect", "reset"])
        return {"success": True}
    
    def worktree_add(self, path: str, branch: str) -> Dict[str, Any]:
        """Add a worktree"""
        args = ["worktree", "add", path, branch]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "path": path,
            "branch": branch,
            "output": stdout.strip() or stderr.strip()
        }
    
    def worktree_list(self) -> List[Dict[str, str]]:
        """List worktrees"""
        args = ["worktree", "list", "--porcelain"]
        
        _, stdout, _ = self._run_git(args)
        
        worktrees = []
        current = {}
        
        for line in stdout.strip().split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line[9:]}
            elif line.startswith("HEAD "):
                current["head"] = line[5:]
            elif line.startswith("branch "):
                current["branch"] = line[7:]
        
        if current:
            worktrees.append(current)
        
        return worktrees
    
    def worktree_remove(self, path: str) -> Dict[str, Any]:
        """Remove a worktree"""
        args = ["worktree", "remove", path]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "path": path,
            "output": stdout.strip() or stderr.strip()
        }
    
    # Submodule operations
    def submodule_add(self, url: str, path: Optional[str] = None) -> Dict[str, Any]:
        """Add a submodule"""
        args = ["submodule", "add", url]
        if path:
            args.append(path)
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "url": url,
            "path": path,
            "output": stdout.strip() or stderr.strip()
        }
    
    def submodule_update(self, init: bool = False, recursive: bool = False) -> Dict[str, Any]:
        """Update submodules"""
        args = ["submodule", "update"]
        
        if init:
            args.append("--init")
        if recursive:
            args.append("--recursive")
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "output": stdout.strip() or stderr.strip()
        }
    
    # Large file operations
    def lfs_track(self, pattern: str) -> Dict[str, Any]:
        """Track files with Git LFS"""
        args = ["lfs", "track", pattern]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "pattern": pattern,
            "output": stdout.strip() or stderr.strip()
        }
    
    def lfs_untrack(self, pattern: str) -> Dict[str, Any]:
        """Untrack files from Git LFS"""
        args = ["lfs", "untrack", pattern]
        
        returncode, stdout, stderr = self._run_git(args, check=False)
        
        return {
            "success": returncode == 0,
            "pattern": pattern,
            "output": stdout.strip() or stderr.strip()
        }


def main():
    """CLI interface for Git operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mrki Git Operations")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize repository")
    init_parser.add_argument("--bare", action="store_true", help="Create bare repository")
    
    # Status command
    subparsers.add_parser("status", help="Get repository status")
    
    # Branch commands
    branch_parser = subparsers.add_parser("branch", help="Branch operations")
    branch_parser.add_argument("action", choices=["create", "list", "delete", "switch"])
    branch_parser.add_argument("name", nargs="?", help="Branch name")
    branch_parser.add_argument("--from", dest="from_branch", help="Create from branch")
    branch_parser.add_argument("--type", choices=[t.value for t in BranchType], help="Branch type")
    
    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Create commit")
    commit_parser.add_argument("message", help="Commit message")
    commit_parser.add_argument("--type", choices=GitOps.COMMIT_TYPES, help="Conventional commit type")
    commit_parser.add_argument("--scope", help="Commit scope")
    commit_parser.add_argument("--amend", action="store_true", help="Amend previous commit")
    
    # Log command
    log_parser = subparsers.add_parser("log", help="Show commit log")
    log_parser.add_argument("-n", type=int, default=10, help="Number of commits")
    
    # Push/Pull commands
    push_parser = subparsers.add_parser("push", help="Push to remote")
    push_parser.add_argument("--remote", default="origin", help="Remote name")
    push_parser.add_argument("--branch", help="Branch name")
    push_parser.add_argument("--force", action="store_true", help="Force push")
    
    pull_parser = subparsers.add_parser("pull", help="Pull from remote")
    pull_parser.add_argument("--remote", default="origin", help="Remote name")
    pull_parser.add_argument("--rebase", action="store_true", help="Rebase instead of merge")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    git = GitOps()
    
    if args.command == "init":
        result = git.init(bare=args.bare)
        print(json.dumps(result, indent=2))
    
    elif args.command == "status":
        result = git.get_status()
        print(json.dumps(result, indent=2))
    
    elif args.command == "branch":
        if args.action == "create":
            branch_type = BranchType(args.type) if args.type else None
            result = git.create_branch(args.name, args.from_branch, branch_type)
            print(json.dumps(result, indent=2))
        elif args.action == "list":
            result = git.list_branches()
            print(json.dumps(result, indent=2))
        elif args.action == "delete":
            result = git.delete_branch(args.name)
            print(json.dumps(result, indent=2))
        elif args.action == "switch":
            result = git.switch_branch(args.name)
            print(json.dumps(result, indent=2))
    
    elif args.command == "commit":
        if args.type:
            msg = CommitMessage(
                type=args.type,
                scope=args.scope,
                description=args.message
            )
            result = git.commit_conventional(msg, all_files=True)
        else:
            result = git.commit(args.message, all_files=True, amend=args.amend)
        print(json.dumps(result, indent=2))
    
    elif args.command == "log":
        result = git.get_log(count=args.n)
        print(json.dumps(result, indent=2))
    
    elif args.command == "push":
        result = git.push(remote=args.remote, branch=args.branch, force=args.force)
        print(json.dumps(result, indent=2))
    
    elif args.command == "pull":
        result = git.pull(remote=args.remote, rebase=args.rebase)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
