/**
 * Mrki - Electron Preload Script
 * Secure bridge between main and renderer processes
 */
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // App info
  app: {
    getVersion: () => ipcRenderer.invoke('app:get-version'),
    getPlatform: () => ipcRenderer.invoke('app:get-platform'),
  },

  // Window controls
  window: {
    minimize: () => ipcRenderer.invoke('window:minimize'),
    maximize: () => ipcRenderer.invoke('window:maximize'),
    close: () => ipcRenderer.invoke('window:close'),
  },

  // WebSocket helper
  websocket: {
    connect: (url) => ipcRenderer.invoke('websocket:connect', url),
  },

  // Platform detection
  platform: process.platform,
  isElectron: true,
});

// Expose Node.js process info (safe only)
contextBridge.exposeInMainWorld('process', {
  versions: {
    node: process.versions.node,
    electron: process.versions.electron,
    chrome: process.versions.chrome,
  },
  env: {
    NODE_ENV: process.env.NODE_ENV,
  },
});

// Log preload completion
console.log('[Electron] Preload script loaded');
