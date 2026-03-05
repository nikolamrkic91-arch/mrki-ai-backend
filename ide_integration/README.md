# Mrki IDE Integration

Complete IDE integration suite for Mrki AI Development Assistant.

## Overview

This directory contains all IDE integrations and terminal interfaces for Mrki:

- **VS Code Extension** (`vscode/`) - Full-featured VS Code extension
- **Cursor Integration** (`cursor/`) - Cursor editor integration
- **Zed Extension** (`zed/`) - Zed editor extension
- **CLI Tool** (`cli/`) - Command-line interface
- **LSP Server** (`lsp/`) - Language Server Protocol implementation
- **DAP Server** (`dap/`) - Debug Adapter Protocol implementation
- **Terminal UI** (`terminal_ui.py`) - Rich terminal interface components
- **File Watcher** (`file_watcher.py`) - File system monitoring

## Quick Install

```bash
# Install everything
./install.sh

# Install specific components
./install.sh --cli-only
./install.sh --vscode-only
./install.sh --cursor-only
./install.sh --zed-only
```

## Components

### CLI Tool

Command-line interface for Mrki:

```bash
mrki status          # Check status
mrki init            # Initialize project
mrki complete file   # Get completions
mrki chat            # Interactive chat
mrki explain file    # Explain code
mrki test file       # Generate tests
mrki watch           # Watch files
```

### VS Code Extension

Features:
- AI-powered code completion
- Inline suggestions
- Interactive chat panel
- Code actions (explain, test, refactor)
- Debug support

Install:
```bash
cd vscode
npm install
npm run compile
code --install-extension .
```

### Cursor Integration

Features:
- Composer integration
- Context sync with Cursor AI
- Inline completion bridge
- @-mention support

### Zed Extension

Features:
- LSP support
- Slash commands (`/mrki`, `/mrki-explain`, `/mrki-test`)
- Inline completions
- Code actions

### LSP Server

Language Server Protocol implementation:

```bash
mrki-lsp --stdio    # Standard I/O mode
mrki-lsp --port 8765 # TCP mode
```

### DAP Server

Debug Adapter Protocol implementation:

```bash
mrki-dap --port 8766
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Editors                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │VS Code  │  │ Cursor  │  │  Zed    │  │  Terminal (CLI) │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
└───────┼────────────┼────────────┼────────────────┼──────────┘
        │            │            │                │
        │            │            │                │
┌───────┴────────────┴────────────┴────────────────┴──────────┐
│                    Protocol Layer                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Language Server Protocol (LSP)              │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │             Debug Adapter Protocol (DAP)               │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Mrki Backend                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  AI Engine  │  │ File Watch  │  │  Context Manager   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Global Config (`~/.mrki/config.json`)

```json
{
  "server": {
    "host": "localhost",
    "port": 8765
  },
  "completion": {
    "enabled": true,
    "inline": true
  },
  "ui": {
    "theme": "dark",
    "animations": true
  }
}
```

### Project Config (`.mrki/config.json`)

```json
{
  "name": "my-project",
  "language": "python",
  "include": ["**/*.py"],
  "exclude": ["**/tests/**", "**/__pycache__/**"]
}
```

## Development

### Setup

```bash
# Install all dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e cli/
pip install -e lsp/
pip install -e dap/
```

### Testing

```bash
# Run all tests
pytest

# Test specific component
pytest lsp/
pytest dap/
```

### Building

```bash
# Build VS Code extension
cd vscode
npm run package

# Build Zed extension
cd zed
cargo build --release
```

## Troubleshooting

### Server not found

```bash
# Check if servers are in PATH
which mrki-lsp
which mrki-dap

# Start servers manually
mrki-lsp --stdio
mrki-dap --port 8766
```

### VS Code extension not working

1. Check Output panel → "Mrki Language Server"
2. Verify mrki-lsp is installed: `which mrki-lsp`
3. Restart VS Code

### No completions

1. Check server status: `mrki status`
2. Verify file type is supported
3. Check completion is enabled in config

## License

MIT
