/**
 * Mrki Desktop - Renderer Process
 * React entry point for the Electron renderer
 */

import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';

// Import shared components
import HomeScreen from '../../src/screens/HomeScreen';
import AgentsScreen from '../../src/screens/AgentsScreen';
import TasksScreen from '../../src/screens/TasksScreen';
import SettingsScreen from '../../src/screens/SettingsScreen';

// Import services
import { createNotificationService } from '../../shared/services/notifications';
import { createSyncService } from '../../shared/services/sync';
import { createWebSocketClient } from '../../shared/services/websocket';

// Import styles
import './styles.css';

// API Configuration
const API_URL = process.env.API_URL || 'http://localhost:3000';
const WS_URL = process.env.WS_URL || 'ws://localhost:3001';

// Initialize services
const initializeServices = async () => {
  // Initialize notifications
  const notifications = createNotificationService({
    requestPermissionsOnInit: true,
  });
  await notifications.initialize();

  // Initialize WebSocket
  const wsClient = createWebSocketClient({
    url: WS_URL,
    autoConnect: true,
    heartbeatInterval: 30000,
  });

  // Initialize sync service
  const syncService = createSyncService({
    apiClient: {
      get: async (path: string, options?: any) => {
        const response = await fetch(`${API_URL}${path}`, options);
        return response.json();
      },
      post: async (path: string, data: any) => {
        const response = await fetch(`${API_URL}${path}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        return response.json();
      },
      put: async (path: string, data: any) => {
        const response = await fetch(`${API_URL}${path}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        return response.json();
      },
      delete: async (path: string) => {
        const response = await fetch(`${API_URL}${path}`, {
          method: 'DELETE',
        });
        return response.json();
      },
    },
    syncInterval: 30000,
  });

  await syncService.initialize();

  // Listen for task completion notifications
  wsClient.on('message:task_complete', async (payload) => {
    // Show native notification via Electron
    if (window.electronAPI) {
      await window.electronAPI.showNotification({
        title: 'Task Completed',
        body: `"${payload.title}" has completed successfully`,
      });
    }
  });

  wsClient.on('message:task_fail', async (payload) => {
    if (window.electronAPI) {
      await window.electronAPI.showNotification({
        title: 'Task Failed',
        body: `"${payload.title}" has failed`,
      });
    }
  });

  // Listen for menu actions
  window.electronAPI?.onMenuAction((action) => {
    console.log('Menu action:', action);
    // Handle menu actions (navigate to different screens)
  });

  // Listen for deep links
  window.electronAPI?.onDeepLink((path) => {
    console.log('Deep link:', path);
    // Handle deep links
  });

  // Listen for updates
  window.electronAPI?.onUpdate((event, data) => {
    console.log('Update event:', event, data);
    // Handle update events
  });
};

// Navigation Component
const Navigation: React.FC = () => {
  const [activeTab, setActiveTab] = useState('home');

  const navItems = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
    { id: 'tasks', label: 'Tasks', icon: '✓' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <nav className="sidebar-nav">
      <div className="nav-header">
        <h1>Mrki</h1>
        <span className="version">v1.0.0</span>
      </div>
      <ul className="nav-list">
        {navItems.map((item) => (
          <li
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </li>
        ))}
      </ul>
    </nav>
  );
};

// Main App Layout
const AppLayout: React.FC = () => {
  const [activeTab, setActiveTab] = useState('home');

  useEffect(() => {
    initializeServices();
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <HomeScreen />;
      case 'agents':
        return <AgentsScreen />;
      case 'tasks':
        return <TasksScreen />;
      case 'settings':
        return <SettingsScreen />;
      default:
        return <HomeScreen />;
    }
  };

  const navItems = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
    { id: 'tasks', label: 'Tasks', icon: '✓' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Mrki</h1>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-button ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
};

// Root App Component
const App: React.FC = () => {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<AppLayout />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
};

// Mount the app
const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
