/**
 * Mrki Inline Completion Provider
 * Provides AI-powered inline code suggestions
 */

import * as vscode from 'vscode';
import { Logger } from './utils/logger';

interface CompletionRequest {
    text: string;
    position: { line: number; character: number };
    language: string;
    filePath: string;
    context?: string;
}

interface CompletionResponse {
    items: Array<{
        insertText: string;
        range?: { start: { line: number; character: number }; end: { line: number; character: number } };
        confidence: number;
    }>;
}

export class MrkiInlineCompletionProvider implements vscode.InlineCompletionItemProvider {
    private logger: Logger;
    private debounceTimer: NodeJS.Timeout | undefined;
    private cache: Map<string, CompletionResponse> = new Map();

    constructor() {
        this.logger = new Logger('InlineCompletion');
    }

    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionItem[] | vscode.InlineCompletionList> {
        const config = vscode.workspace.getConfiguration('mrki.completion');
        
        if (!config.get<boolean>('enabled', true)) {
            return [];
        }

        if (!config.get<boolean>('inlineEnabled', true)) {
            return [];
        }

        // Debounce completion requests
        const delay = config.get<number>('delay', 100);
        
        return new Promise((resolve) => {
            if (this.debounceTimer) {
                clearTimeout(this.debounceTimer);
            }

            this.debounceTimer = setTimeout(async () => {
                try {
                    const items = await this.fetchCompletions(document, position, token);
                    resolve(items);
                } catch (error) {
                    this.logger.error('Error fetching completions:', error);
                    resolve([]);
                }
            }, delay);

            // Handle cancellation
            token.onCancellationRequested(() => {
                if (this.debounceTimer) {
                    clearTimeout(this.debounceTimer);
                }
                resolve([]);
            });
        });
    }

    private async fetchCompletions(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionItem[]> {
        // Get context around cursor
        const contextRange = new vscode.Range(
            Math.max(0, position.line - 50),
            0,
            position.line,
            position.character
        );
        const contextText = document.getText(contextRange);

        // Create cache key
        const cacheKey = `${document.languageId}:${position.line}:${position.character}:${contextText.slice(-100)}`;
        
        // Check cache
        const cached = this.cache.get(cacheKey);
        if (cached) {
            return this.convertToInlineItems(cached, position);
        }

        // Build request
        const request: CompletionRequest = {
            text: document.getText(),
            position: { line: position.line, character: position.character },
            language: document.languageId,
            filePath: document.uri.fsPath,
            context: contextText
        };

        try {
            // Call LSP server for completion
            const response = await this.callCompletionServer(request);
            
            if (token.isCancellationRequested) {
                return [];
            }

            // Cache result
            this.cache.set(cacheKey, response);
            
            // Limit cache size
            if (this.cache.size > 100) {
                const firstKey = this.cache.keys().next().value;
                this.cache.delete(firstKey);
            }

            return this.convertToInlineItems(response, position);
        } catch (error) {
            this.logger.error('Completion request failed:', error);
            return [];
        }
    }

    private async callCompletionServer(request: CompletionRequest): Promise<CompletionResponse> {
        const config = vscode.workspace.getConfiguration('mrki.server');
        const host = config.get<string>('host', 'localhost');
        const port = config.get<number>('port', 8765);

        const response = await fetch(`http://${host}:${port}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json() as CompletionResponse;
    }

    private convertToInlineItems(
        response: CompletionResponse,
        position: vscode.Position
    ): vscode.InlineCompletionItem[] {
        return response.items
            .filter(item => item.confidence > 0.5) // Filter low confidence
            .sort((a, b) => b.confidence - a.confidence)
            .slice(0, 3) // Limit to top 3
            .map(item => {
                const range = item.range
                    ? new vscode.Range(
                        item.range.start.line,
                        item.range.start.character,
                        item.range.end.line,
                        item.range.end.character
                    )
                    : new vscode.Range(position, position);

                return new vscode.InlineCompletionItem(
                    item.insertText,
                    range
                );
            });
    }

    /**
     * Handle acceptance of inline completion
     */
    handleDidAcceptCompletion(item: vscode.InlineCompletionItem): void {
        this.logger.info('Inline completion accepted');
        // Telemetry or analytics could be added here
    }

    /**
     * Handle partial acceptance of inline completion
     */
    handleDidPartiallyAcceptCompletion(
        item: vscode.InlineCompletionItem,
        acceptedLength: number
    ): void {
        this.logger.info(`Inline completion partially accepted (${acceptedLength} chars)`);
    }
}
