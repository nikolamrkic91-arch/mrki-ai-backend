/**
 * Cursor Composer Integration
 * Integrates Mrki with Cursor's Composer feature
 */

import * as vscode from 'vscode';
import { Logger } from './utils/logger';

interface ComposerMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    files?: string[];
}

export class CursorComposer implements vscode.Disposable {
    private panel: vscode.WebviewPanel | undefined;
    private logger: Logger;
    private messages: ComposerMessage[] = [];

    constructor() {
        this.logger = new Logger('CursorComposer');
    }

    show(): void {
        if (this.panel) {
            this.panel.reveal();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'mrkiComposer',
            'Mrki Composer',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: []
            }
        );

        this.panel.webview.html = this.getHtmlContent();

        this.panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.type) {
                    case 'sendMessage':
                        await this.handleMessage(message.content, message.files);
                        break;
                    case 'applyEdit':
                        await this.applyEdit(message.file, message.content);
                        break;
                    case 'addFile':
                        await this.addFileToContext(message.filePath);
                        break;
                }
            },
            undefined,
            []
        );

        this.panel.onDidDispose(() => {
            this.panel = undefined;
        });
    }

    private async handleMessage(content: string, files?: string[]): Promise<void> {
        // Add user message
        this.messages.push({
            role: 'user',
            content,
            files
        });

        this.updateWebview();

        try {
            // Get context from open files
            const context = await this.gatherContext(files);
            
            // Send to Mrki backend
            const response = await this.sendToMrki(content, context);
            
            // Add assistant response
            this.messages.push({
                role: 'assistant',
                content: response
            });

            this.updateWebview();
        } catch (error) {
            this.logger.error('Error in composer:', error);
            this.messages.push({
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            });
            this.updateWebview();
        }
    }

    private async gatherContext(filePaths?: string[]): Promise<string> {
        const contexts: string[] = [];

        if (filePaths) {
            for (const filePath of filePaths) {
                try {
                    const uri = vscode.Uri.file(filePath);
                    const document = await vscode.workspace.openTextDocument(uri);
                    contexts.push(`File: ${filePath}\n${document.getText()}`);
                } catch (error) {
                    this.logger.warn(`Could not read file: ${filePath}`);
                }
            }
        }

        // Add active editor context
        const activeEditor = vscode.window.activeTextEditor;
        if (activeEditor) {
            const selection = activeEditor.selection;
            if (!selection.isEmpty) {
                contexts.push(`Selected code:\n${activeEditor.document.getText(selection)}`);
            }
        }

        return contexts.join('\n\n---\n\n');
    }

    private async sendToMrki(message: string, context: string): Promise<string> {
        const config = vscode.workspace.getConfiguration('mrki.cursor.server');
        const host = config.get<string>('host', 'localhost');
        const port = config.get<number>('port', 8765);

        const response = await fetch(`http://${host}:${port}/composer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                context,
                history: this.messages
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response;
    }

    private async applyEdit(filePath: string, content: string): Promise<void> {
        try {
            const uri = vscode.Uri.file(filePath);
            const document = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(document);

            const fullRange = new vscode.Range(
                document.positionAt(0),
                document.positionAt(document.getText().length)
            );

            await editor.edit(editBuilder => {
                editBuilder.replace(fullRange, content);
            });

            vscode.window.showInformationMessage(`Applied changes to ${filePath}`);
        } catch (error) {
            this.logger.error('Error applying edit:', error);
            vscode.window.showErrorMessage('Failed to apply changes');
        }
    }

    private async addFileToContext(filePath: string): Promise<void> {
        this.panel?.webview.postMessage({
            type: 'fileAdded',
            filePath
        });
    }

    private updateWebview(): void {
        this.panel?.webview.postMessage({
            type: 'messages',
            messages: this.messages
        });
    }

    private getHtmlContent(): string {
        return `<!DOCTYPE html>
        <html>
        <head>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                .header {
                    padding: 12px 16px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .header-title { font-weight: bold; }
                .context-files {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                    padding: 8px 16px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .context-file {
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.85em;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                .context-file button {
                    background: none;
                    border: none;
                    color: inherit;
                    cursor: pointer;
                }
                .messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                }
                .message {
                    margin-bottom: 16px;
                    padding: 12px;
                    border-radius: 8px;
                }
                .message.user {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                }
                .message.assistant {
                    background: var(--vscode-textBlockQuote-background);
                }
                .input-area {
                    padding: 12px;
                    border-top: 1px solid var(--vscode-panel-border);
                }
                .input-row {
                    display: flex;
                    gap: 8px;
                }
                textarea {
                    flex: 1;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    padding: 8px;
                    resize: none;
                    min-height: 60px;
                }
                button {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover { background: var(--vscode-button-hoverBackground); }
                .file-attachment { margin-top: 8px; }
                code {
                    background: var(--vscode-textCodeBlock-background);
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                pre {
                    background: var(--vscode-textCodeBlock-background);
                    padding: 12px;
                    border-radius: 4px;
                    overflow-x: auto;
                    margin: 8px 0;
                }
                .apply-btn {
                    margin-top: 8px;
                    font-size: 0.85em;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <span class="header-title">Mrki Composer</span>
                <button onclick="addCurrentFile()">+ Add Current File</button>
            </div>
            <div class="context-files" id="contextFiles"></div>
            <div class="messages" id="messages"></div>
            <div class="input-area">
                <div class="input-row">
                    <textarea id="input" placeholder="Ask Mrki to edit your code..."></textarea>
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            <script>
                const vscode = acquireVsCodeApi();
                let contextFiles = [];
                let messages = [];

                document.getElementById('input').addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

                function sendMessage() {
                    const input = document.getElementById('input');
                    const content = input.value.trim();
                    if (!content) return;
                    vscode.postMessage({
                        type: 'sendMessage',
                        content,
                        files: contextFiles
                    });
                    input.value = '';
                }

                function addCurrentFile() {
                    vscode.postMessage({ type: 'addFile', filePath: 'current' });
                }

                function applyEdit(file, content) {
                    vscode.postMessage({ type: 'applyEdit', file, content });
                }

                function removeFile(filePath) {
                    contextFiles = contextFiles.filter(f => f !== filePath);
                    updateContextFiles();
                }

                function updateContextFiles() {
                    document.getElementById('contextFiles').innerHTML = contextFiles.map(f =>
                        '<div class="context-file">' + f + '<button onclick="removeFile(\'' + f + '\')">×</button></div>'
                    ).join('');
                }

                function updateMessages() {
                    document.getElementById('messages').innerHTML = messages.map(m => {
                        let content = m.content
                            .replace(/</g, '&lt;').replace(/>/g, '&gt;')
                            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
                            .replace(/`([^`]+)`/g, '<code>$1</code>');
                        return '<div class="message ' + m.role + '">' + content + '</div>';
                    }).join('');
                }

                window.addEventListener('message', (e) => {
                    const msg = e.data;
                    if (msg.type === 'messages') {
                        messages = msg.messages;
                        updateMessages();
                    } else if (msg.type === 'fileAdded') {
                        if (!contextFiles.includes(msg.filePath)) {
                            contextFiles.push(msg.filePath);
                            updateContextFiles();
                        }
                    }
                });
            </script>
        </body>
        </html>`;
    }

    dispose(): void {
        this.panel?.dispose();
    }
}
