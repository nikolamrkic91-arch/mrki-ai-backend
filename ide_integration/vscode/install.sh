#!/bin/bash

# Mrki VS Code Extension Installation Script

set -e

echo "Installing Mrki VS Code Extension..."

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "Error: VS Code is not installed or not in PATH"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install dependencies
echo "Installing dependencies..."
npm install

# Compile TypeScript
echo "Compiling TypeScript..."
npm run compile

# Package extension
echo "Packaging extension..."
npm run package

# Install extension
echo "Installing extension to VS Code..."
code --install-extension mrki-vscode-*.vsix

echo "Installation complete!"
echo "Please reload VS Code to activate the extension."
