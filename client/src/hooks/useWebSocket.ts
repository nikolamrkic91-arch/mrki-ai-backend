/**
 * Mrki - WebSocket Hook
 * Universal WebSocket client for real-time communication
 * Works on: iOS, Android, Windows (Electron)
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import { io, Socket } from 'socket.io-client';

interface WebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
  onMessage?: (data: any) => void;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: any | null;
  error: Error | null;
}

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
    onConnect,
    onDisconnect,
    onError,
    onMessage,
  } = options;

  const socketRef = useRef<Socket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    error: null,
  });

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      console.log('[WebSocket] Already connected');
      return;
    }

    setState((prev) => ({ ...prev, isConnecting: true, error: null }));

    try {
      // Socket.io client with platform info
      socketRef.current = io(url, {
        transports: ['websocket', 'polling'],
        reconnection: false, // We handle reconnection manually
        query: {
          platform: Platform.OS,
          version: '1.0.0',
        },
        timeout: 10000,
      });

      const socket = socketRef.current;

      socket.on('connect', () => {
        console.log('[WebSocket] Connected:', socket.id);
        reconnectCountRef.current = 0;
        setState((prev) => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
        }));
        onConnect?.();
      });

      socket.on('disconnect', (reason) => {
        console.log('[WebSocket] Disconnected:', reason);
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));
        onDisconnect?.(reason);

        // Auto-reconnect on certain disconnect reasons
        if (reason === 'io server disconnect' || reason === 'transport close') {
          attemptReconnect();
        }
      });

      socket.on('connect_error', (error) => {
        console.error('[WebSocket] Connection error:', error.message);
        setState((prev) => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error,
        }));
        onError?.(error);
        attemptReconnect();
      });

      socket.on('message', (data) => {
        console.log('[WebSocket] Message received:', data);
        setState((prev) => ({ ...prev, lastMessage: data }));
        onMessage?.(data);
      });

      // Handle custom events from Mrki server
      socket.on('mrki:event', (data) => {
        console.log('[WebSocket] Mrki event:', data);
        setState((prev) => ({ ...prev, lastMessage: data }));
        onMessage?.(data);
      });

    } catch (error) {
      console.error('[WebSocket] Setup error:', error);
      setState((prev) => ({
        ...prev,
        isConnecting: false,
        error: error as Error,
      }));
      onError?.(error as Error);
    }
  }, [url, onConnect, onDisconnect, onError, onMessage]);

  const disconnect = useCallback(() => {
    // Clear any pending reconnect
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    reconnectCountRef.current = 0;
    setState({
      isConnected: false,
      isConnecting: false,
      lastMessage: null,
      error: null,
    });
  }, []);

  const attemptReconnect = useCallback(() => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      console.log('[WebSocket] Max reconnection attempts reached');
      return;
    }

    reconnectCountRef.current++;
    console.log(`[WebSocket] Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`);

    reconnectTimerRef.current = setTimeout(() => {
      connect();
    }, reconnectDelay);
  }, [connect, reconnectAttempts, reconnectDelay]);

  const send = useCallback((data: any) => {
    if (!socketRef.current?.connected) {
      console.warn('[WebSocket] Cannot send - not connected');
      return false;
    }

    try {
      socketRef.current.emit('message', data);
      return true;
    } catch (error) {
      console.error('[WebSocket] Send error:', error);
      return false;
    }
  }, []);

  const emit = useCallback((event: string, data: any) => {
    if (!socketRef.current?.connected) {
      console.warn('[WebSocket] Cannot emit - not connected');
      return false;
    }

    try {
      socketRef.current.emit(event, data);
      return true;
    } catch (error) {
      console.error('[WebSocket] Emit error:', error);
      return false;
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    send,
    emit,
    socket: socketRef.current,
  };
}

export default useWebSocket;
