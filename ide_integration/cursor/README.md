# Mrki Cursor Integration

Enhanced Mrki integration for the Cursor editor.

## Features

- **Composer Integration**: Mrki-powered code editing in Cursor's Composer
- **Context Sync**: Synchronize context between Mrki and Cursor AI
- **Inline Completion Bridge**: Combine Mrki and Cursor Tab completions
- **@-mention Support**: Reference Mrki context in Cursor chat

## Installation

1. Open Cursor
2. Go to Extensions (Cmd+Shift+X)
3. Click "Install from VSIX"
4. Select `mrki-cursor-*.vsix`

Or install from source:

```bash
cd ide_integration/cursor
npm install
npm run compile
# Package and install
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `mrki.cursor.enabled` | `true` | Enable Cursor integration |
| `mrki.cursor.composer.enabled` | `true` | Enable Mrki Composer |
| `mrki.cursor.inlineCompletions` | `true` | Bridge completions |
| `mrki.cursor.contextSync` | `true` | Sync context |
| `mrki.cursor.priority` | `cursor` | Completion priority |

## Usage

### Mrki Composer

1. Press `Cmd+Shift+O` to open Mrki Composer
2. Add files to context with the + button
3. Ask Mrki to make changes
4. Apply changes directly to files

### Context Sync

Context automatically syncs between Mrki and Cursor. You can also manually sync:

1. Select code in editor
2. Right-click → "Add to Cursor Context"
3. Or use command palette: "Mrki Cursor: Sync with Cursor AI"

### Priority Settings

- **cursor**: Prioritize Cursor Tab completions
- **mrki**: Prioritize Mrki completions
- **combined**: Show both with confidence ranking

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| Enable Mrki Integration | - | Enable integration |
| Disable Mrki Integration | - | Disable integration |
| Sync with Cursor AI | - | Manual context sync |
| Open Mrki Composer | `Cmd+Shift+O` | Open composer panel |
| Add to Cursor Context | - | Add selection to context |

## Integration Details

### How It Works

1. **Context Files**: Both Mrki and Cursor read/write to `.cursor/context/` and `.mrki/context/`
2. **Completion Bridge**: Intercepts and merges completion providers
3. **Composer Panel**: Webview-based interface for multi-file editing

### File Structure

```
workspace/
├── .cursor/
│   └── context/
│       └── context.json    # Cursor context
├── .mrki/
│   └── context/
│       └── context.json    # Mrki context
```

## Troubleshooting

### Completions not appearing

1. Check `mrki.cursor.inlineCompletions` is enabled
2. Verify Mrki server is running
3. Check priority settings

### Context not syncing

1. Ensure `mrki.cursor.contextSync` is enabled
2. Check write permissions in workspace
3. Try manual sync command

## License

MIT
