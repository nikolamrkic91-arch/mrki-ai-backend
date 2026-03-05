/**
 * WebSocket Hook
 * React hook for WebSocket connection management
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketClient } from '../services/websocket';
import { WebSocketMessage, ConnectionState } from '../types';

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  autoReconnect?: boolean;
  reconnectConfig?: {
    initialDelay?: number;
    maxDelay?: number;
    maxRetries?: number;
  };
  heartbeatInterval?: number;
  authToken?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

interface UseWebSocketReturn {
  client: WebSocketClient | null;
  isConnected: boolean;
  isConnecting: boolean;
  connectionState: ConnectionState;
  send: (type: string, payload: any) => boolean;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  connect: () => void;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
}

export const useWebSocket = (options: UseWebSocketOptions): UseWebSocketReturn => {
  const clientRef = useRef<WebSocketClient | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    lastConnectedAt: null,
    reconnectAttempts: 0,
    latency: 0,
  });
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  // Initialize WebSocket client
  useEffect(() => {
    const client = new WebSocketClient({
      url: options.url,
      autoConnect: false,
      reconnectConfig: options.reconnectConfig,
      heartbeatInterval: options.heartbeatInterval,
      authToken: options.authToken,
    });

    // Event handlers
    client.on('connected', () => {
      setConnectionState(client.getState());
      options.onConnect?.();
    });

    client.on('disconnected', () => {
      setConnectionState(client.getState());
      options.onDisconnect?.();
    });

    client.on('message', (message: WebSocketMessage) => {
      setLastMessage(message);
      options.onMessage?.(message);
    });

    client.on('error', (error: Error) => {
      options.onError?.(error);
    });

    client.on('connecting', () => {
      setConnectionState(client.getState());
    });

    client.on('reconnect:attempt', () => {
      setConnectionState(client.getState());
    });

    client.on('heartbeat', () => {
      setConnectionState(client.getState());
    });

    clientRef.current = client;

    // Auto connect if enabled
    if (options.autoConnect !== false) {
      client.connect();
    }

    return () => {
      client.disconnect();
      client.removeAllListeners();
    };
  }, [options.url]);

  // Update auth token when it changes
  useEffect(() => {
    if (clientRef.current && options.authToken) {
      clientRef.current.setAuthToken(options.authToken);
    }
  }, [options.authToken]);

  const send = useCallback((type: string, payload: any): boolean => {
    if (clientRef.current) {
      return clientRef.current.send(type as any, payload);
    }
    return false;
  }, []);

  const subscribe = useCallback((channel: string): void => {
    clientRef.current?.subscribe(channel);
  }, []);

  const unsubscribe = useCallback((channel: string): void => {
    clientRef.current?.unsubscribe(channel);
  }, []);

  const connect = useCallback((): void => {
    clientRef.current?.connect();
  }, []);

  const disconnect = useCallback((): void => {
    clientRef.current?.disconnect();
  }, []);

  return {
    client: clientRef.current,
    isConnected: connectionState.isConnected,
    isConnecting: connectionState.isConnecting,
    connectionState,
    send,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
    lastMessage,
  };
};

// Hook for specific message types
export const useWebSocketMessage = <T = any>(
  client: WebSocketClient | null,
  messageType: string
): T | null => {
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    if (!client) return;

    const handler = (payload: T) => {
      setData(payload);
    };

    client.on(`message:${messageType}`, handler);

    return () => {
      client.off(`message:${messageType}`, handler);
    };
  }, [client, messageType]);

  return data;
};

// Hook for agent status updates
export const useAgentStatus = (client: WebSocketClient | null) => {
  return useWebSocketMessage(client, 'agent_status');
};

// Hook for task updates
export const useTaskUpdates = (client: WebSocketClient | null) => {
  return useWebSocketMessage(client, 'task_update');
};

// Hook for task completion
export const useTaskCompletion = (client: WebSocketClient | null) => {
  return useWebSocketMessage(client, 'task_complete');
};

export default useWebSocket;
