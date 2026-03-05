/**
 * Platform Hook
 * React hook for platform detection and responsive behavior
 */

import { useState, useEffect, useCallback } from 'react';
import { Platform, DeviceType } from '../types';
import * as platformUtils from '../utils/platform';

interface PlatformInfo {
  platform: Platform;
  deviceType: DeviceType;
  isReactNative: boolean;
  isElectron: boolean;
  isBrowser: boolean;
  isIOS: boolean;
  isAndroid: boolean;
  isWindows: boolean;
  isWeb: boolean;
  isMobile: boolean;
  isDesktop: boolean;
  isTouchDevice: boolean;
  supportsNotifications: boolean;
  supportsWebSockets: boolean;
  supportsLocalStorage: boolean;
  styles: ReturnType<typeof platformUtils.getPlatformStyles>;
}

interface WindowDimensions {
  width: number;
  height: number;
}

export const usePlatform = (): PlatformInfo & { dimensions: WindowDimensions } => {
  const [dimensions, setDimensions] = useState<WindowDimensions>({
    width: 0,
    height: 0,
  });

  useEffect(() => {
    // Get initial dimensions
    const updateDimensions = () => {
      if (typeof window !== 'undefined') {
        setDimensions({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }
    };

    updateDimensions();

    // Listen for dimension changes
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, []);

  return {
    platform: platformUtils.getPlatform(),
    deviceType: platformUtils.getDeviceType(),
    isReactNative: typeof navigator !== 'undefined' && navigator.product === 'ReactNative',
    isElectron: platformUtils.isDesktop(),
    isBrowser: typeof window !== 'undefined' && !platformUtils.isMobile(),
    isIOS: platformUtils.isIOS(),
    isAndroid: platformUtils.isAndroid(),
    isWindows: platformUtils.isWindows(),
    isWeb: platformUtils.isWeb(),
    isMobile: platformUtils.isMobile(),
    isDesktop: platformUtils.isDesktop(),
    isTouchDevice: platformUtils.isTouchDevice(),
    supportsNotifications: platformUtils.supportsNotifications(),
    supportsWebSockets: platformUtils.supportsWebSockets(),
    supportsLocalStorage: platformUtils.supportsLocalStorage(),
    styles: platformUtils.getPlatformStyles(),
    dimensions,
  };
};

// Hook for responsive breakpoints
export const useBreakpoint = () => {
  const { width } = useWindowDimensions();

  return {
    isXs: width < 576,
    isSm: width >= 576 && width < 768,
    isMd: width >= 768 && width < 992,
    isLg: width >= 992 && width < 1200,
    isXl: width >= 1200,
    isMobile: width < 768,
    isTablet: width >= 768 && width < 992,
    isDesktop: width >= 992,
  };
};

// Hook for window dimensions (works in both RN and web)
export const useWindowDimensions = (): WindowDimensions => {
  const [dimensions, setDimensions] = useState<WindowDimensions>({
    width: 0,
    height: 0,
  });

  useEffect(() => {
    const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

    if (isReactNative) {
      // Use React Native Dimensions
      try {
        const { Dimensions } = require('react-native');
        const updateDimensions = () => {
          const { width, height } = Dimensions.get('window');
          setDimensions({ width, height });
        };

        updateDimensions();
        const subscription = Dimensions.addEventListener('change', updateDimensions);
        return () => subscription?.remove?.();
      } catch {
        // Fallback
      }
    } else if (typeof window !== 'undefined') {
      // Use web window
      const updateDimensions = () => {
        setDimensions({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      };

      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, []);

  return dimensions;
};

// Hook for safe area insets
export const useSafeAreaInsets = () => {
  const [insets, setInsets] = useState({
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
  });

  useEffect(() => {
    const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

    if (isReactNative) {
      try {
        const { useSafeAreaInsets } = require('react-native-safe-area-context');
        // This would be used directly in component, here we just set defaults
        const styles = platformUtils.getPlatformStyles();
        setInsets({
          top: styles.safeAreaTop,
          bottom: styles.safeAreaBottom,
          left: 0,
          right: 0,
        });
      } catch {
        // Fallback
      }
    }
  }, []);

  return insets;
};

// Hook for keyboard visibility (mobile)
export const useKeyboard = () => {
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

    if (isReactNative) {
      try {
        const { Keyboard } = require('react-native');
        
        const showListener = Keyboard.addListener('keyboardDidShow', (event: any) => {
          setKeyboardVisible(true);
          setKeyboardHeight(event.endCoordinates.height);
        });
        
        const hideListener = Keyboard.addListener('keyboardDidHide', () => {
          setKeyboardVisible(false);
          setKeyboardHeight(0);
        });

        return () => {
          showListener.remove();
          hideListener.remove();
        };
      } catch {
        // Fallback
      }
    }
  }, []);

  return { keyboardVisible, keyboardHeight };
};

// Hook for network status
export const useNetworkStatus = () => {
  const [isConnected, setIsConnected] = useState(true);
  const [connectionType, setConnectionType] = useState<string>('unknown');

  useEffect(() => {
    const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

    if (isReactNative) {
      try {
        const NetInfo = require('@react-native-community/netinfo').default;
        
        const unsubscribe = NetInfo.addEventListener((state: any) => {
          setIsConnected(state.isConnected ?? false);
          setConnectionType(state.type ?? 'unknown');
        });

        return () => unsubscribe();
      } catch {
        // Fallback
      }
    } else if (typeof window !== 'undefined') {
      const handleOnline = () => setIsConnected(true);
      const handleOffline = () => setIsConnected(false);

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);
      setIsConnected(navigator.onLine);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  return { isConnected, connectionType };
};

export default usePlatform;
