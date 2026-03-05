/**
 * Notification Service
 * Handles push notifications across all platforms
 * iOS/Android: Native push notifications
 * Windows/Desktop: Electron notifications
 * Web: Service Worker notifications
 */

import EventEmitter from 'eventemitter3';
import { Notification, NotificationType } from '../types';

interface NotificationOptions {
  requestPermissionsOnInit?: boolean;
  defaultChannelId?: string;
  defaultChannelName?: string;
}

interface NotificationPayload {
  title: string;
  body: string;
  data?: Record<string, any>;
  icon?: string;
  image?: string;
  actions?: NotificationAction[];
}

interface NotificationAction {
  id: string;
  title: string;
  icon?: string;
}

export class NotificationService extends EventEmitter {
  private isInitialized: boolean = false;
  private hasPermission: boolean = false;
  private defaultChannelId: string;
  private defaultChannelName: string;
  private isReactNative: boolean;
  private isElectron: boolean;
  private notificationModule: any = null;

  constructor(options: NotificationOptions = {}) {
    super();
    
    this.defaultChannelId = options.defaultChannelId || 'mrki-default';
    this.defaultChannelName = options.defaultChannelName || 'Mrki Notifications';
    this.isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';
    this.isElectron = this.detectElectron();

    if (options.requestPermissionsOnInit !== false) {
      this.initialize();
    }
  }

  // Detect Electron environment
  private detectElectron(): boolean {
    if (typeof window !== 'undefined' && (window as any).process?.type) {
      return true;
    }
    if (typeof navigator !== 'undefined' && navigator.userAgent.includes('Electron')) {
      return true;
    }
    return false;
  }

  // Initialize notification service
  async initialize(): Promise<boolean> {
    if (this.isInitialized) return this.hasPermission;

    try {
      if (this.isReactNative) {
        await this.initializeReactNative();
      } else if (this.isElectron) {
        await this.initializeElectron();
      } else {
        await this.initializeWeb();
      }
      
      this.isInitialized = true;
      this.emit('initialized', this.hasPermission);
      return this.hasPermission;
    } catch (error) {
      console.error('Failed to initialize notifications:', error);
      this.emit('error', error);
      return false;
    }
  }

  // Initialize React Native notifications
  private async initializeReactNative(): Promise<void> {
    try {
      const Notifications = require('react-native-notifications').Notifications;
      this.notificationModule = Notifications;

      // Register for remote notifications
      Notifications.registerRemoteNotifications();

      // Event listeners
      Notifications.events().registerRemoteNotificationsRegistered((event: any) => {
        this.emit('token:received', event.deviceToken);
      });

      Notifications.events().registerRemoteNotificationsRegistrationFailed((event: any) => {
        console.error('Failed to register for notifications:', event);
        this.emit('registration:failed', event);
      });

      Notifications.events().registerNotificationReceivedForeground((notification: any, completion: any) => {
        this.emit('notification:received', this.parseNativeNotification(notification));
        completion({ alert: true, sound: true, badge: true });
      });

      Notifications.events().registerNotificationReceivedBackground((notification: any, completion: any) => {
        this.emit('notification:received', this.parseNativeNotification(notification));
        completion({ alert: true, sound: true, badge: true });
      });

      Notifications.events().registerNotificationOpened((notification: any, completion: any) => {
        this.emit('notification:opened', this.parseNativeNotification(notification));
        completion();
      });

      // Create notification channel for Android
      if (this.isAndroid()) {
        Notifications.setNotificationChannel({
          channelId: this.defaultChannelId,
          name: this.defaultChannelName,
          importance: 4, // High
          enableLights: true,
          enableVibration: true,
        });
      }

      // Request permissions
      const status = await Notifications.requestPermissions();
      this.hasPermission = status;
    } catch (error) {
      console.error('React Native notifications not available:', error);
    }
  }

  // Initialize Electron notifications
  private async initializeElectron(): Promise<void> {
    // Electron uses HTML5 Notification API
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      this.hasPermission = permission === 'granted';
    }
  }

  // Initialize Web notifications
  private async initializeWeb(): Promise<void> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return;
    }

    if (Notification.permission === 'granted') {
      this.hasPermission = true;
    } else if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.hasPermission = permission === 'granted';
    }

    // Register service worker for push notifications
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.ready;
        
        // Listen for push messages
        navigator.serviceWorker.addEventListener('message', (event) => {
          if (event.data?.type === 'PUSH_NOTIFICATION') {
            this.emit('notification:received', event.data.notification);
          }
        });

        this.emit('service-worker:ready', registration);
      } catch (error) {
        console.error('Service worker not available:', error);
      }
    }
  }

  // Request permission
  async requestPermission(): Promise<boolean> {
    if (this.isReactNative) {
      try {
        const status = await this.notificationModule.requestPermissions();
        this.hasPermission = status;
        return status;
      } catch {
        return false;
      }
    }

    if (!('Notification' in window)) {
      return false;
    }

    const permission = await Notification.requestPermission();
    this.hasPermission = permission === 'granted';
    return this.hasPermission;
  }

  // Check permission status
  getPermissionStatus(): boolean {
    return this.hasPermission;
  }

  // Show local notification
  async showNotification(
    type: NotificationType,
    payload: NotificationPayload
  ): Promise<string | null> {
    if (!this.hasPermission) {
      console.warn('Notification permission not granted');
      return null;
    }

    const notificationId = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      if (this.isReactNative) {
        await this.showReactNativeNotification(notificationId, type, payload);
      } else if (this.isElectron) {
        await this.showElectronNotification(notificationId, type, payload);
      } else {
        await this.showWebNotification(notificationId, type, payload);
      }

      const notification: Notification = {
        id: notificationId,
        type,
        title: payload.title,
        body: payload.body,
        data: payload.data,
        read: false,
        createdAt: new Date().toISOString(),
      };

      this.emit('notification:shown', notification);
      return notificationId;
    } catch (error) {
      console.error('Failed to show notification:', error);
      return null;
    }
  }

  // Show React Native notification
  private async showReactNativeNotification(
    id: string,
    type: NotificationType,
    payload: NotificationPayload
  ): Promise<void> {
    const Notifications = this.notificationModule;
    
    const notification = Notifications.postLocalNotification({
      title: payload.title,
      body: payload.body,
      sound: 'default',
      badge: 1,
      channelId: this.defaultChannelId,
      payload: { id, type, ...payload.data },
    });
  }

  // Show Electron notification
  private async showElectronNotification(
    id: string,
    type: NotificationType,
    payload: NotificationPayload
  ): Promise<void> {
    const notification = new window.Notification(payload.title, {
      body: payload.body,
      icon: payload.icon || '/assets/icon.png',
      badge: payload.image,
      data: { id, type, ...payload.data },
      requireInteraction: type === 'task_complete' || type === 'task_fail',
    });

    notification.onclick = () => {
      this.emit('notification:clicked', { id, type, ...payload.data });
      window.focus();
    };
  }

  // Show Web notification
  private async showWebNotification(
    id: string,
    type: NotificationType,
    payload: NotificationPayload
  ): Promise<void> {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.ready;
      
      await registration.showNotification(payload.title, {
        body: payload.body,
        icon: payload.icon || '/icon-192x192.png',
        badge: payload.icon || '/icon-72x72.png',
        image: payload.image,
        data: { id, type, ...payload.data },
        actions: payload.actions || [],
        requireInteraction: type === 'task_complete' || type === 'task_fail',
        tag: id,
        renotify: true,
      });
    } else {
      // Fallback to regular Notification API
      const notification = new Notification(payload.title, {
        body: payload.body,
        icon: payload.icon || '/icon-192x192.png',
        badge: payload.image,
        data: { id, type, ...payload.data },
        requireInteraction: type === 'task_complete' || type === 'task_fail',
      });

      notification.onclick = () => {
        this.emit('notification:clicked', { id, type, ...payload.data });
        window.focus();
      };
    }
  }

  // Cancel notification
  async cancelNotification(notificationId: string): Promise<void> {
    if (this.isReactNative) {
      // React Native doesn't support canceling local notifications directly
      return;
    }

    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.ready;
      const notifications = await registration.getNotifications({ tag: notificationId });
      notifications.forEach(n => n.close());
    }
  }

  // Cancel all notifications
  async cancelAllNotifications(): Promise<void> {
    if (this.isReactNative) {
      // React Native doesn't support this directly
      return;
    }

    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.ready;
      const notifications = await registration.getNotifications();
      notifications.forEach(n => n.close());
    }
  }

  // Schedule notification
  async scheduleNotification(
    type: NotificationType,
    payload: NotificationPayload,
    date: Date
  ): Promise<string | null> {
    if (this.isReactNative) {
      try {
        const Notifications = this.notificationModule;
        const fireDate = date.toISOString();
        
        const notification = Notifications.postLocalNotification({
          title: payload.title,
          body: payload.body,
          sound: 'default',
          fireDate,
          channelId: this.defaultChannelId,
          payload: { type, ...payload.data },
        });

        return notification.identifier;
      } catch (error) {
        console.error('Failed to schedule notification:', error);
        return null;
      }
    }

    // Web and Electron don't support scheduled notifications natively
    // Use setTimeout as fallback
    const delay = date.getTime() - Date.now();
    if (delay > 0) {
      setTimeout(() => {
        this.showNotification(type, payload);
      }, delay);
    }

    return null;
  }

  // Set badge count
  async setBadgeCount(count: number): Promise<void> {
    if (this.isReactNative) {
      // Use native module for badge
      return;
    }

    if ('setAppBadge' in navigator) {
      try {
        if (count > 0) {
          await (navigator as any).setAppBadge(count);
        } else {
          await (navigator as any).clearAppBadge();
        }
      } catch (error) {
        console.error('Failed to set badge:', error);
      }
    }
  }

  // Parse native notification to our format
  private parseNativeNotification(nativeNotif: any): Notification {
    const payload = nativeNotif.payload || nativeNotif.data || {};
    
    return {
      id: payload.id || nativeNotif.identifier || `notif_${Date.now()}`,
      type: payload.type || 'system',
      title: nativeNotif.title || payload.title || '',
      body: nativeNotif.body || nativeNotif.message || payload.body || '',
      data: payload,
      read: false,
      createdAt: new Date().toISOString(),
    };
  }

  // Check if Android
  private isAndroid(): boolean {
    if (this.isReactNative) {
      try {
        const { Platform } = require('react-native');
        return Platform.OS === 'android';
      } catch {
        return false;
      }
    }
    return /android/i.test(navigator.userAgent);
  }

  // Dispose
  dispose(): void {
    this.removeAllListeners();
  }
}

// Create singleton instance
let notificationService: NotificationService | null = null;

export const createNotificationService = (options?: NotificationOptions): NotificationService => {
  notificationService = new NotificationService(options);
  return notificationService;
};

export const getNotificationService = (): NotificationService | null => {
  return notificationService;
};

// Helper for task completion notifications
export const showTaskCompletionNotification = async (
  service: NotificationService,
  taskTitle: string,
  taskId: string,
  success: boolean = true
): Promise<string | null> => {
  return service.showNotification(
    success ? 'task_complete' : 'task_fail',
    {
      title: success ? 'Task Completed' : 'Task Failed',
      body: `"${taskTitle}" has ${success ? 'completed successfully' : 'failed'}`,
      data: { taskId, taskTitle },
      actions: [
        { id: 'view', title: 'View' },
        { id: 'dismiss', title: 'Dismiss' },
      ],
    }
  );
};

export default {
  NotificationService,
  createNotificationService,
  getNotificationService,
  showTaskCompletionNotification,
};
