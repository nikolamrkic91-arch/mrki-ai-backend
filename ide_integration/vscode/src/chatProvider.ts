/**
 * Mrki Chat Provider
 * Webview-based chat interface for AI interactions
 */

import * as vscode from 'vscode';
import { Logger } from './utils/logger';

interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
}

export class MrkiChatProvider implements vscode.WebviewViewProvider {
    private view?: vscode.WebviewView;
    private logger: Logger;
    private messages: ChatMessage[] = [];
    private isProcessing: boolean = false;

    constructor(private readonly extensionUri: vscode.Uri) {
        this.logger = new Logger('ChatProvider');
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        token: vscode.CancellationToken
    ): void {
        this.view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri]
        };

        webviewView.webview.html = this.getHtmlContent();

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.type) {
                    case 'sendMessage':
                        await this.handleUserMessage(message.content);
                        break;
                    case 'clearChat':
                        this.clearChat();
                        break;
                    case 'insertCode':
                        await this.insertCode(message.code);
                        break;
                    case 'copyCode':
                        await this.copyCode(message.code);
                        break;
                }
            },
            undefined,
            []
        );

        // Load initial welcome message
        this.addMessage({
            role: 'assistant',
            content: 'Hello! I\'m Mrki, your AI coding assistant. How can I help you today?',
            timestamp: Date.now()
        });
    }

    private async handleUserMessage(content: string): Promise<void> {
        // Add user message
        this.addMessage({
            role: 'user',
            content,
            timestamp: Date.now()
        });

        this.isProcessing = true;
        this.updateStatus();

        try {
            // Get context from active editor
            const context = this.getEditorContext();
            
            // Send to AI backend
            const response = await this.sendToAI(content, context);
            
            // Add AI response
            this.addMessage({
                role: 'assistant',
                content: response,
                timestamp: Date.now()
            });
        } catch (error) {
            this.logger.error('Chat error:', error);
            this.addMessage({
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: Date.now()
            });
        } finally {
            this.isProcessing = false;
            this.updateStatus();
        }
    }

    private async sendToAI(message: string, context?: string): Promise<string> {
        const config = vscode.workspace.getConfiguration('mrki');
        const host = config.get<string>('server.host', 'localhost');
        const port = config.get<number>('server.port', 8765);
        const model = config.get<string>('chat.model', 'mrki-large');

        const response = await fetch(`http://${host}:${port}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                context,
                model,
                history: this.messages.slice(-10) // Last 10 messages for context
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response;
    }

    private getEditorContext(): string | undefined {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return undefined;

        const selection = editor.selection;
        if (selection.isEmpty) {
            // Return surrounding context
            const line = editor.document.lineAt(selection.active.line);
            return line.text;
        }

        return editor.document.getText(selection);
    }

    private addMessage(message: ChatMessage): void {
        this.messages.push(message);
        this.updateWebview();
    }

    private clearChat(): void {
        this.messages = [];
        this.updateWebview();
        this.addMessage({
            role: 'assistant',
            content: 'Chat cleared. How can I help you?',
            timestamp: Date.now()
        });
    }

    private async insertCode(code: string): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        await editor.edit(editBuilder => {
            editBuilder.insert(editor.selection.active, code);
        });
    }

    private async copyCode(code: string): Promise<void> {
        await vscode.env.clipboard.writeText(code);
        vscode.window.showInformationMessage('Code copied to clipboard');
    }

    private updateStatus(): void {
        this.view?.webview.postMessage({
            type: 'status',
            isProcessing: this.isProcessing
        });
    }

    private updateWebview(): void {
        this.view?.webview.postMessage({
            type: 'messages',
            messages: this.messages
        });
    }

    private getHtmlContent(): string {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                
                body {
                    font-family: var(--vscode-font-family);
                    font-size: var(--vscode-font-size);
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                .chat-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                
                .message {
                    max-width: 90%;
                    padding: 12px;
                    border-radius: 8px;
                    word-wrap: break-word;
                }
                
                .message.user {
                    align-self: flex-end;
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                }
                
                .message.assistant {
                    align-self: flex-start;
                    background: var(--vscode-textBlockQuote-background);
                }
                
                .message.system {
                    align-self: center;
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                    font-size: 0.9em;
                }
                
                .message-content {
                    line-height: 1.5;
                }
                
                .message-content pre {
                    background: var(--vscode-textCodeBlock-background);
                    padding: 12px;
                    border-radius: 4px;
                    overflow-x: auto;
                    margin: 8px 0;
                }
                
                .message-content code {
                    font-family: var(--vscode-editor-font-family);
                    font-size: var(--vscode-editor-font-size);
                }
                
                .code-block {
                    position: relative;
                    margin: 8px 0;
                }
                
                .code-actions {
                    position: absolute;
                    top: 4px;
                    right: 4px;
                    display: flex;
                    gap: 4px;
                }
                
                .code-action-btn {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.8em;
                }
                
                .code-action-btn:hover {
                    background: var(--vscode-button-hoverBackground);
                }
                
                .input-container {
                    padding: 12px;
                    border-top: 1px solid var(--vscode-panel-border);
                    display: flex;
                    gap: 8px;
                }
                
                .message-input {
                    flex: 1;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-family: inherit;
                    font-size: inherit;
                    resize: none;
                    min-height: 40px;
                    max-height: 120px;
                }
                
                .message-input:focus {
                    outline: none;
                    border-color: var(--vscode-focusBorder);
                }
                
                .send-btn {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .send-btn:hover:not(:disabled) {
                    background: var(--vscode-button-hoverBackground);
                }
                
                .send-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .status-indicator {
                    padding: 8px 16px;
                    text-align: center;
                    font-size: 0.9em;
                    color: var(--vscode-descriptionForeground);
                }
                
                .status-indicator.processing::after {
                    content: '...';
                    animation: dots 1.5s steps(4, end) infinite;
                }
                
                @keyframes dots {
                    0%, 20% { content: ''; }
                    40% { content: '.'; }
                    60% { content: '..'; }
                    80%, 100% { content: '...'; }
                }
                
                .toolbar {
                    padding: 8px 16px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .toolbar-title {
                    font-weight: bold;
                }
                
                .toolbar-actions {
                    display: flex;
                    gap: 8px;
                }
                
                .toolbar-btn {
                    background: transparent;
                    color: var(--vscode-foreground);
                    border: none;
                    padding: 4px 8px;
                    cursor: pointer;
                    border-radius: 4px;
                }
                
                .toolbar-btn:hover {
                    background: var(--vscode-toolbar-hoverBackground);
                }
            </style>
        </head>
        <body>
            <div class="toolbar">
                <span class="toolbar-title">Mrki Chat</span>
                <div class="toolbar-actions">
                    <button class="toolbar-btn" onclick="clearChat()">Clear</button>
                </div>
            </div>
            
            <div class="chat-container" id="chatContainer"></div>
            
            <div class="status-indicator" id="statusIndicator"></div>
            
            <div class="input-container">
                <textarea 
                    class="message-input" 
                    id="messageInput" 
                    placeholder="Ask me anything..."
                    rows="1"
                ></textarea>
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">
                    Send
                </button>
            </div>
            
            <script>
                const vscode = acquireVsCodeApi();
                const chatContainer = document.getElementById('chatContainer');
                const messageInput = document.getElementById('messageInput');
                const sendBtn = document.getElementById('sendBtn');
                const statusIndicator = document.getElementById('statusIndicator');
                
                let messages = [];
                let isProcessing = false;
                
                // Auto-resize textarea
                messageInput.addEventListener('input', function() {
                    this.style.height = 'auto';
                    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
                });
                
                // Send on Enter (Shift+Enter for new line)
                messageInput.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });
                
                function sendMessage() {
                    const content = messageInput.value.trim();
                    if (!content || isProcessing) return;
                    
                    vscode.postMessage({
                        type: 'sendMessage',
                        content: content
                    });
                    
                    messageInput.value = '';
                    messageInput.style.height = 'auto';
                }
                
                function clearChat() {
                    vscode.postMessage({ type: 'clearChat' });
                }
                
                function insertCode(code) {
                    vscode.postMessage({
                        type: 'insertCode',
                        code: code
                    });
                }
                
                function copyCode(code) {
                    vscode.postMessage({
                        type: 'copyCode',
                        code: code
                    });
                }
                
                function renderMessages() {
                    chatContainer.innerHTML = messages.map(msg => {
                        const time = new Date(msg.timestamp).toLocaleTimeString();
                        let content = msg.content;
                        
                        // Process code blocks
                        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                            return \`
                                <div class="code-block">
                                    <div class="code-actions">
                                        <button class="code-action-btn" onclick='insertCode(\${JSON.stringify(code)})'>Insert</button>
                                        <button class="code-action-btn" onclick='copyCode(\${JSON.stringify(code)})'>Copy</button>
                                    </div>
                                    <pre><code class="language-\${lang || 'text'}">\${escapeHtml(code)}</code></pre>
                                </div>
                            \`;
                        });
                        
                        // Process inline code
                        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
                        
                        return \`
                            <div class="message \${msg.role}">
                                <div class="message-content">\${content}</div>
                            </div>
                        \`;
                    }).join('');
                    
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                
                function escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }
                
                function updateStatus() {
                    if (isProcessing) {
                        statusIndicator.classList.add('processing');
                        statusIndicator.textContent = 'Mrki is thinking';
                        sendBtn.disabled = true;
                    } else {
                        statusIndicator.classList.remove('processing');
                        statusIndicator.textContent = '';
                        sendBtn.disabled = false;
                    }
                }
                
                // Handle messages from extension
                window.addEventListener('message', event => {
                    const message = event.data;
                    
                    switch (message.type) {
                        case 'messages':
                            messages = message.messages;
                            renderMessages();
                            break;
                        case 'status':
                            isProcessing = message.isProcessing;
                            updateStatus();
                            break;
                    }
                });
                
                // Initial render
                renderMessages();
            </script>
        </body>
        </html>`;
    }
}
