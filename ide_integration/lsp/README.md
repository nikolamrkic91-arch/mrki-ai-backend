# Mrki Language Server Protocol (LSP) Implementation

Full LSP implementation for Mrki AI-powered development.

## Features

- **Text Document Synchronization**: Full, incremental changes
- **Code Completion**: AI-powered context-aware completions
- **Hover Information**: Symbol documentation
- **Go to Definition**: Navigate to symbol definitions
- **Find References**: Find all symbol references
- **Document Symbols**: Outline view support
- **Code Actions**: Quick fixes and refactorings
- **Formatting**: Document and range formatting
- **Rename**: Symbol renaming
- **Semantic Tokens**: Syntax highlighting
- **Inlay Hints**: Type hints and parameter names

## Installation

```bash
pip install mrki[lsp]
```

## Usage

### Standalone

```bash
# Start LSP server on stdio
mrki-lsp --stdio

# Start with TCP
mrki-lsp --port 8765

# Debug mode
mrki-lsp --stdio --debug
```

### With VS Code

The VS Code extension automatically starts the LSP server.

### With Zed

Configure in Zed settings:

```json
{
  "lsp": {
    "mrki": {
      "binary": {
        "path": "mrki-lsp",
        "arguments": ["--stdio"]
      }
    }
  }
}
```

## Protocol Methods

### Standard LSP Methods

| Method | Description |
|--------|-------------|
| `initialize` | Initialize connection |
| `textDocument/didOpen` | Document opened |
| `textDocument/didClose` | Document closed |
| `textDocument/didChange` | Document changed |
| `textDocument/completion` | Code completion |
| `textDocument/hover` | Hover information |
| `textDocument/definition` | Go to definition |
| `textDocument/references` | Find references |
| `textDocument/documentSymbol` | Document symbols |
| `textDocument/codeAction` | Code actions |
| `textDocument/formatting` | Format document |
| `textDocument/rename` | Rename symbol |

### Mrki-Specific Methods

| Method | Description |
|--------|-------------|
| `mrki/explain` | Explain code |
| `mrki/generateTests` | Generate tests |
| `mrki/refactor` | Refactor code |

## Configuration

### Initialization Options

```json
{
  "completion": {
    "enabled": true,
    "inlineEnabled": true
  },
  "hover": {
    "enabled": true
  },
  "codeActions": {
    "enabled": true
  }
}
```

## Development

```bash
# Install dependencies
pip install -e .[dev]

# Run tests
pytest

# Type check
mypy mrki_lsp

# Lint
ruff check mrki_lsp
```

## Architecture

```
┌─────────────┐     LSP     ┌──────────────┐     HTTP     ┌─────────────┐
│   Editor    │◄───────────►│  LSP Server  │◄────────────►│  AI Backend  │
│  (VS Code)  │             │  (mrki-lsp)  │              │   (Mrki)    │
└─────────────┘             └──────────────┘              └─────────────┘
```

## License

MIT
