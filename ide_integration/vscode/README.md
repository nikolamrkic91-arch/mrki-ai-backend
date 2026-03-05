# Mrki VS Code Extension

Official VS Code extension for Mrki - AI-powered development environment with intelligent code completion, inline suggestions, and AI chat.

## Features

- **AI-Powered Code Completion**: Context-aware completions powered by machine learning
- **Inline Suggestions**: Real-time code suggestions as you type
- **AI Chat Interface**: Interactive chat for code explanations and assistance
- **Code Actions**: Explain, refactor, generate tests, and add documentation
- **Debug Support**: Full Debug Adapter Protocol integration
- **Multi-Language Support**: Python, JavaScript, TypeScript, Rust, Go, and more

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Mrki"
4. Click Install

### From Source

```bash
cd ide_integration/vscode
npm install
npm run compile
# Press F5 to launch extension host
```

## Configuration

Open VS Code settings (Ctrl+,) and search for "Mrki":

| Setting | Default | Description |
|---------|---------|-------------|
| `mrki.enabled` | `true` | Enable Mrki extension |
| `mrki.server.host` | `localhost` | Language server host |
| `mrki.server.port` | `8765` | Language server port |
| `mrki.completion.enabled` | `true` | Enable code completion |
| `mrki.completion.inlineEnabled` | `true` | Enable inline suggestions |
| `mrki.completion.delay` | `100` | Completion trigger delay (ms) |
| `mrki.debug.enabled` | `true` | Enable debug adapter |
| `mrki.chat.model` | `mrki-large` | AI model for chat |

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| `Mrki: Start` | - | Start Mrki language server |
| `Mrki: Stop` | - | Stop Mrki language server |
| `Mrki: Restart` | - | Restart Mrki language server |
| `Mrki: Trigger Completion` | `Ctrl+Space` | Trigger AI completion |
| `Mrki: Open AI Chat` | `Ctrl+Shift+M` | Open chat panel |
| `Mrki: Explain Selected Code` | - | Explain selected code |
| `Mrki: Generate Tests` | - | Generate tests for selection |
| `Mrki: Refactor Code` | - | Refactor selected code |

## Usage

### Code Completion

1. Start typing in any supported file
2. Mrki will show inline suggestions
3. Press `Tab` to accept or keep typing to ignore

### AI Chat

1. Open the Mrki Chat panel from the sidebar
2. Type your question or request
3. Mrki will respond with explanations, code, or suggestions

### Code Actions

1. Select code in the editor
2. Right-click and choose from Mrki actions:
   - Explain with Mrki
   - Generate tests with Mrki
   - Refactor with Mrki
   - Add documentation with Mrki

### Debugging

1. Open the Run and Debug panel (Ctrl+Shift+D)
2. Select "Debug with Mrki" configuration
3. Press F5 to start debugging

## Requirements

- VS Code 1.85.0 or higher
- Mrki language server running (see main project)

## Troubleshooting

### Extension not working

1. Check Mrki status in the status bar
2. Open Output panel (Ctrl+Shift+U) and select "Mrki"
3. Check for error messages

### No completions appearing

1. Ensure `mrki.completion.enabled` is true
2. Check that language server is running
3. Verify file type is supported

## License

MIT
