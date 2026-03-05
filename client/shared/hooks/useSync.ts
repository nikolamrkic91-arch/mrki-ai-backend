/**
 * Sync Hook
 * React hook for cloud synchronization
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { SyncService } from '../services/sync';
import { SyncState, Agent, Task } from '../types';
import { EntityStorage } from '../services/storage';

interface UseSyncOptions {
  apiClient: any;
  syncInterval?: number;
  autoStart?: boolean;
}

interface UseSyncReturn {
  syncState: SyncState;
  isSyncing: boolean;
  lastSyncAt: string | null;
  pendingChangesCount: number;
  sync: () => Promise<void>;
  forceSync: () => Promise<void>;
  reset: () => Promise<void>;
}

export const useSync = (options: UseSyncOptions): UseSyncReturn => {
  const serviceRef = useRef<SyncService | null>(null);
  const [syncState, setSyncState] = useState<SyncState>({
    lastSyncAt: null,
    pendingChanges: [],
    isSyncing: false,
    syncError: null,
  });

  // Initialize sync service
  useEffect(() => {
    const service = new SyncService({
      apiClient: options.apiClient,
      syncInterval: options.syncInterval,
    });

    service.on('sync:start', () => {
      setSyncState(service.getState());
    });

    service.on('sync:complete', () => {
      setSyncState(service.getState());
    });

    service.on('sync:error', () => {
      setSyncState(service.getState());
    });

    service.on('change:queued', () => {
      setSyncState(service.getState());
    });

    serviceRef.current = service;

    if (options.autoStart !== false) {
      service.initialize();
    }

    return () => {
      service.dispose();
    };
  }, []);

  const sync = useCallback(async () => {
    if (serviceRef.current) {
      await serviceRef.current.sync();
    }
  }, []);

  const forceSync = useCallback(async () => {
    if (serviceRef.current) {
      await serviceRef.current.forceSync();
    }
  }, []);

  const reset = useCallback(async () => {
    if (serviceRef.current) {
      await serviceRef.current.reset();
    }
  }, []);

  return {
    syncState,
    isSyncing: syncState.isSyncing,
    lastSyncAt: syncState.lastSyncAt,
    pendingChangesCount: syncState.pendingChanges.length,
    sync,
    forceSync,
    reset,
  };
};

// Hook for local entities with sync
interface UseLocalEntitiesOptions<T> {
  entityName: 'agents' | 'tasks';
  storage?: EntityStorage<T>;
}

interface UseLocalEntitiesReturn<T> {
  entities: T[];
  getById: (id: string) => Promise<T | null>;
  save: (entity: T) => Promise<void>;
  remove: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export const useLocalEntities = <T extends { id: string }>(
  options: UseLocalEntitiesOptions<T>
): UseLocalEntitiesReturn<T> => {
  const storageRef = useRef<EntityStorage<T> | null>(null);
  const [entities, setEntities] = useState<T[]>([]);

  // Initialize storage
  useEffect(() => {
    storageRef.current = new EntityStorage<T>(options.entityName, options.storage);
    refresh();
  }, [options.entityName]);

  const refresh = useCallback(async () => {
    if (storageRef.current) {
      const data = await storageRef.current.getAll();
      setEntities(data);
    }
  }, []);

  const getById = useCallback(async (id: string): Promise<T | null> => {
    if (storageRef.current) {
      return storageRef.current.get(id);
    }
    return null;
  }, []);

  const save = useCallback(async (entity: T): Promise<void> => {
    if (storageRef.current) {
      await storageRef.current.set(entity);
      await refresh();
    }
  }, []);

  const remove = useCallback(async (id: string): Promise<void> => {
    if (storageRef.current) {
      await storageRef.current.delete(id);
      await refresh();
    }
  }, []);

  return {
    entities,
    getById,
    save,
    remove,
    refresh,
  };
};

// Hook for agents
export const useAgents = () => {
  return useLocalEntities<Agent>({ entityName: 'agents' });
};

// Hook for tasks
export const useTasks = () => {
  return useLocalEntities<Task>({ entityName: 'tasks' });
};

export default useSync;
