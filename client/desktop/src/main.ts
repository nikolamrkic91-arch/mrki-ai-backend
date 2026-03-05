/**
 * Mrki Desktop - Electron Main Process
 * Entry point for the Windows desktop application
 */

import { app, BrowserWindow, ipcMain, nativeTheme, Notification, Tray, Menu, shell } from 'electron';
import * as path from 'path';
import * as log from 'electron-log';
import { autoUpdater } from 'electron-updater';

// Configure logging
log.transports.file.level = 'info';
log.info('Application starting...');

// Constants
const isDevelopment = process.env.NODE_ENV === 'development';
const APP_NAME = 'Mrki';
const DEFAULT_WIDTH = 1400;
const DEFAULT_HEIGHT = 900;
const MIN_WIDTH = 800;
const MIN_HEIGHT = 600;

// Global references
let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

// Create main window
const createWindow = (): void => {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT,
    minWidth: MIN_WIDTH,
    minHeight: MIN_HEIGHT,
    title: APP_NAME,
    icon: path.join(__dirname, '../assets/icon.png'),
    show: false, // Show when ready
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: false,
    },
    titleBarStyle: 'default',
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#1a1a1a' : '#ffffff',
  });

  // Load the app
  if (isDevelopment) {
    // Load from webpack dev server in development
    mainWindow.loadURL('http://localhost:3000');
    // Open DevTools
    mainWindow.webContents.openDevTools();
  } else {
    // Load built files in production
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
    
    // Check for updates in production
    if (!isDevelopment) {
      autoUpdater.checkForUpdatesAndNotify();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Create tray icon
  createTray();
};

// Create system tray
const createTray = (): void => {
  const iconPath = path.join(__dirname, '../assets/tray-icon.png');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Mrki',
      click: () => {
        mainWindow?.show();
        mainWindow?.focus();
      },
    },
    {
      label: 'New Task',
      click: () => {
        mainWindow?.show();
        mainWindow?.webContents.send('menu:new-task');
      },
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        mainWindow?.show();
        mainWindow?.webContents.send('menu:settings');
      },
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quit();
      },
    },
  ]);

  tray.setToolTip(APP_NAME);
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow?.show();
      mainWindow?.focus();
    }
  });
};

// App event handlers
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    // On macOS, re-create window when dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // On Windows, quit when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // Someone tried to run a second instance, focus our window instead
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }
      mainWindow.focus();
    }
  });
}

// IPC handlers
ipcMain.handle('app:get-version', () => {
  return app.getVersion();
});

ipcMain.handle('app:get-platform', () => {
  return process.platform;
});

ipcMain.handle('theme:get', () => {
  return nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
});

ipcMain.handle('theme:set', (_, theme: 'light' | 'dark' | 'system') => {
  nativeTheme.themeSource = theme;
  return nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
});

// Notification handler
ipcMain.handle('notification:show', (_, options: {
  title: string;
  body: string;
  icon?: string;
  silent?: boolean;
}) => {
  if (Notification.isSupported()) {
    const notification = new Notification({
      title: options.title,
      body: options.body,
      icon: options.icon || path.join(__dirname, '../assets/icon.png'),
      silent: options.silent,
    });

    notification.on('click', () => {
      mainWindow?.show();
      mainWindow?.focus();
    });

    notification.show();
    return true;
  }
  return false;
});

// Window control handlers
ipcMain.handle('window:minimize', () => {
  mainWindow?.minimize();
});

ipcMain.handle('window:maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});

ipcMain.handle('window:close', () => {
  mainWindow?.close();
});

ipcMain.handle('window:hide', () => {
  mainWindow?.hide();
});

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
  log.info('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
  log.info('Update available:', info);
  mainWindow?.webContents.send('update:available', info);
});

autoUpdater.on('update-not-available', () => {
  log.info('Update not available');
});

autoUpdater.on('error', (err) => {
  log.error('Update error:', err);
});

autoUpdater.on('download-progress', (progress) => {
  log.info('Download progress:', progress);
  mainWindow?.webContents.send('update:progress', progress);
});

autoUpdater.on('update-downloaded', (info) => {
  log.info('Update downloaded:', info);
  mainWindow?.webContents.send('update:downloaded', info);
  
  // Show notification
  if (Notification.isSupported()) {
    const notification = new Notification({
      title: 'Update Ready',
      body: 'A new version of Mrki is ready to install. Click to restart.',
    });
    
    notification.on('click', () => {
      autoUpdater.quitAndInstall();
    });
    
    notification.show();
  }
});

// Handle protocol activation (deep links)
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('mrki', process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient('mrki');
}

app.on('open-url', (event, url) => {
  event.preventDefault();
  log.info('Opened with URL:', url);
  
  // Parse and handle deep link
  const urlObj = new URL(url);
  if (urlObj.protocol === 'mrki:') {
    mainWindow?.webContents.send('deep-link', urlObj.pathname);
  }
});
