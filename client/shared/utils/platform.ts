/**
 * Platform Detection Utilities
 * Detects the current platform and provides platform-specific helpers
 */

import { Platform, DeviceType } from '../types';

// Check if running in React Native
const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

// Check if running in Electron
const isElectron = () => {
  if (typeof window !== 'undefined' && window.process && window.process.type) {
    return true;
  }
  if (typeof navigator !== 'undefined' && navigator.userAgent.indexOf('Electron') >= 0) {
    return true;
  }
  return false;
};

// Check if running in browser
const isBrowser = () => {
  return typeof window !== 'undefined' && !isReactNative && !isElectron();
};

// Get current platform
export const getPlatform = (): Platform => {
  if (isReactNative) {
    // In React Native, use Platform module
    try {
      const { Platform } = require('react-native');
      return Platform.OS === 'ios' ? 'ios' : 'android';
    } catch {
      return 'unknown';
    }
  }
  
  if (isElectron()) {
    return 'windows';
  }
  
  if (isBrowser()) {
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('win')) return 'windows';
    if (userAgent.includes('mac')) return 'ios'; // macOS treated as iOS-like
    if (userAgent.includes('linux')) return 'android'; // Linux treated as Android-like
    return 'web';
  }
  
  return 'unknown';
};

// Get device type
export const getDeviceType = (): DeviceType => {
  if (isReactNative) {
    try {
      const { Platform, Dimensions } = require('react-native');
      const { width, height } = Dimensions.get('window');
      const screenSize = Math.min(width, height);
      
      // Tablets typically have larger screens
      if (screenSize > 600) return 'tablet';
      return 'mobile';
    } catch {
      return 'mobile';
    }
  }
  
  if (isBrowser() || isElectron()) {
    const width = window.innerWidth;
    if (width >= 1024) return 'desktop';
    if (width >= 768) return 'tablet';
    return 'mobile';
  }
  
  return 'mobile';
};

// Platform checkers
export const isIOS = (): boolean => getPlatform() === 'ios';
export const isAndroid = (): boolean => getPlatform() === 'android';
export const isWindows = (): boolean => getPlatform() === 'windows';
export const isWeb = (): boolean => getPlatform() === 'web';
export const isMobile = (): boolean => isIOS() || isAndroid();
export const isDesktop = (): boolean => isWindows() || isElectron();

// Check if touch device
export const isTouchDevice = (): boolean => {
  if (isReactNative) return true;
  if (isBrowser() || isElectron()) {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }
  return false;
};

// Get platform-specific styles
export const getPlatformStyles = () => {
  const platform = getPlatform();
  const deviceType = getDeviceType();
  
  return {
    // Safe area insets
    safeAreaTop: isIOS() ? (deviceType === 'mobile' ? 44 : 24) : 0,
    safeAreaBottom: isIOS() ? (deviceType === 'mobile' ? 34 : 20) : 0,
    
    // Status bar height
    statusBarHeight: isIOS() ? (deviceType === 'mobile' ? 44 : 24) : (isAndroid() ? 24 : 0),
    
    // Navigation bar height
    navigationBarHeight: isMobile() ? 56 : 64,
    
    // Tab bar height
    tabBarHeight: isMobile() ? 80 : 60,
    
    // Default padding
    defaultPadding: isMobile() ? 16 : 24,
    
    // Font scaling
    fontScale: isMobile() ? 1 : 1.1,
    
    // Touch target size
    touchTargetSize: isTouchDevice() ? 44 : 32,
  };
};

// Platform-specific feature detection
export const supportsNotifications = (): boolean => {
  if (isReactNative) return true;
  if (isBrowser() || isElectron()) {
    return 'Notification' in window;
  }
  return false;
};

export const supportsWebSockets = (): boolean => {
  return typeof WebSocket !== 'undefined';
};

export const supportsLocalStorage = (): boolean => {
  if (isReactNative) {
    try {
      const AsyncStorage = require('@react-native-async-storage/async-storage');
      return !!AsyncStorage;
    } catch {
      return false;
    }
  }
  try {
    const test = '__storage_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
};

export const supportsIndexedDB = (): boolean => {
  return typeof indexedDB !== 'undefined';
};

// Platform info object
export const getPlatformInfo = () => ({
  platform: getPlatform(),
  deviceType: getDeviceType(),
  isReactNative,
  isElectron: isElectron(),
  isBrowser: isBrowser(),
  isTouchDevice: isTouchDevice(),
  supportsNotifications: supportsNotifications(),
  supportsWebSockets: supportsWebSockets(),
  supportsLocalStorage: supportsLocalStorage(),
  supportsIndexedDB: supportsIndexedDB(),
  styles: getPlatformStyles(),
});

export default {
  getPlatform,
  getDeviceType,
  isIOS,
  isAndroid,
  isWindows,
  isWeb,
  isMobile,
  isDesktop,
  isTouchDevice,
  getPlatformStyles,
  supportsNotifications,
  supportsWebSockets,
  supportsLocalStorage,
  supportsIndexedDB,
  getPlatformInfo,
};
