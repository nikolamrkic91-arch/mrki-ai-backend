/**
 * Inline Completion Bridge
 * Bridges Mrki completions with Cursor Tab
 */

import * as vscode from 'vscode';
import { Logger } from './utils/logger';

interface CompletionItem {
    text: string;
    confidence: number;
    source: 'mrki' | 'cursor' | 'combined';
}

export class InlineCompletionBridge implements vscode.Disposable {
    private logger: Logger;
    private disposables: vscode.Disposable[] = [];
    private mrkiCompletions: Map<string, CompletionItem[]> = new Map();

    constructor() {
        this.logger = new Logger('InlineCompletionBridge');
        this.registerProviders();
    }

    private registerProviders(): void {
        const config = vscode.workspace.getConfiguration('mrki.cursor');
        const priority = config.get<string>('priority', 'cursor');

        if (priority === 'mrki' || priority === 'combined') {
            // Register Mrki as primary provider
            this.registerMrkiProvider();
        }

        // Listen for Cursor completions
        this.listenForCursorCompletions();
    }

    private registerMrkiProvider(): void {
        const provider: vscode.InlineCompletionItemProvider = {
            provideInlineCompletionItems: async (document, position, context, token) => {
                const config = vscode.workspace.getConfiguration('mrki.cursor');
                if (!config.get<boolean>('inlineCompletions', true)) {
                    return [];
                }

                const cacheKey = this.getCacheKey(document, position);
                const cached = this.mrkiCompletions.get(cacheKey);
                
                if (cached) {
                    return this.convertToInlineItems(cached);
                }

                try {
                    const completions = await this.fetchMrkiCompletions(document, position);
                    this.mrkiCompletions.set(cacheKey, completions);
                    return this.convertToInlineItems(completions);
                } catch (error) {
                    this.logger.error('Failed to fetch Mrki completions:', error);
                    return [];
                }
            }
        };

        const disposable = vscode.languages.registerInlineCompletionItemProvider(
            [
                { scheme: 'file', language: 'python' },
                { scheme: 'file', language: 'javascript' },
                { scheme: 'file', language: 'typescript' },
                { scheme: 'file', language: 'rust' },
                { scheme: 'file', language: 'go' },
            ],
            provider
        );

        this.disposables.push(disposable);
    }

    private listenForCursorCompletions(): void {
        // Monitor for Cursor Tab completions
        // This is done through file watching and command interception
        
        vscode.workspace.onDidChangeTextDocument((e) => {
            // Detect if change was from Cursor Tab
            if (this.isCursorCompletion(e)) {
                this.handleCursorCompletion(e);
            }
        }, null, this.disposables);
    }

    private async fetchMrkiCompletions(
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<CompletionItem[]> {
        const config = vscode.workspace.getConfiguration('mrki.cursor.server');
        const host = config.get<string>('host', 'localhost');
        const port = config.get<number>('port', 8765);

        const contextText = document.getText(new vscode.Range(
            new vscode.Position(Math.max(0, position.line - 20), 0),
            position
        ));

        const response = await fetch(`http://${host}:${port}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: document.getText(),
                position: { line: position.line, character: position.character },
                language: document.languageId,
                context: contextText
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.items.map((item: any) => ({
            text: item.insertText,
            confidence: item.confidence,
            source: 'mrki' as const
        }));
    }

    private convertToInlineItems(items: CompletionItem[]): vscode.InlineCompletionItem[] {
        return items
            .filter(item => item.confidence > 0.5)
            .sort((a, b) => b.confidence - a.confidence)
            .slice(0, 3)
            .map(item => new vscode.InlineCompletionItem(item.text));
    }

    private isCursorCompletion(e: vscode.TextDocumentChangeEvent): boolean {
        // Detect Cursor Tab completions by analyzing the change
        // Cursor typically inserts multi-line completions at once
        const changes = e.contentChanges;
        if (changes.length !== 1) return false;
        
        const change = changes[0];
        // Cursor completions are typically insertions (not replacements)
        if (change.rangeLength > 0) return false;
        
        // Cursor completions often contain newlines
        if (!change.text.includes('\n')) return false;
        
        return true;
    }

    private handleCursorCompletion(e: vscode.TextDocumentChangeEvent): void {
        this.logger.debug('Detected Cursor completion');
        
        const config = vscode.workspace.getConfiguration('mrki.cursor');
        if (config.get<string>('priority') === 'mrki') {
            // If Mrki has higher priority, we might want to override
            // This is complex and would require intercepting the completion
        }
    }

    private getCacheKey(document: vscode.TextDocument, position: vscode.Position): string {
        const lineText = document.lineAt(position.line).text.slice(0, position.character);
        return `${document.languageId}:${position.line}:${lineText.slice(-50)}`;
    }

    dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
}
