/**
 * Mrki Mobile App
 * React Native entry point for iOS and Android
 */

import React, { useEffect } from 'react';
import { StatusBar, useColorScheme } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Import screens from shared src
import HomeScreen from '../../src/screens/HomeScreen';
import AgentsScreen from '../../src/screens/AgentsScreen';
import TasksScreen from '../../src/screens/TasksScreen';
import SettingsScreen from '../../src/screens/SettingsScreen';

// Import services
import { createNotificationService } from '../../shared/services/notifications';
import { createSyncService } from '../../shared/services/sync';
import { createWebSocketClient } from '../../shared/services/websocket';

// API Configuration
const API_URL = 'https://unrequisitioned-caroll-glamorously.ngrok-free.app';
const WS_URL = 'wss://unrequisitioned-caroll-glamorously.ngrok-free.app';

// Navigation types
export type RootStackParamList = {
  Main: undefined;
  AgentDetail: { agentId: string };
  TaskDetail: { taskId: string };
};

export type MainTabParamList = {
  Home: undefined;
  Agents: undefined;
  Tasks: undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

// Main Tab Navigator
const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Agents':
              iconName = focused ? 'robot' : 'robot-outline';
              break;
            case 'Tasks':
              iconName = focused ? 'check-circle' : 'check-circle-outline';
              break;
            case 'Settings':
              iconName = focused ? 'cog' : 'cog-outline';
              break;
            default:
              iconName = 'help-circle';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Agents" component={AgentsScreen} />
      <Tab.Screen name="Tasks" component={TasksScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
};

// Initialize services
const initializeServices = async () => {
  // Initialize notifications
  const notifications = createNotificationService({
    requestPermissionsOnInit: true,
  });
  await notifications.initialize();

  // Initialize WebSocket
  const wsClient = createWebSocketClient({
    url: WS_URL,
    autoConnect: true,
    heartbeatInterval: 30000,
  });

  // Initialize sync service
  const syncService = createSyncService({
    apiClient: {
      get: async (path: string, options?: any) => {
        const response = await fetch(`${API_URL}${path}`, options);
        return response.json();
      },
      post: async (path: string, data: any) => {
        const response = await fetch(`${API_URL}${path}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        return response.json();
      },
      put: async (path: string, data: any) => {
        const response = await fetch(`${API_URL}${path}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        return response.json();
      },
      delete: async (path: string) => {
        const response = await fetch(`${API_URL}${path}`, {
          method: 'DELETE',
        });
        return response.json();
      },
    },
    syncInterval: 30000,
  });

  await syncService.initialize();

  // Listen for task completion notifications
  wsClient.on('message:task_complete', async (payload) => {
    const { showTaskCompletionNotification } = await import('../../shared/services/notifications');
    await showTaskCompletionNotification(notifications, payload.title, payload.taskId, true);
  });

  wsClient.on('message:task_fail', async (payload) => {
    const { showTaskCompletionNotification } = await import('../../shared/services/notifications');
    await showTaskCompletionNotification(notifications, payload.title, payload.taskId, false);
  });
};

// Main App Component
const App: React.FC = () => {
  const colorScheme = useColorScheme();
  const isDarkMode = colorScheme === 'dark';

  useEffect(() => {
    initializeServices();
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar
        barStyle={isDarkMode ? 'light-content' : 'dark-content'}
        backgroundColor={isDarkMode ? '#000000' : '#FFFFFF'}
      />
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
          }}
        >
          <Stack.Screen name="Main" component={MainTabNavigator} />
          {/* Add more screens here */}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

export default App;
