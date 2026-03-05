/**
 * Local-First Storage Service
 * Unified storage interface with platform-specific implementations
 * Supports offline-first architecture with sync capabilities
 */

import { Platform } from '../types';

// Storage interface
export interface StorageAdapter {
  getItem<T>(key: string): Promise<T | null>;
  setItem<T>(key: string, value: T): Promise<void>;
  removeItem(key: string): Promise<void>;
  clear(): Promise<void>;
  keys(): Promise<string[]>;
  getAll<T>(): Promise<Record<string, T>>;
}

// Storage options
interface StorageOptions {
  prefix?: string;
  encryption?: boolean;
  compression?: boolean;
}

// React Native storage implementation
class ReactNativeStorage implements StorageAdapter {
  private AsyncStorage: any;
  private prefix: string;

  constructor(options: StorageOptions = {}) {
    this.prefix = options.prefix || 'mrki:';
    try {
      this.AsyncStorage = require('@react-native-async-storage/async-storage').default;
    } catch {
      throw new Error('AsyncStorage not available');
    }
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  async getItem<T>(key: string): Promise<T | null> {
    try {
      const value = await this.AsyncStorage.getItem(this.getKey(key));
      if (value === null) return null;
      return JSON.parse(value);
    } catch (error) {
      console.error('Storage getItem error:', error);
      return null;
    }
  }

  async setItem<T>(key: string, value: T): Promise<void> {
    try {
      await this.AsyncStorage.setItem(this.getKey(key), JSON.stringify(value));
    } catch (error) {
      console.error('Storage setItem error:', error);
      throw error;
    }
  }

  async removeItem(key: string): Promise<void> {
    try {
      await this.AsyncStorage.removeItem(this.getKey(key));
    } catch (error) {
      console.error('Storage removeItem error:', error);
      throw error;
    }
  }

  async clear(): Promise<void> {
    try {
      const allKeys = await this.AsyncStorage.getAllKeys();
      const prefixKeys = allKeys.filter((k: string) => k.startsWith(this.prefix));
      await this.AsyncStorage.multiRemove(prefixKeys);
    } catch (error) {
      console.error('Storage clear error:', error);
      throw error;
    }
  }

  async keys(): Promise<string[]> {
    try {
      const allKeys = await this.AsyncStorage.getAllKeys();
      return allKeys
        .filter((k: string) => k.startsWith(this.prefix))
        .map((k: string) => k.slice(this.prefix.length));
    } catch (error) {
      console.error('Storage keys error:', error);
      return [];
    }
  }

  async getAll<T>(): Promise<Record<string, T>> {
    try {
      const keys = await this.keys();
      const entries = await Promise.all(
        keys.map(async (key) => {
          const value = await this.getItem<T>(key);
          return [key, value] as [string, T];
        })
      );
      return Object.fromEntries(entries.filter(([_, v]) => v !== null));
    } catch (error) {
      console.error('Storage getAll error:', error);
      return {};
    }
  }
}

// Web/Electron storage implementation (localStorage + IndexedDB)
class WebStorage implements StorageAdapter {
  private prefix: string;
  private useIndexedDB: boolean;
  private db: IDBDatabase | null = null;
  private dbName: string = 'mrki-storage';
  private storeName: string = 'data';

  constructor(options: StorageOptions = {}) {
    this.prefix = options.prefix || 'mrki:';
    this.useIndexedDB = typeof indexedDB !== 'undefined';
    if (this.useIndexedDB) {
      this.initIndexedDB();
    }
  }

  private async initIndexedDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName);
        }
      };
    });
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  async getItem<T>(key: string): Promise<T | null> {
    const fullKey = this.getKey(key);
    
    // Try IndexedDB first for large data
    if (this.useIndexedDB && this.db) {
      try {
        const transaction = this.db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.get(fullKey);
        
        return new Promise((resolve) => {
          request.onsuccess = () => {
            resolve(request.result ?? null);
          };
          request.onerror = () => resolve(null);
        });
      } catch {
        // Fall through to localStorage
      }
    }
    
    // Fallback to localStorage
    try {
      const value = localStorage.getItem(fullKey);
      if (value === null) return null;
      return JSON.parse(value);
    } catch {
      return null;
    }
  }

  async setItem<T>(key: string, value: T): Promise<void> {
    const fullKey = this.getKey(key);
    const serialized = JSON.stringify(value);
    
    // Use IndexedDB for large data (>1MB)
    if (this.useIndexedDB && this.db && serialized.length > 1000000) {
      try {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        await new Promise<void>((resolve, reject) => {
          const request = store.put(value, fullKey);
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
        return;
      } catch {
        // Fall through to localStorage
      }
    }
    
    // Fallback to localStorage
    try {
      localStorage.setItem(fullKey, serialized);
    } catch (error) {
      // Handle quota exceeded
      if ((error as Error).name === 'QuotaExceededError') {
        await this.evictLRU();
        localStorage.setItem(fullKey, serialized);
      } else {
        throw error;
      }
    }
  }

  async removeItem(key: string): Promise<void> {
    const fullKey = this.getKey(key);
    
    if (this.useIndexedDB && this.db) {
      try {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        await new Promise<void>((resolve, reject) => {
          const request = store.delete(fullKey);
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
      } catch {
        // Fall through
      }
    }
    
    localStorage.removeItem(fullKey);
  }

  async clear(): Promise<void> {
    // Clear localStorage
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(this.prefix)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    // Clear IndexedDB
    if (this.useIndexedDB && this.db) {
      try {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        await new Promise<void>((resolve, reject) => {
          const request = store.clear();
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
      } catch {
        // Ignore errors
      }
    }
  }

  async keys(): Promise<string[]> {
    const keys: string[] = [];
    
    // Get from localStorage
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(this.prefix)) {
        keys.push(key.slice(this.prefix.length));
      }
    }
    
    // Get from IndexedDB
    if (this.useIndexedDB && this.db) {
      try {
        const transaction = this.db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.getAllKeys();
        
        await new Promise<void>((resolve) => {
          request.onsuccess = () => {
            const dbKeys = (request.result as string[])
              .filter(k => k.startsWith(this.prefix))
              .map(k => k.slice(this.prefix.length));
            keys.push(...dbKeys);
            resolve();
          };
          request.onerror = () => resolve();
        });
      } catch {
        // Ignore errors
      }
    }
    
    return [...new Set(keys)];
  }

  async getAll<T>(): Promise<Record<string, T>> {
    const keys = await this.keys();
    const entries = await Promise.all(
      keys.map(async (key) => {
        const value = await this.getItem<T>(key);
        return [key, value] as [string, T];
      })
    );
    return Object.fromEntries(entries.filter(([_, v]) => v !== null));
  }

  // Evict least recently used items when quota exceeded
  private async evictLRU(): Promise<void> {
    const keys: { key: string; timestamp: number }[] = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(this.prefix)) {
        try {
          const value = localStorage.getItem(key);
          if (value) {
            const parsed = JSON.parse(value);
            keys.push({
              key,
              timestamp: parsed._meta?.updatedAt || 0,
            });
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
    
    // Sort by timestamp and remove oldest 10%
    keys.sort((a, b) => a.timestamp - b.timestamp);
    const toRemove = Math.ceil(keys.length * 0.1);
    keys.slice(0, toRemove).forEach(({ key }) => {
      localStorage.removeItem(key);
    });
  }
}

// Storage factory
export const createStorage = (options: StorageOptions = {}): StorageAdapter => {
  const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';
  
  if (isReactNative) {
    return new ReactNativeStorage(options);
  }
  
  return new WebStorage(options);
};

// Default storage instance
let defaultStorage: StorageAdapter | null = null;

export const getStorage = (): StorageAdapter => {
  if (!defaultStorage) {
    defaultStorage = createStorage();
  }
  return defaultStorage;
};

// Entity-specific storage helpers
export class EntityStorage<T extends { id: string }> {
  private storage: StorageAdapter;
  private entityName: string;

  constructor(entityName: string, storage?: StorageAdapter) {
    this.entityName = entityName;
    this.storage = storage || getStorage();
  }

  private getKey(id: string): string {
    return `${this.entityName}:${id}`;
  }

  async get(id: string): Promise<T | null> {
    return this.storage.getItem<T>(this.getKey(id));
  }

  async getAll(): Promise<T[]> {
    const keys = await this.storage.keys();
    const entityKeys = keys.filter(k => k.startsWith(`${this.entityName}:`));
    const entities = await Promise.all(
      entityKeys.map(key => this.storage.getItem<T>(key))
    );
    return entities.filter((e): e is T => e !== null);
  }

  async set(entity: T): Promise<void> {
    const data = {
      ...entity,
      _meta: {
        updatedAt: Date.now(),
        entityType: this.entityName,
      },
    };
    await this.storage.setItem(this.getKey(entity.id), data);
  }

  async delete(id: string): Promise<void> {
    await this.storage.removeItem(this.getKey(id));
  }

  async clear(): Promise<void> {
    const keys = await this.storage.keys();
    const entityKeys = keys.filter(k => k.startsWith(`${this.entityName}:`));
    await Promise.all(entityKeys.map(key => this.storage.removeItem(key)));
  }

  async query(predicate: (entity: T) => boolean): Promise<T[]> {
    const all = await this.getAll();
    return all.filter(predicate);
  }
}

export default {
  createStorage,
  getStorage,
  EntityStorage,
};
