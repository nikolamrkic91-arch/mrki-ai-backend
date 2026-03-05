/**
 * Mrki Cursor Integration Extension
 * Bridges Mrki with Cursor's AI features
 */

import * as vscode from 'vscode';
import { CursorComposer } from './composer';
import { CursorContextSync } from './contextSync';
import { InlineCompletionBridge } from './inlineCompletionBridge';
import { Logger } from './utils/logger';

let composer: CursorComposer | undefined;
let contextSync: CursorContextSync | undefined;
let inlineBridge: InlineCompletionBridge | undefined;
let logger: Logger;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    logger = new Logger('CursorIntegration');
    logger.info('Activating Mrki Cursor integration...');

    const config = vscode.workspace.getConfiguration('mrki.cursor');
    
    if (!config.get<boolean>('enabled', true)) {
        logger.info('Cursor integration disabled');
        return;
    }

    // Initialize components
    if (config.get<boolean>('composer.enabled', true)) {
        composer = new CursorComposer();
        context.subscriptions.push(composer);
    }

    if (config.get<boolean>('contextSync', true)) {
        contextSync = new CursorContextSync();
        context.subscriptions.push(contextSync);
    }

    if (config.get<boolean>('inlineCompletions', true)) {
        inlineBridge = new InlineCompletionBridge();
        context.subscriptions.push(inlineBridge);
    }

    // Register commands
    registerCommands(context);

    // Set up file watchers for @-mentions
    setupFileWatchers(context);

    logger.info('Mrki Cursor integration activated');
}

function registerCommands(context: vscode.ExtensionContext): void {
    // Enable command
    const enableCmd = vscode.commands.registerCommand('mrki.cursor.enable', async () => {
        await vscode.workspace.getConfiguration('mrki.cursor').update('enabled', true, true);
        vscode.window.showInformationMessage('Mrki Cursor integration enabled');
    });
    context.subscriptions.push(enableCmd);

    // Disable command
    const disableCmd = vscode.commands.registerCommand('mrki.cursor.disable', async () => {
        await vscode.workspace.getConfiguration('mrki.cursor').update('enabled', false, true);
        vscode.window.showInformationMessage('Mrki Cursor integration disabled');
    });
    context.subscriptions.push(disableCmd);

    // Sync command
    const syncCmd = vscode.commands.registerCommand('mrki.cursor.sync', async () => {
        await contextSync?.syncContext();
        vscode.window.showInformationMessage('Context synced with Cursor AI');
    });
    context.subscriptions.push(syncCmd);

    // Composer command
    const composerCmd = vscode.commands.registerCommand('mrki.cursor.composer', () => {
        composer?.show();
    });
    context.subscriptions.push(composerCmd);

    // Add to context command
    const contextCmd = vscode.commands.registerCommand('mrki.cursor.context', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to add to context');
            return;
        }
        const selectedText = editor.document.getText(editor.selection);
        await contextSync?.addToContext(selectedText);
        vscode.window.showInformationMessage('Added to Cursor context');
    });
    context.subscriptions.push(contextCmd);
}

function setupFileWatchers(context: vscode.ExtensionContext): void {
    // Watch for @-mention files that Cursor creates
    const watcher = vscode.workspace.createFileSystemWatcher('**/.cursor/**');
    
    watcher.onDidCreate((uri) => {
        logger.info(`Cursor file created: ${uri.fsPath}`);
        contextSync?.handleCursorFileChange(uri);
    });
    
    watcher.onDidChange((uri) => {
        logger.info(`Cursor file changed: ${uri.fsPath}`);
        contextSync?.handleCursorFileChange(uri);
    });

    context.subscriptions.push(watcher);
}

export async function deactivate(): Promise<void> {
    logger?.info('Deactivating Mrki Cursor integration...');
    composer?.dispose();
    contextSync?.dispose();
    inlineBridge?.dispose();
}
