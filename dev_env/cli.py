#!/usr/bin/env python3
"""
Mrki CLI - Full-Stack Development Environment
Main command-line interface for the Mrki development toolkit
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .project_scaffolder import ProjectScaffolder, ProjectConfig, StackType
from .git_ops import GitOps, CommitMessage
from .code_gen import CodeGenerator, PythonGenerator, JavaScriptGenerator
from .database.manager import DatabaseManager, DatabaseType
from .api_builder.builder import APIBuilder, HTTPMethod, Parameter, ParameterLocation, Response
from .docker.manager import DockerManager
from .testing.manager import TestManager
from .cicd import CICDGenerator, CICDPlatform


def cmd_scaffold(args):
    """Scaffold a new project"""
    config = ProjectConfig(
        name=args.name,
        stack=StackType(args.stack),
        description=args.description,
        author=args.author,
        docker=args.docker,
        ci_cd=args.ci_cd,
        testing=args.testing,
    )
    
    scaffolder = ProjectScaffolder(args.output)
    result = scaffolder.scaffold(config)
    
    print(f"✅ Project '{args.name}' created successfully!")
    print(f"📁 Location: {result['project_path']}")
    print(f"🔧 Stack: {result['stack']}")
    print(f"✨ Features: {', '.join(result['features'])}")
    print(f"📄 Files created: {len(result['created_files'])}")


def cmd_git(args):
    """Git operations"""
    git = GitOps(args.path)
    
    if args.git_command == "status":
        result = git.get_status()
        print(json.dumps(result, indent=2))
    
    elif args.git_command == "commit":
        if args.conventional:
            msg = CommitMessage(
                type=args.type or "feat",
                scope=args.scope,
                description=args.message,
            )
            result = git.commit_conventional(msg)
        else:
            result = git.commit(args.message, all_files=args.all)
        print(f"✅ {result['message']}")
    
    elif args.git_command == "branch":
        if args.action == "create":
            from .git_ops import BranchType
            branch_type = BranchType(args.branch_type) if args.branch_type else None
            result = git.create_branch(args.name, branch_type=branch_type)
        elif args.action == "list":
            result = git.list_branches()
            for branch in result:
                marker = "*" if branch["current"] else " "
                print(f"{marker} {branch['name']}")
            return
        elif args.action == "switch":
            result = git.switch_branch(args.name)
        
        print(f"✅ {result['message']}")


def cmd_db(args):
    """Database operations"""
    manager = DatabaseManager()
    
    if args.db_command == "generate-schema":
        tables = json.loads(args.tables or "[]")
        db_type = DatabaseType(args.db_type)
        schema = manager.generate_schema(tables, db_type)
        print(schema)
    
    elif args.db_command == "generate-erd":
        tables = json.loads(args.tables or "[]")
        erd = manager.generate_erd(tables, args.format)
        print(erd)
    
    elif args.db_command == "create-migration":
        filepath = manager.create_migration(args.name, args.up, args.down)
        print(f"✅ Migration created: {filepath}")


def cmd_api(args):
    """API operations"""
    builder = APIBuilder(args.output)
    
    if args.api_command == "init":
        builder.set_info(args.title, args.version, args.description)
        builder.save_openapi()
        print(f"✅ OpenAPI spec saved to {args.output}/openapi.json")
    
    elif args.api_command == "add-crud":
        from .api_builder.builder import create_crud_endpoints
        
        builder.set_info("API", "1.0.0")
        for endpoint in create_crud_endpoints(args.resource):
            builder.add_endpoint(endpoint)
        
        builder.save_openapi()
        print(f"✅ CRUD endpoints for '{args.resource}' added")
    
    elif args.api_command == "generate-client":
        filepath = builder.generate_client_sdk(args.language, args.output)
        print(f"✅ Client SDK generated: {filepath}")


def cmd_docker(args):
    """Docker operations"""
    manager = DockerManager()
    
    if args.docker_command == "generate":
        files = manager.generate_docker_files(Path(args.path), args.stack)
        print(f"✅ Docker files generated:")
        for f in files:
            print(f"  - {f}")
    
    elif args.docker_command == "k8s":
        files = manager.save_kubernetes_manifests(args.output, args.namespace)
        print(f"✅ Kubernetes manifests generated:")
        for f in files:
            print(f"  - {f}")


def cmd_test(args):
    """Test operations"""
    manager = TestManager()
    
    if args.test_command == "generate":
        files = manager.generate_test_files(Path(args.path), args.stack)
        print(f"✅ Test files generated:")
        for f in files:
            print(f"  - {f}")


def cmd_cicd(args):
    """CI/CD operations"""
    generator = CICDGenerator(args.output)
    
    platform = CICDPlatform(args.platform)
    result = generator.generate(platform, args.stack)
    print(f"✅ CI/CD configuration generated: {result}")


def cmd_code(args):
    """Code generation"""
    generators = {
        "python": PythonGenerator,
        "javascript": JavaScriptGenerator,
    }
    
    gen_class = generators.get(args.language)
    if not gen_class:
        print(f"❌ Unsupported language: {args.language}")
        sys.exit(1)
    
    generator = gen_class(args.output)
    
    if args.code_command == "model":
        from .code_gen.generator import Field, FieldType
        
        fields = []
        for f in args.fields:
            name, type_str = f.split(":")
            field_type = FieldType(type_str)
            fields.append(Field(name, field_type))
        
        code = generator.generate_model(args.name, fields)
        print(code)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="mrki",
        description="Mrki - Full-Stack Development Environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mrki scaffold myapp --stack mern
  mrki git commit -m "Add new feature" --type feat
  mrki db generate-schema --tables '[{"name":"users","columns":[{"name":"id","type":"uuid","primary_key":true}]}]'
  mrki api init --title "My API" --version 1.0.0
  mrki docker generate --stack mern
  mrki cicd --platform github_actions --stack mern
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scaffold command
    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold a new project")
    scaffold_parser.add_argument("name", help="Project name")
    scaffold_parser.add_argument("--stack", choices=[s.value for s in StackType],
                                default="mern", help="Technology stack")
    scaffold_parser.add_argument("--description", default="", help="Project description")
    scaffold_parser.add_argument("--author", default="", help="Project author")
    scaffold_parser.add_argument("--output", default=".", help="Output directory")
    scaffold_parser.add_argument("--docker", action="store_true", default=True,
                                help="Include Docker configuration")
    scaffold_parser.add_argument("--ci-cd", action="store_true", default=True,
                                help="Include CI/CD configuration")
    scaffold_parser.add_argument("--testing", action="store_true", default=True,
                                help="Include testing configuration")
    scaffold_parser.set_defaults(func=cmd_scaffold)
    
    # Git command
    git_parser = subparsers.add_parser("git", help="Git operations")
    git_subparsers = git_parser.add_subparsers(dest="git_command", help="Git commands")
    
    git_status = git_subparsers.add_parser("status", help="Get repository status")
    git_status.add_argument("--path", default=".", help="Repository path")
    
    git_commit = git_subparsers.add_parser("commit", help="Create a commit")
    git_commit.add_argument("-m", "--message", required=True, help="Commit message")
    git_commit.add_argument("--conventional", action="store_true", help="Use conventional commits")
    git_commit.add_argument("--type", choices=GitOps.COMMIT_TYPES, help="Commit type")
    git_commit.add_argument("--scope", help="Commit scope")
    git_commit.add_argument("--all", action="store_true", help="Stage all changes")
    git_commit.add_argument("--path", default=".", help="Repository path")
    
    git_branch = git_subparsers.add_parser("branch", help="Branch operations")
    git_branch.add_argument("action", choices=["create", "list", "switch", "delete"],
                           help="Branch action")
    git_branch.add_argument("--name", help="Branch name")
    git_branch.add_argument("--branch-type", choices=["feature", "bugfix", "hotfix", "release"],
                           help="Branch type prefix")
    git_branch.add_argument("--path", default=".", help="Repository path")
    
    git_parser.set_defaults(func=cmd_git)
    
    # Database command
    db_parser = subparsers.add_parser("db", help="Database operations")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="Database commands")
    
    db_schema = db_subparsers.add_parser("generate-schema", help="Generate database schema")
    db_schema.add_argument("--tables", help="Tables JSON definition")
    db_schema.add_argument("--db-type", choices=[t.value for t in DatabaseType],
                          default="postgresql", help="Database type")
    
    db_erd = db_subparsers.add_parser("generate-erd", help="Generate ERD diagram")
    db_erd.add_argument("--tables", help="Tables JSON definition")
    db_erd.add_argument("--format", choices=["mermaid", "dbml"], default="mermaid",
                       help="ERD format")
    
    db_migrate = db_subparsers.add_parser("create-migration", help="Create migration")
    db_migrate.add_argument("name", help="Migration name")
    db_migrate.add_argument("--up", default="", help="Up migration SQL")
    db_migrate.add_argument("--down", default="", help="Down migration SQL")
    
    db_parser.set_defaults(func=cmd_db)
    
    # API command
    api_parser = subparsers.add_parser("api", help="API operations")
    api_subparsers = api_parser.add_subparsers(dest="api_command", help="API commands")
    
    api_init = api_subparsers.add_parser("init", help="Initialize API spec")
    api_init.add_argument("--title", default="API", help="API title")
    api_init.add_argument("--version", default="1.0.0", help="API version")
    api_init.add_argument("--description", default="", help="API description")
    api_init.add_argument("--output", default=".", help="Output directory")
    
    api_crud = api_subparsers.add_parser("add-crud", help="Add CRUD endpoints")
    api_crud.add_argument("resource", help="Resource name")
    api_crud.add_argument("--output", default=".", help="Output directory")
    
    api_client = api_subparsers.add_parser("generate-client", help="Generate client SDK")
    api_client.add_argument("language", choices=["typescript", "javascript", "python", "go"],
                           help="Target language")
    api_client.add_argument("--output", default="./client", help="Output directory")
    
    api_parser.set_defaults(func=cmd_api)
    
    # Docker command
    docker_parser = subparsers.add_parser("docker", help="Docker operations")
    docker_subparsers = docker_parser.add_subparsers(dest="docker_command", help="Docker commands")
    
    docker_gen = docker_subparsers.add_parser("generate", help="Generate Docker files")
    docker_gen.add_argument("--path", default=".", help="Project path")
    docker_gen.add_argument("--stack", default="mern", help="Stack type")
    
    docker_k8s = docker_subparsers.add_parser("k8s", help="Generate Kubernetes manifests")
    docker_k8s.add_argument("--output", default="./k8s", help="Output directory")
    docker_k8s.add_argument("--namespace", default="default", help="Kubernetes namespace")
    
    docker_parser.set_defaults(func=cmd_docker)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test operations")
    test_subparsers = test_parser.add_subparsers(dest="test_command", help="Test commands")
    
    test_gen = test_subparsers.add_parser("generate", help="Generate test files")
    test_gen.add_argument("--path", default=".", help="Project path")
    test_gen.add_argument("--stack", default="mern", help="Stack type")
    
    test_parser.set_defaults(func=cmd_test)
    
    # CI/CD command
    cicd_parser = subparsers.add_parser("cicd", help="CI/CD operations")
    cicd_parser.add_argument("--platform", choices=[p.value for p in CICDPlatform],
                            default="github_actions", help="CI/CD platform")
    cicd_parser.add_argument("--stack", default="mern", help="Stack type")
    cicd_parser.add_argument("--output", default=".", help="Output directory")
    cicd_parser.set_defaults(func=cmd_cicd)
    
    # Code generation command
    code_parser = subparsers.add_parser("code", help="Code generation")
    code_subparsers = code_parser.add_subparsers(dest="code_command", help="Code commands")
    
    code_model = code_subparsers.add_parser("model", help="Generate model code")
    code_model.add_argument("language", choices=["python", "javascript"], help="Target language")
    code_model.add_argument("name", help="Model name")
    code_model.add_argument("--fields", nargs="+", default=[], help="Fields (name:type)")
    code_model.add_argument("--output", default=".", help="Output directory")
    
    code_parser.set_defaults(func=cmd_code)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
