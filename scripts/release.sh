#!/bin/bash
# Mrki release script
# This script prepares and creates a new release

set -e

echo "🚀 Mrki Release Script"
echo "======================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're on main branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo -e "${RED}Error: Must be on main branch to release (currently on $current_branch)${NC}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: There are uncommitted changes${NC}"
    exit 1
fi

# Get current version
current_version=$(python -c "import mrki; print(mrki.__version__)")
echo -e "${BLUE}Current version: $current_version${NC}"

# Ask for new version
echo ""
read -p "Enter new version (e.g., 1.0.1): " new_version

if [ -z "$new_version" ]; then
    echo -e "${RED}Error: Version cannot be empty${NC}"
    exit 1
fi

# Validate version format
if ! [[ $new_version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
    echo -e "${RED}Error: Invalid version format. Use semantic versioning (e.g., 1.0.0)${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Preparing release $new_version...${NC}"
echo ""

# Update version in source
echo -e "${BLUE}Updating version...${NC}"
# Note: In a real scenario, you would update the version file here
# sed -i "s/__version__ = .*/__version__ = \"$new_version\"/" src/mrki/__init__.py

# Update CHANGELOG
echo -e "${BLUE}Updating CHANGELOG...${NC}"
if ! grep -q "## \[$new_version\]" CHANGELOG.md; then
    echo -e "${YELLOW}Warning: Version $new_version not found in CHANGELOG.md${NC}"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests
echo -e "${BLUE}Running tests...${NC}"
if ! make test; then
    echo -e "${RED}Error: Tests failed${NC}"
    exit 1
fi

# Build package
echo -e "${BLUE}Building package...${NC}"
python -m build

# Check distribution
echo -e "${BLUE}Checking distribution...${NC}"
twine check dist/*

# Commit changes
echo -e "${BLUE}Committing changes...${NC}"
git add -A
git commit -m "Release version $new_version"

# Create tag
echo -e "${BLUE}Creating git tag...${NC}"
git tag -a "v$new_version" -m "Release version $new_version"

echo ""
echo -e "${GREEN}✅ Release $new_version prepared!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git log --oneline -5"
echo "  2. Push to trigger release: git push origin main --tags"
echo "  3. GitHub Actions will build and publish the release"
echo ""
echo "Or to cancel:"
echo "  git reset --hard HEAD~1"
echo "  git tag -d v$new_version"
