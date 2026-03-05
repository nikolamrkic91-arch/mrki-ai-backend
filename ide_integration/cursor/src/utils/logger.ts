/**
 * Logger Utility for Cursor Integration
 */

import * as vscode from 'vscode';

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
}

export class Logger {
    private static outputChannel: vscode.OutputChannel | undefined;
    private static logLevel: LogLevel = LogLevel.INFO;
    private prefix: string;

    constructor(prefix: string) {
        this.prefix = prefix;
        if (!Logger.outputChannel) {
            Logger.outputChannel = vscode.window.createOutputChannel('Mrki Cursor');
        }
    }

    static setLogLevel(level: LogLevel): void {
        Logger.logLevel = level;
    }

    debug(message: string, ...args: any[]): void {
        this.log(LogLevel.DEBUG, message, ...args);
    }

    info(message: string, ...args: any[]): void {
        this.log(LogLevel.INFO, message, ...args);
    }

    warn(message: string, ...args: any[]): void {
        this.log(LogLevel.WARN, message, ...args);
    }

    error(message: string, ...args: any[]): void {
        this.log(LogLevel.ERROR, message, ...args);
    }

    private log(level: LogLevel, message: string, ...args: any[]): void {
        if (level < Logger.logLevel) return;

        const timestamp = new Date().toISOString();
        const levelStr = LogLevel[level];
        const formatted = `[${timestamp}] [${levelStr}] [${this.prefix}] ${message}`;
        
        if (args.length > 0) {
            Logger.outputChannel?.appendLine(`${formatted} ${args.map(a => 
                typeof a === 'object' ? JSON.stringify(a) : String(a)
            ).join(' ')}`);
        } else {
            Logger.outputChannel?.appendLine(formatted);
        }
    }

    dispose(): void {
        Logger.outputChannel?.dispose();
        Logger.outputChannel = undefined;
    }
}
