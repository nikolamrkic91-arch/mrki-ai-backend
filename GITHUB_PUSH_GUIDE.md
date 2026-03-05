# GitHub Push Guide for Mrki

## Quick Push Instructions

### Option 1: Using GitHub CLI (Recommended)

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Windows: winget install --id GitHub.cli
# Linux: see https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Authenticate with GitHub
gh auth login

# Create a new private repository and push
cd /tmp/mrki
gh repo create mrki --private --source=. --push

# Or create public repository
git remote add origin https://github.com/YOUR_USERNAME/mrki.git
git push -u origin main
```

### Option 2: Manual Setup

```bash
# 1. Create a new repository on GitHub (without README, .gitignore, or LICENSE)
# Go to: https://github.com/new
# Name: mrki
# Visibility: Private (recommended for personal use)

# 2. Add remote and push
cd /tmp/mrki
git remote add origin https://github.com/YOUR_USERNAME/mrki.git
git branch -M main
git push -u origin main
```

### Option 3: Using SSH

```bash
# Ensure you have SSH keys set up with GitHub
# See: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

cd /tmp/mrki
git remote add origin git@github.com:YOUR_USERNAME/mrki.git
git branch -M main
git push -u origin main
```

## Repository Structure

Your repository will contain:

```
mrki/
├── .github/          # GitHub Actions, issue templates
├── api/              # Unified FastAPI application
├── client/           # Cross-platform React Native/Electron app
├── core/             # Agent orchestration system
├── dev_env/          # Full-stack development environment
├── docs/             # Documentation
├── gamedev/          # Game development modules
├── ide_integration/  # VS Code, Cursor, Zed extensions
├── infrastructure/   # Terraform, Kubernetes configs
├── moe/              # Mixture-of-Experts architecture
├── src/              # Python package source
├── visual_engine/    # Visual-to-code engine
├── main.py           # Application entry point
├── docker-compose.full.yml  # Complete local stack
└── README.md         # Main documentation
```

## After Pushing

1. **Enable GitHub Actions**: Go to repository Settings > Actions > General > Allow all actions
2. **Set up secrets** (if needed): Settings > Secrets and variables > Actions
3. **Configure GitHub Pages** (optional): Settings > Pages > Source > GitHub Actions
4. **Add topics**: Repository page > gear icon > Topics (e.g., ai, agents, code-generation)

## Verification

```bash
# Verify remote is set correctly
git remote -v

# Check repository status
git status

# View commit history
git log --oneline -10
```

## Troubleshooting

**Permission denied**: Check your GitHub token/SSH key has push access
**Repository not found**: Ensure the repository exists and is spelled correctly
**Large files**: If you have files >100MB, use Git LFS: https://git-lfs.github.com/

## Need Help?

- GitHub Docs: https://docs.github.com/en/get-started
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf
