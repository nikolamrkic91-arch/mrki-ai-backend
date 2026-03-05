#!/bin/bash
# Mrki setup script
# This script sets up the development environment for Mrki

set -e

echo "🚀 Setting up Mrki development environment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.9 or higher is required (found $python_version)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version OK ($python_version)${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
else
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
pre-commit install

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p data logs plugins backups

# Create local config if it doesn't exist
if [ ! -f "config.local.yaml" ]; then
    echo -e "${BLUE}Creating local config...${NC}"
    cp config.example.yaml config.local.yaml
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Start the server: mrki server start"
echo "  3. Run tests: make test"
echo "  4. View docs: make serve-docs"
echo ""
echo "For more information, see CONTRIBUTING.md"
