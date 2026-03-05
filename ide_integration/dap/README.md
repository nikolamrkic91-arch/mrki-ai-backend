# Mrki Debug Adapter Protocol (DAP) Implementation

Full DAP implementation for debugging with Mrki.

## Features

- **Launch/Attach**: Start and attach to debug sessions
- **Breakpoints**: Line, function, and conditional breakpoints
- **Stepping**: Step in, over, out
- **Stack Traces**: View call stack
- **Variables**: Inspect local and global variables
- **Evaluation**: Evaluate expressions
- **Exception Handling**: Catch raised and uncaught exceptions

## Installation

```bash
pip install mrki[dap]
```

## Usage

### Standalone

```bash
# Start DAP server
mrki-dap --port 8766

# Debug mode
mrki-dap --debug
```

### With VS Code

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "mrki",
      "request": "launch",
      "name": "Debug with Mrki",
      "program": "${workspaceFolder}/main.py",
      "args": [],
      "env": {},
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

## Protocol Methods

### Lifecycle

| Method | Description |
|--------|-------------|
| `initialize` | Initialize debug adapter |
| `launch` | Launch debuggee |
| `attach` | Attach to running process |
| `disconnect` | End debug session |
| `terminate` | Terminate debuggee |

### Control

| Method | Description |
|--------|-------------|
| `continue` | Continue execution |
| `next` | Step over |
| `stepIn` | Step into |
| `stepOut` | Step out |
| `pause` | Pause execution |

### Inspection

| Method | Description |
|--------|-------------|
| `stackTrace` | Get call stack |
| `scopes` | Get variable scopes |
| `variables` | Get variables |
| `evaluate` | Evaluate expression |
| `source` | Get source code |
| `threads` | Get threads |

### Breakpoints

| Method | Description |
|--------|-------------|
| `setBreakpoints` | Set line breakpoints |
| `setFunctionBreakpoints` | Set function breakpoints |
| `setExceptionBreakpoints` | Set exception breakpoints |

## Events

| Event | Description |
|-------|-------------|
| `initialized` | Adapter initialized |
| `stopped` | Execution stopped |
| `continued` | Execution continued |
| `thread` | Thread event |
| `output` | Output message |
| `breakpoint` | Breakpoint event |
| `terminated` | Debuggee terminated |
| `exited` | Debuggee exited |

## Configuration

### Launch Configuration

```json
{
  "type": "mrki",
  "request": "launch",
  "name": "Debug Program",
  "program": "${workspaceFolder}/main.py",
  "args": ["arg1", "arg2"],
  "env": {
    "DEBUG": "1"
  },
  "cwd": "${workspaceFolder}",
  "stopOnEntry": false
}
```

## Development

```bash
# Install dependencies
pip install -e .[dev]

# Run tests
pytest

# Type check
mypy mrki_dap
```

## License

MIT
