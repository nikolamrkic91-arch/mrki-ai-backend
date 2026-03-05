/**
 * Mrki Status Bar
 * Shows connection status and quick actions
 */

import * as vscode from 'vscode';

export type MrkiStatus = 'loading' | 'ready' | 'error' | 'stopped';

export class MrkiStatusBar implements vscode.Disposable {
    private statusBarItem: vscode.StatusBarItem;
    private currentStatus: MrkiStatus = 'stopped';

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.command = 'mrki.status';
        this.updateDisplay();
        this.statusBarItem.show();
    }

    setStatus(status: MrkiStatus): void {
        this.currentStatus = status;
        this.updateDisplay();
    }

    getStatus(): MrkiStatus {
        return this.currentStatus;
    }

    private updateDisplay(): void {
        const icons: Record<MrkiStatus, string> = {
            loading: '$(sync~spin)',
            ready: '$(check)',
            error: '$(error)',
            stopped: '$(circle-slash)'
        };

        const tooltips: Record<MrkiStatus, string> = {
            loading: 'Mrki is starting...',
            ready: 'Mrki is ready',
            error: 'Mrki encountered an error',
            stopped: 'Mrki is stopped'
        };

        this.statusBarItem.text = `${icons[this.currentStatus]} Mrki`;
        this.statusBarItem.tooltip = tooltips[this.currentStatus];
        
        // Update color based on status
        if (this.currentStatus === 'error') {
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        } else if (this.currentStatus === 'ready') {
            this.statusBarItem.backgroundColor = undefined;
        } else {
            this.statusBarItem.backgroundColor = undefined;
        }
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
