/**
 * Cursor Context Sync
 * Synchronizes context between Mrki and Cursor AI
 */

import * as vscode from 'vscode';
import { Logger } from './utils/logger';

interface ContextItem {
    type: 'file' | 'selection' | 'symbol';
    content: string;
    path?: string;
    timestamp: number;
}

export class CursorContextSync implements vscode.Disposable {
    private logger: Logger;
    private contextItems: ContextItem[] = [];
    private cursorContextPath: string;
    private mrkiContextPath: string;

    constructor() {
        this.logger = new Logger('ContextSync');
        
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        this.cursorContextPath = `${workspaceRoot}/.cursor/context`;
        this.mrkiContextPath = `${workspaceRoot}/.mrki/context`;
        
        this.initializeContextFiles();
    }

    private async initializeContextFiles(): Promise<void> {
        try {
            // Ensure context directories exist
            const cursorUri = vscode.Uri.file(this.cursorContextPath);
            const mrkiUri = vscode.Uri.file(this.mrkiContextPath);
            
            await vscode.workspace.fs.createDirectory(cursorUri);
            await vscode.workspace.fs.createDirectory(mrkiUri);
            
            this.logger.info('Context directories initialized');
        } catch (error) {
            this.logger.error('Failed to initialize context directories:', error);
        }
    }

    async syncContext(): Promise<void> {
        this.logger.info('Syncing context between Mrki and Cursor...');
        
        try {
            // Read Cursor context
            const cursorContext = await this.readCursorContext();
            
            // Read Mrki context
            const mrkiContext = await this.readMrkiContext();
            
            // Merge contexts
            const mergedContext = this.mergeContexts(cursorContext, mrkiContext);
            
            // Write to both
            await this.writeCursorContext(mergedContext);
            await this.writeMrkiContext(mergedContext);
            
            this.logger.info('Context sync complete');
        } catch (error) {
            this.logger.error('Context sync failed:', error);
            throw error;
        }
    }

    async addToContext(content: string, type: 'file' | 'selection' | 'symbol' = 'selection'): Promise<void> {
        const item: ContextItem = {
            type,
            content,
            timestamp: Date.now()
        };

        this.contextItems.push(item);
        
        // Trim old items
        if (this.contextItems.length > 50) {
            this.contextItems = this.contextItems.slice(-50);
        }

        await this.writeMrkiContext(this.contextItems);
        
        // Also sync to Cursor if enabled
        const config = vscode.workspace.getConfiguration('mrki.cursor');
        if (config.get<boolean>('contextSync', true)) {
            await this.writeCursorContext(this.contextItems);
        }

        this.logger.info(`Added ${type} to context`);
    }

    async handleCursorFileChange(uri: vscode.Uri): Promise<void> {
        this.logger.info(`Handling Cursor file change: ${uri.fsPath}`);
        
        try {
            const content = await vscode.workspace.fs.readFile(uri);
            const text = Buffer.from(content).toString('utf-8');
            
            // Parse Cursor context file
            const cursorContext = this.parseCursorContext(text);
            
            // Sync to Mrki
            await this.writeMrkiContext(cursorContext);
            
            this.logger.info('Cursor context synced to Mrki');
        } catch (error) {
            this.logger.error('Failed to handle Cursor file change:', error);
        }
    }

    private async readCursorContext(): Promise<ContextItem[]> {
        try {
            const uri = vscode.Uri.file(`${this.cursorContextPath}/context.json`);
            const content = await vscode.workspace.fs.readFile(uri);
            return JSON.parse(Buffer.from(content).toString('utf-8'));
        } catch {
            return [];
        }
    }

    private async readMrkiContext(): Promise<ContextItem[]> {
        try {
            const uri = vscode.Uri.file(`${this.mrkiContextPath}/context.json`);
            const content = await vscode.workspace.fs.readFile(uri);
            return JSON.parse(Buffer.from(content).toString('utf-8'));
        } catch {
            return [];
        }
    }

    private async writeCursorContext(context: ContextItem[]): Promise<void> {
        const uri = vscode.Uri.file(`${this.cursorContextPath}/context.json`);
        const content = Buffer.from(JSON.stringify(context, null, 2));
        await vscode.workspace.fs.writeFile(uri, content);
    }

    private async writeMrkiContext(context: ContextItem[]): Promise<void> {
        const uri = vscode.Uri.file(`${this.mrkiContextPath}/context.json`);
        const content = Buffer.from(JSON.stringify(context, null, 2));
        await vscode.workspace.fs.writeFile(uri, content);
    }

    private mergeContexts(cursor: ContextItem[], mrki: ContextItem[]): ContextItem[] {
        const merged = new Map<string, ContextItem>();
        
        // Add all items with deduplication
        [...cursor, ...mrki, ...this.contextItems].forEach(item => {
            const key = `${item.type}:${item.content.slice(0, 100)}`;
            if (!merged.has(key) || item.timestamp > (merged.get(key)?.timestamp || 0)) {
                merged.set(key, item);
            }
        });
        
        return Array.from(merged.values())
            .sort((a, b) => b.timestamp - a.timestamp)
            .slice(0, 50);
    }

    private parseCursorContext(text: string): ContextItem[] {
        try {
            // Cursor stores context in a specific format
            const parsed = JSON.parse(text);
            if (Array.isArray(parsed)) {
                return parsed;
            }
            // Handle Cursor's format
            if (parsed.context) {
                return parsed.context.map((c: any) => ({
                    type: c.type || 'file',
                    content: c.content || c.text || '',
                    path: c.path,
                    timestamp: c.timestamp || Date.now()
                }));
            }
            return [];
        } catch {
            // Try to extract context from text format
            return [{
                type: 'file',
                content: text,
                timestamp: Date.now()
            }];
        }
    }

    dispose(): void {
        // Cleanup if needed
    }
}
