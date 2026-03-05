/**
 * WebSocket Client with Auto-Reconnection
 * Platform-agnostic WebSocket wrapper with robust connection management
 */

import EventEmitter from 'eventemitter3';
import { WebSocketMessage, MessageType, ConnectionState } from '../types';

// Reconnection configuration
const DEFAULT_RECONNECT_CONFIG = {
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  maxRetries: 10,
  randomizationFactor: 0.5,
};

interface ReconnectConfig {
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  maxRetries: number;
  randomizationFactor: number;
}

interface WebSocketClientOptions {
  url: string;
  reconnectConfig?: Partial<ReconnectConfig>;
  heartbeatInterval?: number;
  heartbeatTimeout?: number;
  autoConnect?: boolean;
  authToken?: string;
}

export class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectConfig: ReconnectConfig;
  private heartbeatInterval: number;
  private heartbeatTimeout: number;
  private authToken?: string;
  
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private heartbeatTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  
  private state: ConnectionState = {
    isConnected: false,
    isConnecting: false,
    lastConnectedAt: null,
    reconnectAttempts: 0,
    latency: 0,
  };
  
  private messageQueue: WebSocketMessage[] = [];
  private subscriptions: Set<string> = new Set();
  private pingSentAt: number = 0;

  constructor(options: WebSocketClientOptions) {
    super();
    
    this.url = options.url;
    this.reconnectConfig = { ...DEFAULT_RECONNECT_CONFIG, ...options.reconnectConfig };
    this.heartbeatInterval = options.heartbeatInterval || 30000;
    this.heartbeatTimeout = options.heartbeatTimeout || 10000;
    this.authToken = options.authToken;

    if (options.autoConnect !== false) {
      this.connect();
    }
  }

  // Get current connection state
  getState(): ConnectionState {
    return { ...this.state };
  }

  // Check if connected
  isConnected(): boolean {
    return this.state.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  // Connect to WebSocket server
  connect(): void {
    if (this.state.isConnecting || this.isConnected()) {
      return;
    }

    this.state.isConnecting = true;
    this.emit('connecting');

    try {
      // Add auth token to URL if provided
      let connectionUrl = this.url;
      if (this.authToken) {
        const separator = this.url.includes('?') ? '&' : '?';
        connectionUrl += `${separator}token=${encodeURIComponent(this.authToken)}`;
      }

      this.ws = new WebSocket(connectionUrl);
      this.setupEventHandlers();
    } catch (error) {
      this.handleError(error as Error);
    }
  }

  // Disconnect from server
  disconnect(): void {
    this.clearTimers();
    
    if (this.ws) {
      // Send close frame
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000, 'Client disconnect');
      }
      this.ws = null;
    }

    this.state.isConnected = false;
    this.state.isConnecting = false;
    this.state.reconnectAttempts = 0;
    
    this.emit('disconnected');
  }

  // Send message to server
  send(type: MessageType, payload: any): boolean {
    const message: WebSocketMessage = {
      type,
      payload,
      timestamp: Date.now(),
      id: this.generateMessageId(),
    };

    if (this.isConnected()) {
      try {
        this.ws!.send(JSON.stringify(message));
        this.emit('message:sent', message);
        return true;
      } catch (error) {
        this.handleError(error as Error);
      }
    }

    // Queue message if not connected
    this.messageQueue.push(message);
    this.emit('message:queued', message);
    return false;
  }

  // Subscribe to a channel/topic
  subscribe(channel: string): void {
    this.subscriptions.add(channel);
    if (this.isConnected()) {
      this.send('subscribe', { channel });
    }
  }

  // Unsubscribe from a channel/topic
  unsubscribe(channel: string): void {
    this.subscriptions.delete(channel);
    if (this.isConnected()) {
      this.send('unsubscribe', { channel });
    }
  }

  // Update auth token
  setAuthToken(token: string): void {
    this.authToken = token;
    // Reconnect with new token if already connected
    if (this.isConnected()) {
      this.disconnect();
      this.connect();
    }
  }

  // Get pending message queue
  getMessageQueue(): WebSocketMessage[] {
    return [...this.messageQueue];
  }

  // Clear message queue
  clearMessageQueue(): void {
    this.messageQueue = [];
  }

  // Setup WebSocket event handlers
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.handleOpen();
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(event.data);
    };

    this.ws.onclose = (event) => {
      this.handleClose(event);
    };

    this.ws.onerror = (error) => {
      this.handleError(error as any);
    };
  }

  // Handle connection open
  private handleOpen(): void {
    this.state.isConnected = true;
    this.state.isConnecting = false;
    this.state.lastConnectedAt = new Date().toISOString();
    this.state.reconnectAttempts = 0;

    this.emit('connected');

    // Start heartbeat
    this.startHeartbeat();

    // Resubscribe to channels
    this.subscriptions.forEach(channel => {
      this.send('subscribe', { channel });
    });

    // Send queued messages
    this.flushMessageQueue();

    // Authenticate if token available
    if (this.authToken) {
      this.send('auth', { token: this.authToken });
    }
  }

  // Handle incoming message
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      
      // Handle ping/pong
      if (message.type === 'ping') {
        this.send('pong', {});
        return;
      }
      
      if (message.type === 'pong') {
        this.handlePong();
        return;
      }

      this.emit('message', message);
      this.emit(`message:${message.type}`, message.payload);
    } catch (error) {
      this.emit('message:raw', data);
    }
  }

  // Handle connection close
  private handleClose(event: CloseEvent): void {
    this.state.isConnected = false;
    this.state.isConnecting = false;
    this.stopHeartbeat();

    this.emit('closed', event);

    // Attempt reconnection if not intentionally closed
    if (event.code !== 1000 && event.code !== 1001) {
      this.scheduleReconnect();
    }
  }

  // Handle error
  private handleError(error: Error | Event): void {
    this.state.isConnecting = false;
    this.emit('error', error);
  }

  // Schedule reconnection with exponential backoff
  private scheduleReconnect(): void {
    if (this.state.reconnectAttempts >= this.reconnectConfig.maxRetries) {
      this.emit('reconnect:failed');
      return;
    }

    const delay = this.calculateReconnectDelay();
    this.state.reconnectAttempts++;

    this.emit('reconnect:scheduled', { delay, attempt: this.state.reconnectAttempts });

    this.reconnectTimer = setTimeout(() => {
      this.emit('reconnect:attempt', this.state.reconnectAttempts);
      this.connect();
    }, delay);
  }

  // Calculate reconnect delay with exponential backoff and jitter
  private calculateReconnectDelay(): number {
    const { initialDelay, maxDelay, backoffMultiplier, randomizationFactor } = this.reconnectConfig;
    
    let delay = initialDelay * Math.pow(backoffMultiplier, this.state.reconnectAttempts);
    delay = Math.min(delay, maxDelay);
    
    // Add jitter to prevent thundering herd
    const jitter = delay * randomizationFactor * (Math.random() - 0.5);
    delay += jitter;
    
    return Math.max(delay, initialDelay);
  }

  // Start heartbeat
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      this.ping();
    }, this.heartbeatInterval);
  }

  // Stop heartbeat
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer);
      this.heartbeatTimeoutTimer = null;
    }
  }

  // Send ping
  private ping(): void {
    if (!this.isConnected()) return;
    
    this.pingSentAt = Date.now();
    this.send('ping', {});
    
    // Set timeout for pong response
    this.heartbeatTimeoutTimer = setTimeout(() => {
      this.emit('heartbeat:timeout');
      // Reconnect on heartbeat timeout
      this.disconnect();
      this.connect();
    }, this.heartbeatTimeout);
  }

  // Handle pong response
  private handlePong(): void {
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer);
      this.heartbeatTimeoutTimer = null;
    }
    
    this.state.latency = Date.now() - this.pingSentAt;
    this.emit('heartbeat', { latency: this.state.latency });
  }

  // Flush queued messages
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift();
      if (message) {
        try {
          this.ws!.send(JSON.stringify(message));
          this.emit('message:sent', message);
        } catch (error) {
          this.messageQueue.unshift(message);
          break;
        }
      }
    }
  }

  // Clear all timers
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
  }

  // Generate unique message ID
  private generateMessageId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Create singleton instance
let wsClient: WebSocketClient | null = null;

export const createWebSocketClient = (options: WebSocketClientOptions): WebSocketClient => {
  wsClient = new WebSocketClient(options);
  return wsClient;
};

export const getWebSocketClient = (): WebSocketClient | null => {
  return wsClient;
};

export default WebSocketClient;
