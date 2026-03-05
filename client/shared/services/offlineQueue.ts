/**
 * Offline Queue System
 * Manages actions when offline and syncs when connection is restored
 */

import EventEmitter from 'eventemitter3';
import { QueuedAction } from '../types';
import { StorageAdapter } from './storage';

interface OfflineQueueOptions {
  storage?: StorageAdapter;
  maxQueueSize?: number;
  defaultMaxRetries?: number;
  retryDelay?: number;
  storageKey?: string;
}

type ActionHandler = (action: QueuedAction) => Promise<boolean>;

export class OfflineQueue extends EventEmitter {
  private queue: QueuedAction[] = [];
  private storage: StorageAdapter | null = null;
  private storageKey: string = 'mrki:offline-queue';
  private maxQueueSize: number = 1000;
  private defaultMaxRetries: number = 3;
  private retryDelay: number = 5000;
  private handlers: Map<string, ActionHandler> = new Map();
  private isProcessing: boolean = false;
  private isOnline: boolean = true;

  constructor(options: OfflineQueueOptions = {}) {
    super();
    
    this.storage = options.storage || null;
    this.maxQueueSize = options.maxQueueSize || 1000;
    this.defaultMaxRetries = options.defaultMaxRetries || 3;
    this.retryDelay = options.retryDelay || 5000;
    this.storageKey = options.storageKey || 'mrki:offline-queue';

    this.loadQueue();
    this.setupNetworkListeners();
  }

  // Register action handler
  registerHandler(actionType: string, handler: ActionHandler): void {
    this.handlers.set(actionType, handler);
  }

  // Unregister action handler
  unregisterHandler(actionType: string): void {
    this.handlers.delete(actionType);
  }

  // Queue an action
  async queueAction(
    type: string,
    payload: any,
    options: { priority?: number; maxRetries?: number } = {}
  ): Promise<string> {
    const action: QueuedAction = {
      id: this.generateId(),
      type,
      payload,
      priority: options.priority ?? 0,
      createdAt: new Date().toISOString(),
      retryCount: 0,
      maxRetries: options.maxRetries ?? this.defaultMaxRetries,
    };

    // Check queue size limit
    if (this.queue.length >= this.maxQueueSize) {
      // Remove lowest priority, oldest action
      this.queue.sort((a, b) => {
        if (a.priority !== b.priority) return a.priority - b.priority;
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      });
      this.queue.shift();
      this.emit('action:dropped', action);
    }

    this.queue.push(action);
    await this.saveQueue();
    
    this.emit('action:queued', action);

    // Try to process immediately if online
    if (this.isOnline) {
      this.processQueue();
    }

    return action.id;
  }

  // Remove an action from queue
  async removeAction(actionId: string): Promise<boolean> {
    const index = this.queue.findIndex(a => a.id === actionId);
    if (index === -1) return false;
    
    const action = this.queue.splice(index, 1)[0];
    await this.saveQueue();
    
    this.emit('action:removed', action);
    return true;
  }

  // Get current queue
  getQueue(): QueuedAction[] {
    return [...this.queue];
  }

  // Get queue length
  getQueueLength(): number {
    return this.queue.length;
  }

  // Clear queue
  async clearQueue(): Promise<void> {
    this.queue = [];
    await this.saveQueue();
    this.emit('queue:cleared');
  }

  // Process all queued actions
  async processQueue(): Promise<void> {
    if (this.isProcessing || !this.isOnline || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;
    this.emit('processing:start');

    // Sort by priority (higher first) and then by creation time
    this.queue.sort((a, b) => {
      if (b.priority !== a.priority) return b.priority - a.priority;
      return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
    });

    const failedActions: QueuedAction[] = [];

    while (this.queue.length > 0 && this.isOnline) {
      const action = this.queue[0];
      const handler = this.handlers.get(action.type);

      if (!handler) {
        console.warn(`No handler registered for action type: ${action.type}`);
        this.queue.shift();
        this.emit('action:skipped', action, 'No handler');
        continue;
      }

      try {
        this.emit('action:processing', action);
        const success = await handler(action);

        if (success) {
          this.queue.shift();
          this.emit('action:success', action);
        } else {
          action.retryCount++;
          if (action.retryCount >= action.maxRetries) {
            this.queue.shift();
            this.emit('action:failed', action, 'Max retries exceeded');
          } else {
            // Move to end of queue for retry
            this.queue.shift();
            failedActions.push(action);
            this.emit('action:retry', action);
          }
        }
      } catch (error) {
        action.retryCount++;
        if (action.retryCount >= action.maxRetries) {
          this.queue.shift();
          this.emit('action:failed', action, error);
        } else {
          this.queue.shift();
          failedActions.push(action);
          this.emit('action:retry', action, error);
        }
      }

      await this.saveQueue();
    }

    // Add failed actions back to queue
    this.queue.push(...failedActions);
    await this.saveQueue();

    this.isProcessing = false;
    this.emit('processing:end');

    // If there are still failed actions, schedule retry
    if (failedActions.length > 0 && this.isOnline) {
      setTimeout(() => this.processQueue(), this.retryDelay);
    }
  }

  // Set online status
  setOnline(online: boolean): void {
    const wasOffline = !this.isOnline && online;
    this.isOnline = online;
    
    if (wasOffline) {
      this.emit('online');
      this.processQueue();
    } else if (!online) {
      this.emit('offline');
    }
  }

  // Get online status
  isOnlineStatus(): boolean {
    return this.isOnline;
  }

  // Setup network status listeners
  private setupNetworkListeners(): void {
    if (typeof window !== 'undefined' && 'addEventListener' in window) {
      window.addEventListener('online', () => {
        this.setOnline(true);
      });
      
      window.addEventListener('offline', () => {
        this.setOnline(false);
      });

      // Initial state
      this.isOnline = navigator.onLine;
    }

    // React Native NetInfo
    if (typeof navigator !== 'undefined' && navigator.product === 'ReactNative') {
      try {
        const NetInfo = require('@react-native-community/netinfo').default;
        NetInfo.addEventListener((state: any) => {
          this.setOnline(state.isConnected ?? false);
        });
      } catch {
        // NetInfo not available
      }
    }
  }

  // Load queue from storage
  private async loadQueue(): Promise<void> {
    if (!this.storage) return;
    
    try {
      const data = await this.storage.getItem<QueuedAction[]>(this.storageKey);
      if (data) {
        this.queue = data;
        this.emit('queue:loaded', this.queue.length);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
    }
  }

  // Save queue to storage
  private async saveQueue(): Promise<void> {
    if (!this.storage) return;
    
    try {
      await this.storage.setItem(this.storageKey, this.queue);
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  // Generate unique ID
  private generateId(): string {
    return `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Create singleton instance
let offlineQueue: OfflineQueue | null = null;

export const createOfflineQueue = (options?: OfflineQueueOptions): OfflineQueue => {
  offlineQueue = new OfflineQueue(options);
  return offlineQueue;
};

export const getOfflineQueue = (): OfflineQueue | null => {
  return offlineQueue;
};

// Common action types
export const ActionTypes = {
  CREATE_AGENT: 'CREATE_AGENT',
  UPDATE_AGENT: 'UPDATE_AGENT',
  DELETE_AGENT: 'DELETE_AGENT',
  CREATE_TASK: 'CREATE_TASK',
  UPDATE_TASK: 'UPDATE_TASK',
  DELETE_TASK: 'DELETE_TASK',
  SEND_MESSAGE: 'SEND_MESSAGE',
  UPDATE_SETTINGS: 'UPDATE_SETTINGS',
} as const;

export default {
  OfflineQueue,
  createOfflineQueue,
  getOfflineQueue,
  ActionTypes,
};
