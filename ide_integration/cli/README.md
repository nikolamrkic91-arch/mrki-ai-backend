# Mrki CLI

Command-line interface for Mrki AI Development Assistant.

## Installation

```bash
# Install from PyPI
pip install mrki-cli

# Or install from source
cd ide_integration/cli
pip install -e .
```

## Quick Start

```bash
# Check Mrki status
mrki status

# Initialize Mrki in your project
mrki init

# Get code completions
mrki complete file.py

# Start interactive chat
mrki chat

# Explain code
mrki explain file.py

# Generate tests
mrki test file.py -o test_file.py

# Watch files for changes
mrki watch
```

## Commands

### `mrki status`

Show Mrki server and configuration status.

```bash
mrki status
```

### `mrki init`

Initialize Mrki in the current project.

```bash
mrki init
```

Creates `.mrki/config.json` with project settings.

### `mrki complete`

Get AI-powered code completions.

```bash
# Complete a file
mrki complete file.py

# Complete at specific position
mrki complete file.py --line 10 --column 5

# Complete from stdin
echo "def fibonacci(n):" | mrki complete
```

### `mrki chat`

Start interactive chat with Mrki AI.

```bash
mrki chat
```

Features:
- Natural language code questions
- Code explanations
- Refactoring suggestions
- Test generation

### `mrki explain`

Explain code in natural language.

```bash
# Explain a file
mrki explain file.py

# Explain from stdin
cat file.py | mrki explain
```

### `mrki test`

Generate tests for code.

```bash
# Generate tests and print to stdout
mrki test file.py

# Save tests to file
mrki test file.py -o test_file.py
```

### `mrki refactor`

Refactor code with AI assistance.

```bash
mrki refactor file.py "simplify this function"
```

### `mrki watch`

Watch files for changes.

```bash
# Watch current directory
mrki watch

# Watch specific path
mrki watch ./src
```

### `mrki config`

Manage Mrki configuration.

```bash
# Show all config
mrki config

# Get specific value
mrki config server.port

# Set value
mrki config server.port 8765
```

## Configuration

Configuration is stored in `~/.mrki/config.json`:

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

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MRKI_SERVER_HOST` | Server host |
| `MRKI_SERVER_PORT` | Server port |
| `MRKI_LOG_LEVEL` | Log level (debug, info, warn, error) |

## Shell Completion

### Bash

```bash
mrki --install-completion bash
```

### Zsh

```bash
mrki --install-completion zsh
```

### Fish

```bash
mrki --install-completion fish
```

## Troubleshooting

### Server not found

```bash
# Start Mrki server
mrki-server start

# Or check if it's running
curl http://localhost:8765/health
```

### No completions

1. Check server is running: `mrki status`
2. Verify file type is supported
3. Check completion is enabled: `mrki config completion.enabled`

## License

MIT
