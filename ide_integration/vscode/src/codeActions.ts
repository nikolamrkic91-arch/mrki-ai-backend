/**
 * Mrki Code Actions Provider
 * Provides AI-powered code actions and quick fixes
 */

import * as vscode from 'vscode';
import { Logger } from './utils/logger';

export class MrkiCodeActionsProvider implements vscode.CodeActionProvider {
    private logger: Logger;

    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix,
        vscode.CodeActionKind.RefactorRewrite,
        vscode.CodeActionKind.Source
    ];

    constructor() {
        this.logger = new Logger('CodeActions');
    }

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.CodeAction[] | undefined {
        const actions: vscode.CodeAction[] = [];

        // Add explain action if there's a selection
        if (!range.isEmpty) {
            const explainAction = new vscode.CodeAction(
                'Explain with Mrki',
                vscode.CodeActionKind.Empty
            );
            explainAction.command = {
                command: 'mrki.explainCode',
                title: 'Explain Code'
            };
            actions.push(explainAction);

            // Generate tests action
            const testAction = new vscode.CodeAction(
                'Generate tests with Mrki',
                vscode.CodeActionKind.Source
            );
            testAction.command = {
                command: 'mrki.generateTests',
                title: 'Generate Tests'
            };
            actions.push(testAction);

            // Refactor action
            const refactorAction = new vscode.CodeAction(
                'Refactor with Mrki',
                vscode.CodeActionKind.RefactorRewrite
            );
            refactorAction.command = {
                command: 'mrki.refactor',
                title: 'Refactor Code'
            };
            actions.push(refactorAction);

            // Document action
            const documentAction = new vscode.CodeAction(
                'Add documentation with Mrki',
                vscode.CodeActionKind.Source
            );
            documentAction.command = {
                command: 'mrki.documentCode',
                title: 'Add Documentation'
            };
            actions.push(documentAction);
        }

        return actions;
    }

    resolveCodeAction?(
        codeAction: vscode.CodeAction,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.CodeAction> {
        return codeAction;
    }
}
