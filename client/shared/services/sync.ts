/**
 * Cloud Sync Service
 * Manages synchronization between local storage and cloud backend
 * Implements local-first architecture with conflict resolution
 */

import EventEmitter from 'eventemitter3';
import { SyncState, PendingChange, Agent, Task, ApiResponse } from '../types';
import { StorageAdapter, EntityStorage } from './storage';

interface SyncOptions {
  storage?: StorageAdapter;
  apiClient?: any;
  syncInterval?: number;
  conflictResolution?: 'local' | 'remote' | 'timestamp';
  enableDeltaSync?: boolean;
}

interface SyncResult {
  success: boolean;
  syncedEntities: number;
  conflicts: Conflict[];
  errors: SyncError[];
}

interface Conflict {
  entityType: string;
  entityId: string;
  localVersion: any;
  remoteVersion: any;
  resolution: 'local' | 'remote' | 'merged';
}

interface SyncError {
  entityType: string;
  entityId: string;
  error: string;
}

interface SyncMetadata {
  lastSyncAt: string | null;
  pendingChanges: PendingChange[];
  entityVersions: Record<string, number>;
}

export class SyncService extends EventEmitter {
  private state: SyncState;
  private storage: StorageAdapter;
  private apiClient: any;
  private syncInterval: number;
  private conflictResolution: 'local' | 'remote' | 'timestamp';
  private enableDeltaSync: boolean;
  private syncTimer: ReturnType<typeof setInterval> | null = null;
  private isInitialized: boolean = false;

  private agentStorage: EntityStorage<Agent>;
  private taskStorage: EntityStorage<Task>;

  constructor(options: SyncOptions = {}) {
    super();
    
    this.storage = options.storage || require('./storage').getStorage();
    this.apiClient = options.apiClient;
    this.syncInterval = options.syncInterval || 30000;
    this.conflictResolution = options.conflictResolution || 'timestamp';
    this.enableDeltaSync = options.enableDeltaSync ?? true;

    this.agentStorage = new EntityStorage<Agent>('agents', this.storage);
    this.taskStorage = new EntityStorage<Task>('tasks', this.storage);

    this.state = {
      lastSyncAt: null,
      pendingChanges: [],
      isSyncing: false,
      syncError: null,
    };
  }

  // Initialize sync service
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    await this.loadState();
    this.startAutoSync();
    this.isInitialized = true;
    
    this.emit('initialized');
  }

  // Get current sync state
  getState(): SyncState {
    return { ...this.state };
  }

  // Check if syncing
  isSyncing(): boolean {
    return this.state.isSyncing;
  }

  // Start auto sync
  startAutoSync(): void {
    this.stopAutoSync();
    
    if (this.syncInterval > 0) {
      this.syncTimer = setInterval(() => {
        this.sync();
      }, this.syncInterval);
    }
  }

  // Stop auto sync
  stopAutoSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  }

  // Perform full sync
  async sync(): Promise<SyncResult> {
    if (this.state.isSyncing || !this.apiClient) {
      return {
        success: false,
        syncedEntities: 0,
        conflicts: [],
        errors: [{
          entityType: 'system',
          entityId: 'sync',
          error: this.state.isSyncing ? 'Sync already in progress' : 'No API client',
        }],
      };
    }

    this.state.isSyncing = true;
    this.state.syncError = null;
    this.emit('sync:start');

    const result: SyncResult = {
      success: true,
      syncedEntities: 0,
      conflicts: [],
      errors: [],
    };

    try {
      // 1. Push pending changes to server
      const pushResult = await this.pushPendingChanges();
      result.errors.push(...pushResult.errors);

      // 2. Pull changes from server
      const pullResult = await this.pullChanges();
      result.syncedEntities += pullResult.syncedEntities;
      result.conflicts.push(...pullResult.conflicts);
      result.errors.push(...pullResult.errors);

      // 3. Update last sync time
      this.state.lastSyncAt = new Date().toISOString();
      await this.saveState();

      this.emit('sync:complete', result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.state.syncError = errorMessage;
      result.success = false;
      result.errors.push({
        entityType: 'system',
        entityId: 'sync',
        error: errorMessage,
      });
      this.emit('sync:error', error);
    } finally {
      this.state.isSyncing = false;
    }

    return result;
  }

  // Push pending changes to server
  private async pushPendingChanges(): Promise<{ errors: SyncError[] }> {
    const errors: SyncError[] = [];
    const pendingChanges = [...this.state.pendingChanges];

    for (const change of pendingChanges) {
      try {
        let response: ApiResponse<any>;

        switch (change.operation) {
          case 'create':
            response = await this.apiClient.post(`/${change.entityType}`, change.data);
            break;
          case 'update':
            response = await this.apiClient.put(`/${change.entityType}/${change.entityId}`, change.data);
            break;
          case 'delete':
            response = await this.apiClient.delete(`/${change.entityType}/${change.entityId}`);
            break;
          default:
            continue;
        }

        if (response.success) {
          // Remove from pending changes
          this.state.pendingChanges = this.state.pendingChanges.filter(
            c => c.id !== change.id
          );
          this.emit('change:pushed', change);
        } else {
          change.retryCount++;
          if (change.retryCount >= 3) {
            this.state.pendingChanges = this.state.pendingChanges.filter(
              c => c.id !== change.id
            );
            errors.push({
              entityType: change.entityType,
              entityId: change.entityId,
              error: response.error?.message || 'Push failed',
            });
          }
        }
      } catch (error) {
        change.retryCount++;
        if (change.retryCount >= 3) {
          this.state.pendingChanges = this.state.pendingChanges.filter(
            c => c.id !== change.id
          );
          errors.push({
            entityType: change.entityType,
            entityId: change.entityId,
            error: error instanceof Error ? error.message : 'Push failed',
          });
        }
      }
    }

    await this.saveState();
    return { errors };
  }

  // Pull changes from server
  private async pullChanges(): Promise<{ syncedEntities: number; conflicts: Conflict[]; errors: SyncError[] }> {
    const result = {
      syncedEntities: 0,
      conflicts: [] as Conflict[],
      errors: [] as SyncError[],
    };

    try {
      // Fetch agents
      const agentsResponse = await this.apiClient.get('/agents', {
        params: this.enableDeltaSync && this.state.lastSyncAt
          ? { since: this.state.lastSyncAt }
          : undefined,
      });

      if (agentsResponse.success) {
        for (const remoteAgent of agentsResponse.data || []) {
          const localAgent = await this.agentStorage.get(remoteAgent.id);
          
          if (localAgent) {
            // Check for conflict
            const conflict = this.detectConflict('agents', localAgent, remoteAgent);
            if (conflict) {
              const resolution = this.resolveConflict(conflict);
              result.conflicts.push(resolution);
              
              if (resolution.resolution === 'remote') {
                await this.agentStorage.set(remoteAgent);
                result.syncedEntities++;
              }
            } else {
              await this.agentStorage.set(remoteAgent);
              result.syncedEntities++;
            }
          } else {
            await this.agentStorage.set(remoteAgent);
            result.syncedEntities++;
          }
        }
      }

      // Fetch tasks
      const tasksResponse = await this.apiClient.get('/tasks', {
        params: this.enableDeltaSync && this.state.lastSyncAt
          ? { since: this.state.lastSyncAt }
          : undefined,
      });

      if (tasksResponse.success) {
        for (const remoteTask of tasksResponse.data || []) {
          const localTask = await this.taskStorage.get(remoteTask.id);
          
          if (localTask) {
            const conflict = this.detectConflict('tasks', localTask, remoteTask);
            if (conflict) {
              const resolution = this.resolveConflict(conflict);
              result.conflicts.push(resolution);
              
              if (resolution.resolution === 'remote') {
                await this.taskStorage.set(remoteTask);
                result.syncedEntities++;
              }
            } else {
              await this.taskStorage.set(remoteTask);
              result.syncedEntities++;
            }
          } else {
            await this.taskStorage.set(remoteTask);
            result.syncedEntities++;
          }
        }
      }
    } catch (error) {
      result.errors.push({
        entityType: 'system',
        entityId: 'pull',
        error: error instanceof Error ? error.message : 'Pull failed',
      });
    }

    return result;
  }

  // Queue a local change for sync
  async queueChange(
    entityType: 'agent' | 'task' | 'user' | 'settings',
    entityId: string,
    operation: 'create' | 'update' | 'delete',
    data: any
  ): Promise<void> {
    const change: PendingChange = {
      id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      entityType,
      entityId,
      operation,
      data,
      createdAt: new Date().toISOString(),
      retryCount: 0,
    };

    // Remove any existing pending change for this entity
    this.state.pendingChanges = this.state.pendingChanges.filter(
      c => !(c.entityType === entityType && c.entityId === entityId)
    );

    this.state.pendingChanges.push(change);
    await this.saveState();
    
    this.emit('change:queued', change);

    // Trigger immediate sync if online
    if (!this.state.isSyncing) {
      this.sync();
    }
  }

  // Detect conflict between local and remote versions
  private detectConflict(entityType: string, local: any, remote: any): Conflict | null {
    const localVersion = local._meta?.version || local.updatedAt || 0;
    const remoteVersion = remote._meta?.version || remote.updatedAt || 0;

    if (localVersion === remoteVersion) {
      return null;
    }

    // Simple comparison - in production, use proper versioning
    if (JSON.stringify(local) === JSON.stringify(remote)) {
      return null;
    }

    return {
      entityType,
      entityId: local.id,
      localVersion: local,
      remoteVersion: remote,
      resolution: 'local', // Will be updated by resolveConflict
    };
  }

  // Resolve conflict based on strategy
  private resolveConflict(conflict: Conflict): Conflict {
    switch (this.conflictResolution) {
      case 'local':
        conflict.resolution = 'local';
        break;
      case 'remote':
        conflict.resolution = 'remote';
        break;
      case 'timestamp':
      default:
        const localTime = new Date(conflict.localVersion.updatedAt || 0).getTime();
        const remoteTime = new Date(conflict.remoteVersion.updatedAt || 0).getTime();
        conflict.resolution = remoteTime > localTime ? 'remote' : 'local';
        break;
    }

    this.emit('conflict:resolved', conflict);
    return conflict;
  }

  // Load sync state from storage
  private async loadState(): Promise<void> {
    try {
      const metadata = await this.storage.getItem<SyncMetadata>('mrki:sync:metadata');
      if (metadata) {
        this.state.lastSyncAt = metadata.lastSyncAt;
        this.state.pendingChanges = metadata.pendingChanges || [];
      }
    } catch (error) {
      console.error('Failed to load sync state:', error);
    }
  }

  // Save sync state to storage
  private async saveState(): Promise<void> {
    try {
      const metadata: SyncMetadata = {
        lastSyncAt: this.state.lastSyncAt,
        pendingChanges: this.state.pendingChanges,
        entityVersions: {},
      };
      await this.storage.setItem('mrki:sync:metadata', metadata);
    } catch (error) {
      console.error('Failed to save sync state:', error);
    }
  }

  // Force sync now
  async forceSync(): Promise<SyncResult> {
    return this.sync();
  }

  // Reset sync state
  async reset(): Promise<void> {
    this.stopAutoSync();
    this.state = {
      lastSyncAt: null,
      pendingChanges: [],
      isSyncing: false,
      syncError: null,
    };
    await this.saveState();
    this.startAutoSync();
    this.emit('reset');
  }

  // Dispose
  dispose(): void {
    this.stopAutoSync();
    this.removeAllListeners();
  }
}

// Create singleton instance
let syncService: SyncService | null = null;

export const createSyncService = (options?: SyncOptions): SyncService => {
  syncService = new SyncService(options);
  return syncService;
};

export const getSyncService = (): SyncService | null => {
  return syncService;
};

export default {
  SyncService,
  createSyncService,
  getSyncService,
};
