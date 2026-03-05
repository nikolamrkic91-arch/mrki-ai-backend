/**
 * Mrki - Main App Component (Shared)
 * Works on: iOS, Android, Windows (Electron)
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Platform,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { useWebSocket } from './hooks/useWebSocket';

// Platform detection
const isMobile = Platform.OS === 'ios' || Platform.OS === 'android';
const isDesktop = Platform.OS === 'web' && typeof window !== 'undefined' && (window as any).electron;

interface Message {
  id: string;
  type: 'info' | 'success' | 'error';
  content: string;
  timestamp: number;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  const { connect, disconnect, send, isConnected, lastMessage } = useWebSocket({
    url: 'ws://localhost:3000',
    autoConnect: true,
    onConnect: () => {
      setConnectionStatus('connected');
      addMessage('info', 'Connected to Mrki server');
    },
    onDisconnect: () => {
      setConnectionStatus('disconnected');
      addMessage('info', 'Disconnected from server');
    },
    onError: (error) => {
      setConnectionStatus('disconnected');
      addMessage('error', `Connection error: ${error.message}`);
    },
  });

  const addMessage = (type: Message['type'], content: string) => {
    const newMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      type,
      content,
      timestamp: Date.now(),
    };
    setMessages((prev) => [newMessage, ...prev].slice(0, 50));
  };

  useEffect(() => {
    if (lastMessage) {
      addMessage('info', `Received: ${JSON.stringify(lastMessage)}`);
    }
  }, [lastMessage]);

  const handleSendTest = () => {
    send({
      type: 'ping',
      timestamp: Date.now(),
      platform: Platform.OS,
    });
    addMessage('success', 'Sent ping to server');
  };

  const handleReconnect = () => {
    setConnectionStatus('connecting');
    connect();
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return '#4CAF50';
      case 'connecting': return '#FFC107';
      default: return '#F44336';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Mrki</Text>
        <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
        <Text style={styles.statusText}>
          {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
        </Text>
      </View>

      {/* Platform Info */}
      <View style={styles.platformInfo}>
        <Text style={styles.platformText}>
          Platform: {Platform.OS} {isDesktop && '(Electron)'}
        </Text>
      </View>

      {/* Action Buttons */}
      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleSendTest}
          disabled={!isConnected}
        >
          <Text style={styles.buttonText}>Send Ping</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={handleReconnect}
        >
          <Text style={styles.buttonText}>Reconnect</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.dangerButton]}
          onPress={disconnect}
        >
          <Text style={styles.buttonText}>Disconnect</Text>
        </TouchableOpacity>
      </View>

      {/* Messages */}
      <ScrollView style={styles.messageContainer}>
        <Text style={styles.sectionTitle}>Messages</Text>
        {messages.length === 0 ? (
          <Text style={styles.emptyText}>No messages yet</Text>
        ) : (
          messages.map((msg) => (
            <View key={msg.id} style={styles.messageItem}>
              <View style={[styles.messageDot, { 
                backgroundColor: 
                  msg.type === 'error' ? '#F44336' : 
                  msg.type === 'success' ? '#4CAF50' : '#2196F3' 
              }]} />
              <View style={styles.messageContent}>
                <Text style={styles.messageText}>{msg.content}</Text>
                <Text style={styles.messageTime}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
  },
  platformInfo: {
    padding: 12,
    backgroundColor: '#e3f2fd',
    alignItems: 'center',
  },
  platformText: {
    fontSize: 14,
    color: '#1976d2',
    fontWeight: '500',
  },
  buttonRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
    flexWrap: 'wrap',
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    minWidth: 100,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#2196F3',
  },
  secondaryButton: {
    backgroundColor: '#757575',
  },
  dangerButton: {
    backgroundColor: '#F44336',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  messageContainer: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    marginTop: 20,
  },
  messageItem: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  messageDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 4,
    marginRight: 10,
  },
  messageContent: {
    flex: 1,
  },
  messageText: {
    fontSize: 14,
    color: '#333',
  },
  messageTime: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
});
