/**
 * Mrki Debug Adapter
 * Debug Adapter Protocol implementation for VS Code
 */

import * as vscode from 'vscode';
import {
    DebugAdapterExecutable,
    DebugAdapterDescriptor,
    DebugAdapterDescriptorFactory,
    DebugAdapterInlineImplementation,
    DebugSession,
    ProviderResult
} from 'vscode';
import { Logger } from './utils/logger';

/**
 * Debug Adapter Factory
 * Creates debug adapter instances for Mrki debugging
 */
export class DebugAdapterFactory implements DebugAdapterDescriptorFactory {
    private logger: Logger;

    constructor() {
        this.logger = new Logger('DebugAdapter');
    }

    createDebugAdapterDescriptor(
        session: DebugSession,
        executable: DebugAdapterExecutable | undefined
    ): ProviderResult<DebugAdapterDescriptor> {
        this.logger.info(`Creating debug adapter for session: ${session.id}`);

        const config = vscode.workspace.getConfiguration('mrki.debug');
        const port = config.get<number>('port', 8766);

        // Return executable that starts the debug adapter
        return new DebugAdapterExecutable(
            'python',
            ['-m', 'mrki.dap.server', '--port', port.toString()],
            { cwd: session.workspaceFolder?.uri.fsPath }
        );
    }
}

/**
 * Debug Configuration Provider
 * Provides debug configurations for Mrki
 */
export class DebugConfigurationProvider implements vscode.DebugConfigurationProvider {
    private logger: Logger;

    constructor() {
        this.logger = new Logger('DebugConfig');
    }

    /**
     * Provide initial debug configurations
     */
    provideDebugConfigurations?(
        folder: vscode.WorkspaceFolder | undefined,
        token?: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.DebugConfiguration[]> {
        return [
            {
                type: 'mrki',
                request: 'launch',
                name: 'Debug with Mrki',
                program: '${workspaceFolder}/main.py',
                args: [],
                env: {},
                cwd: '${workspaceFolder}'
            },
            {
                type: 'mrki',
                request: 'launch',
                name: 'Debug Current File',
                program: '${file}',
                args: [],
                env: {},
                cwd: '${workspaceFolder}'
            }
        ];
    }

    /**
     * Resolve debug configuration before launch
     */
    resolveDebugConfiguration?(
        folder: vscode.WorkspaceFolder | undefined,
        debugConfiguration: vscode.DebugConfiguration,
        token?: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.DebugConfiguration> {
        this.logger.info('Resolving debug configuration');

        // Set defaults
        if (!debugConfiguration.program) {
            debugConfiguration.program = '${workspaceFolder}/main.py';
        }
        if (!debugConfiguration.cwd) {
            debugConfiguration.cwd = '${workspaceFolder}';
        }
        if (!debugConfiguration.args) {
            debugConfiguration.args = [];
        }
        if (!debugConfiguration.env) {
            debugConfiguration.env = {};
        }

        return debugConfiguration;
    }
}
