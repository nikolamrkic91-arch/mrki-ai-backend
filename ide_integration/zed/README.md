# Mrki Extension for Zed

Official Mrki extension for the Zed editor.

## Features

- **Language Server Protocol**: Full LSP support for Python, JavaScript, TypeScript, Rust, and Go
- **Slash Commands**: Quick AI actions via `/mrki`, `/mrki-explain`, `/mrki-test`, `/mrki-refactor`
- **Inline Completions**: AI-powered code suggestions
- **Context Awareness**: Mrki understands your codebase

## Installation

### From Zed Extensions

1. Open Zed
2. Press `Cmd+Shift+P` → "extensions: install"
3. Search for "Mrki"
4. Click Install

### From Source

```bash
cd ide_integration/zed
cargo build --release
# Copy to Zed extensions directory
```

## Setup

1. Install Mrki language server:
   ```bash
   pip install mrki[lsp]
   ```

2. Ensure `mrki-lsp` is in your PATH

3. Restart Zed

## Slash Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/mrki` | Ask Mrki anything | `/mrki explain this function` |
| `/mrki-explain` | Explain selected code | `/mrki-explain` |
| `/mrki-test` | Generate tests | `/mrki-test` |
| `/mrki-refactor` | Refactor code | `/mrki-refactor simplify` |

## Configuration

Add to your Zed settings (`~/.config/zed/settings.json`):

```json
{
  "mrki": {
    "enabled": true,
    "server": {
      "host": "localhost",
      "port": 8765
    },
    "completion": {
      "enabled": true,
      "inline_enabled": true
    }
  }
}
```

## Supported Languages

- Python
- JavaScript
- TypeScript
- Rust
- Go
- Java
- C/C++
- Ruby
- PHP

## Usage

### Code Completion

1. Start typing in any supported file
2. Mrki will show suggestions automatically
3. Press `Tab` to accept

### Slash Commands

1. Open the assistant panel (`Cmd+?`)
2. Type `/mrki` followed by your question
3. Press Enter to send

### Explain Code

1. Select code in the editor
2. Type `/mrki-explain` in assistant
3. Mrki will explain the selection

### Generate Tests

1. Select a function or class
2. Type `/mrki-test` in assistant
3. Mrki will generate tests

## Troubleshooting

### Language server not found

```bash
# Check if mrki-lsp is installed
which mrki-lsp

# If not found, install it
pip install mrki[lsp]
```

### Completions not appearing

1. Check Mrki is enabled in settings
2. Verify language server is running
3. Check Zed logs: `~/.config/zed/logs/`

## Development

```bash
# Build extension
cargo build

# Run tests
cargo test

# Package for distribution
cargo build --release
```

## License

MIT
