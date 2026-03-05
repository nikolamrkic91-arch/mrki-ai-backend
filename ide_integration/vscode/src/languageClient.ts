/**
 * Mrki Language Client
 * LSP client implementation for VS Code
 */

import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind,
    Executable
} from 'vscode-languageclient/node';
import { Logger } from './utils/logger';

export class MrkiLanguageClient implements vscode.Disposable {
    private client: LanguageClient | undefined;
    private logger: Logger;
    private isStarted: boolean = false;

    constructor() {
        this.logger = new Logger('LanguageClient');
    }

    async start(): Promise<void> {
        if (this.isStarted) {
            this.logger.warn('Language client already started');
            return;
        }

        const config = vscode.workspace.getConfiguration('mrki.server');
        const host = config.get<string>('host', 'localhost');
        const port = config.get<number>('port', 8765);

        // Server options - connect to external LSP server
        const serverOptions: ServerOptions = {
            run: {
                command: 'python',
                args: ['-m', 'mrki.lsp.server', '--port', port.toString()],
                transport: TransportKind.stdio
            },
            debug: {
                command: 'python',
                args: ['-m', 'mrki.lsp.server', '--port', port.toString(), '--debug'],
                transport: TransportKind.stdio
            }
        };

        // Client options
        const clientOptions: LanguageClientOptions = {
            documentSelector: [
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
            synchronize: {
                fileEvents: vscode.workspace.createFileSystemWatcher('**/*')
            },
            outputChannel: vscode.window.createOutputChannel('Mrki Language Server'),
            revealOutputChannelOn: 4, // Never
            initializationOptions: {
                host,
                port,
                capabilities: {
                    completionProvider: true,
                    hoverProvider: true,
                    definitionProvider: true,
                    referencesProvider: true,
                    documentSymbolProvider: true,
                    codeActionProvider: true,
                    codeLensProvider: true,
                    documentFormattingProvider: true,
                    documentRangeFormattingProvider: true,
                    documentOnTypeFormattingProvider: true,
                    renameProvider: true,
                    foldingRangeProvider: true,
                    executeCommandProvider: true,
                    selectionRangeProvider: true,
                    semanticTokensProvider: true,
                    inlayHintProvider: true,
                    inlineValueProvider: true,
                }
            }
        };

        this.client = new LanguageClient(
            'mrki',
            'Mrki Language Server',
            serverOptions,
            clientOptions
        );

        try {
            await this.client.start();
            this.isStarted = true;
            this.logger.info('Language client started successfully');
        } catch (error) {
            this.logger.error('Failed to start language client:', error);
            throw error;
        }
    }

    async stop(): Promise<void> {
        if (!this.isStarted || !this.client) {
            return;
        }

        try {
            await this.client.stop();
            this.isStarted = false;
            this.logger.info('Language client stopped');
        } catch (error) {
            this.logger.error('Error stopping language client:', error);
        }
    }

    isRunning(): boolean {
        return this.isStarted && this.client !== undefined;
    }

    async explainCode(code: string): Promise<string | undefined> {
        if (!this.client) return undefined;
        
        try {
            const result = await this.client.sendRequest('mrki/explain', { code });
            return result as string;
        } catch (error) {
            this.logger.error('Failed to explain code:', error);
            return undefined;
        }
    }

    async generateTests(code: string): Promise<string | undefined> {
        if (!this.client) return undefined;
        
        try {
            const result = await this.client.sendRequest('mrki/generateTests', { code });
            return result as string;
        } catch (error) {
            this.logger.error('Failed to generate tests:', error);
            return undefined;
        }
    }

    async refactorCode(code: string): Promise<string | undefined> {
        if (!this.client) return undefined;
        
        try {
            const result = await this.client.sendRequest('mrki/refactor', { code });
            return result as string;
        } catch (error) {
            this.logger.error('Failed to refactor code:', error);
            return undefined;
        }
    }

    dispose(): void {
        this.stop();
    }
}
