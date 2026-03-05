/**
 * Shared types for Mrki Client
 * Platform-agnostic type definitions
 */

// Platform types
export type Platform = 'ios' | 'android' | 'windows' | 'web' | 'unknown';

export type DeviceType = 'mobile' | 'tablet' | 'desktop';

// User types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  preferences: UserPreferences;
  createdAt: string;
  updatedAt: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  language: string;
  timezone: string;
}

// Agent types
export interface Agent {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  type: AgentType;
  config: AgentConfig;
  createdAt: string;
  updatedAt: string;
  lastRunAt?: string;
}

export type AgentStatus = 'idle' | 'running' | 'paused' | 'error' | 'completed';

export type AgentType = 'task' | 'research' | 'code' | 'chat' | 'custom';

export interface AgentConfig {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  tools?: string[];
  [key: string]: any;
}

// Task types
export interface Task {
  id: string;
  agentId: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  input?: string;
  output?: string;
  metadata?: Record<string, any>;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

export type TaskStatus = 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

// Message types for WebSocket
export interface WebSocketMessage {
  type: MessageType;
  payload: any;
  timestamp: number;
  id: string;
}

export type MessageType =
  | 'auth'
  | 'auth_success'
  | 'auth_error'
  | 'ping'
  | 'pong'
  | 'subscribe'
  | 'unsubscribe'
  | 'task_create'
  | 'task_update'
  | 'task_complete'
  | 'task_fail'
  | 'agent_status'
  | 'notification'
  | 'sync_request'
  | 'sync_response'
  | 'error';

// Sync types
export interface SyncState {
  lastSyncAt: string | null;
  pendingChanges: PendingChange[];
  isSyncing: boolean;
  syncError: string | null;
}

export interface PendingChange {
  id: string;
  entityType: 'agent' | 'task' | 'user' | 'settings';
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  data: any;
  createdAt: string;
  retryCount: number;
}

// Offline queue types
export interface QueuedAction {
  id: string;
  type: string;
  payload: any;
  priority: number;
  createdAt: string;
  retryCount: number;
  maxRetries: number;
}

// Notification types
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  data?: Record<string, any>;
  read: boolean;
  createdAt: string;
}

export type NotificationType = 'task_complete' | 'task_fail' | 'agent_status' | 'system' | 'mention';

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: ApiMeta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface ApiMeta {
  page?: number;
  limit?: number;
  total?: number;
  hasMore?: boolean;
}

// Connection types
export interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  lastConnectedAt: string | null;
  reconnectAttempts: number;
  latency: number;
}

// Settings types
export interface AppSettings {
  apiUrl: string;
  wsUrl: string;
  syncInterval: number;
  maxOfflineQueue: number;
  enableAnalytics: boolean;
  enableCrashReporting: boolean;
}

// Theme types
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    success: string;
    warning: string;
    info: string;
  };
  fonts: {
    regular: string;
    medium: string;
    bold: string;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
}
