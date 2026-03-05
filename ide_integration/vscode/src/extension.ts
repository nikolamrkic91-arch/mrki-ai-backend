/**
 * Mrki VS Code Extension
 * Main entry point for the extension
 */

import * as vscode from 'vscode';
import { MrkiLanguageClient } from './languageClient';
import { MrkiInlineCompletionProvider } from './inlineCompletion';
import { MrkiChatProvider } from './chatProvider';
import { MrkiStatusBar } from './statusBar';
import { MrkiCodeActionsProvider } from './codeActions';
import { DebugAdapterFactory } from './debugAdapter';
import { Logger } from './utils/logger';

let languageClient: MrkiLanguageClient | undefined;
let statusBar: MrkiStatusBar | undefined;
let logger: Logger;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    logger = new Logger('MrkiExtension');
    logger.info('Activating Mrki extension...');

    // Initialize status bar
    statusBar = new MrkiStatusBar();
    context.subscriptions.push(statusBar);

    // Initialize language client
    languageClient = new MrkiLanguageClient();
    await languageClient.start();
    context.subscriptions.push(languageClient);

    // Register inline completion provider
    const inlineProvider = new MrkiInlineCompletionProvider();
    const inlineDisposable = vscode.languages.registerInlineCompletionItemProvider(
        [
            { scheme: 'file', language: 'python' },
            { scheme: 'file', language: 'javascript' },
            { scheme: 'file', language: 'typescript' },
            { scheme: 'file', language: 'rust' },
            { scheme: 'file', language: 'go' },
            { scheme: 'file', language: 'java' },
            { scheme: 'file', language: 'cpp' },
            { scheme: 'file', language: 'c' },
            { scheme: 'file', language: 'ruby' },
            { scheme: 'file', language: 'php' },
        ],
        inlineProvider
    );
    context.subscriptions.push(inlineDisposable);

    // Register chat provider
    const chatProvider = new MrkiChatProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('mrki.chatView', chatProvider)
    );

    // Register code actions provider
    const codeActionsProvider = new MrkiCodeActionsProvider();
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            [
                { scheme: 'file', language: 'python' },
                { scheme: 'file', language: 'javascript' },
                { scheme: 'file', language: 'typescript' },
            ],
            codeActionsProvider
        )
    );

    // Register debug adapter
    const debugFactory = new DebugAdapterFactory();
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('mrki', debugFactory)
    );

    // Register commands
    registerCommands(context);

    // Set context
    vscode.commands.executeCommand('setContext', 'mrki.enabled', true);

    logger.info('Mrki extension activated successfully');
    statusBar.setStatus('ready');
}

function registerCommands(context: vscode.ExtensionContext): void {
    // Start command
    const startCmd = vscode.commands.registerCommand('mrki.start', async () => {
        if (!languageClient) {
            languageClient = new MrkiLanguageClient();
        }
        await languageClient.start();
        statusBar?.setStatus('ready');
        vscode.window.showInformationMessage('Mrki started successfully');
    });
    context.subscriptions.push(startCmd);

    // Stop command
    const stopCmd = vscode.commands.registerCommand('mrki.stop', async () => {
        if (languageClient) {
            await languageClient.stop();
            languageClient = undefined;
        }
        statusBar?.setStatus('stopped');
        vscode.window.showInformationMessage('Mrki stopped');
    });
    context.subscriptions.push(stopCmd);

    // Restart command
    const restartCmd = vscode.commands.registerCommand('mrki.restart', async () => {
        statusBar?.setStatus('loading');
        if (languageClient) {
            await languageClient.stop();
        }
        languageClient = new MrkiLanguageClient();
        await languageClient.start();
        statusBar?.setStatus('ready');
        vscode.window.showInformationMessage('Mrki restarted');
    });
    context.subscriptions.push(restartCmd);

    // Status command
    const statusCmd = vscode.commands.registerCommand('mrki.status', () => {
        const status = languageClient?.isRunning() ? 'Running' : 'Stopped';
        vscode.window.showInformationMessage(`Mrki Status: ${status}`);
    });
    context.subscriptions.push(statusCmd);

    // Complete command
    const completeCmd = vscode.commands.registerCommand('mrki.complete', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }
        await vscode.commands.executeCommand('editor.action.triggerSuggest');
    });
    context.subscriptions.push(completeCmd);

    // Explain code command
    const explainCmd = vscode.commands.registerCommand('mrki.explainCode', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to explain');
            return;
        }
        const selectedText = editor.document.getText(editor.selection);
        // Send to language server for explanation
        const explanation = await languageClient?.explainCode(selectedText);
        if (explanation) {
            const panel = vscode.window.createWebviewPanel(
                'mrkiExplanation',
                'Code Explanation',
                vscode.ViewColumn.Beside,
                {}
            );
            panel.webview.html = getExplanationHtml(explanation);
        }
    });
    context.subscriptions.push(explainCmd);

    // Generate tests command
    const testCmd = vscode.commands.registerCommand('mrki.generateTests', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to generate tests for');
            return;
        }
        const selectedText = editor.document.getText(editor.selection);
        const tests = await languageClient?.generateTests(selectedText);
        if (tests) {
            const doc = await vscode.workspace.openTextDocument({
                content: tests,
                language: editor.document.languageId
            });
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
        }
    });
    context.subscriptions.push(testCmd);

    // Refactor command
    const refactorCmd = vscode.commands.registerCommand('mrki.refactor', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to refactor');
            return;
        }
        const selectedText = editor.document.getText(editor.selection);
        const refactored = await languageClient?.refactorCode(selectedText);
        if (refactored) {
            editor.edit(editBuilder => {
                editBuilder.replace(editor.selection, refactored);
            });
        }
    });
    context.subscriptions.push(refactorCmd);

    // Open chat command
    const chatCmd = vscode.commands.registerCommand('mrki.openChat', () => {
        vscode.commands.executeCommand('mrki.chatView.focus');
    });
    context.subscriptions.push(chatCmd);
}

function getExplanationHtml(explanation: string): string {
    return `<!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: var(--vscode-font-family); padding: 20px; }
            pre { background: var(--vscode-textBlockQuote-background); padding: 10px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h2>Code Explanation</h2>
        <div>${explanation.replace(/\n/g, '<br>')}</div>
    </body>
    </html>`;
}

export async function deactivate(): Promise<void> {
    logger?.info('Deactivating Mrki extension...');
    if (languageClient) {
        await languageClient.stop();
    }
    logger?.info('Mrki extension deactivated');
}
