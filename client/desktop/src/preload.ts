/**
 * Mrki Desktop - Preload Script
 * Securely exposes Electron APIs to the renderer process
 */

import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getVersion: () => ipcRenderer.invoke('app:get-version'),
  getPlatform: () => ipcRenderer.invoke('app:get-platform'),

  // Theme
  getTheme: () => ipcRenderer.invoke('theme:get'),
  setTheme: (theme: 'light' | 'dark' | 'system') => ipcRenderer.invoke('theme:set', theme),

  // Notifications
  showNotification: (options: {
    title: string;
    body: string;
    icon?: string;
    silent?: boolean;
  }) => ipcRenderer.invoke('notification:show', options),

  // Window control
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),
  hideWindow: () => ipcRenderer.invoke('window:hide'),

  // Event listeners
  onMenuAction: (callback: (action: string) => void) => {
    ipcRenderer.on('menu:new-task', () => callback('new-task'));
    ipcRenderer.on('menu:settings', () => callback('settings'));
  },

  onDeepLink: (callback: (path: string) => void) => {
    ipcRenderer.on('deep-link', (_, path) => callback(path));
  },

  onUpdate: (callback: (event: string, data: any) => void) => {
    ipcRenderer.on('update:available', (_, data) => callback('available', data));
    ipcRenderer.on('update:progress', (_, data) => callback('progress', data));
    ipcRenderer.on('update:downloaded', (_, data) => callback('downloaded', data));
  },

  // Remove listeners
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  },
});

// Type definitions for the exposed API
declare global {
  interface Window {
    electronAPI: {
      getVersion: () => Promise<string>;
      getPlatform: () => Promise<string>;
      getTheme: () => Promise<'light' | 'dark'>;
      setTheme: (theme: 'light' | 'dark' | 'system') => Promise<'light' | 'dark'>;
      showNotification: (options: {
        title: string;
        body: string;
        icon?: string;
        silent?: boolean;
      }) => Promise<boolean>;
      minimizeWindow: () => Promise<void>;
      maximizeWindow: () => Promise<void>;
      closeWindow: () => Promise<void>;
      hideWindow: () => Promise<void>;
      onMenuAction: (callback: (action: string) => void) => void;
      onDeepLink: (callback: (path: string) => void) => void;
      onUpdate: (callback: (event: string, data: any) => void) => void;
      removeAllListeners: (channel: string) => void;
    };
  }
}
