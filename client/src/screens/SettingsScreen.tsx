/**
 * Settings Screen
 * User preferences and app configuration
 */

import React, { useState, useCallback } from 'react';
import { usePlatform, useNetworkStatus } from '@shared/hooks/usePlatform';
import { useSync } from '@shared/hooks/useSync';
import AdaptiveView from '@components/AdaptiveView';
import AdaptiveText from '@components/AdaptiveText';
import AdaptiveButton from '@components/AdaptiveButton';

const API_URL = process.env.API_URL || 'http://localhost:3000';

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

interface SettingItemProps {
  title: string;
  description?: string;
  value?: React.ReactNode;
  onPress?: () => void;
  danger?: boolean;
}

const SettingItem: React.FC<SettingItemProps> = ({ title, description, value, onPress, danger }) => {
  const containerStyle = {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  };

  if (isReactNative) {
    const { View, TouchableOpacity, Switch } = require('react-native');

    const content = (
      <View style={containerStyle}>
        <View style={{ flex: 1 }}>
          <AdaptiveText variant="body" style={{ color: danger ? '#FF3B30' : '#000000' }}>
            {title}
          </AdaptiveText>
          {description && (
            <AdaptiveText variant="caption" style={{ color: '#666', marginTop: 2 }}>
              {description}
            </AdaptiveText>
          )}
        </View>
        {value}
      </View>
    );

    if (onPress) {
      return (
        <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
          {content}
        </TouchableOpacity>
      );
    }

    return content;
  }

  // Web implementation
  const content = (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '12px 16px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #E5E5EA',
    }}>
      <div style={{ flex: 1 }}>
        <AdaptiveText variant="body" style={{ color: danger ? '#FF3B30' : '#000000' }}>
          {title}
        </AdaptiveText>
        {description && (
          <AdaptiveText variant="caption" style={{ color: '#666', marginTop: 2 }}>
            {description}
          </AdaptiveText>
        )}
      </div>
      {value}
    </div>
  );

  if (onPress) {
    return (
      <div
        onClick={onPress}
        style={{ cursor: 'pointer' }}
        onMouseEnter={(e) => {
          (e.currentTarget.firstChild as HTMLElement).style.backgroundColor = '#F2F2F7';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget.firstChild as HTMLElement).style.backgroundColor = '#FFFFFF';
        }}
      >
        {content}
      </div>
    );
  }

  return content;
};

export const SettingsScreen: React.FC = () => {
  const platform = usePlatform();
  const network = useNetworkStatus();
  const { syncState, sync, forceSync, reset } = useSync({ apiClient: null });
  
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [analytics, setAnalytics] = useState(true);
  const [syncInterval, setSyncInterval] = useState(30);

  const handleSyncNow = useCallback(async () => {
    await forceSync();
  }, [forceSync]);

  const handleClearCache = useCallback(() => {
    if (isReactNative) {
      const { Alert } = require('react-native');
      Alert.alert(
        'Clear Cache',
        'This will clear all local data. Are you sure?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Clear', 
            style: 'destructive',
            onPress: async () => {
              await reset();
            }
          },
        ]
      );
    } else {
      if (window.confirm('This will clear all local data. Are you sure?')) {
        reset();
      }
    }
  }, [reset]);

  const handleLogout = useCallback(() => {
    if (isReactNative) {
      const { Alert } = require('react-native');
      Alert.alert(
        'Logout',
        'Are you sure you want to logout?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Logout', 
            style: 'destructive',
            onPress: () => {
              // Handle logout
              console.log('Logout');
            }
          },
        ]
      );
    } else {
      if (window.confirm('Are you sure you want to logout?')) {
        // Handle logout
        console.log('Logout');
      }
    }
  }, []);

  const formatLastSync = (date: string | null): string => {
    if (!date) return 'Never';
    const syncDate = new Date(date);
    const now = new Date();
    const diff = now.getTime() - syncDate.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return syncDate.toLocaleDateString();
  };

  if (isReactNative) {
    const { View, ScrollView, Switch } = require('react-native');

    return (
      <View style={{ flex: 1, backgroundColor: '#F2F2F7' }}>
        {/* Header */}
        <View style={{ padding: 16, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#E5E5EA' }}>
          <AdaptiveText variant="h1">Settings</AdaptiveText>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          {/* Account Section */}
          <View style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginHorizontal: 16, marginBottom: 8 }}>
              Account
            </AdaptiveText>
            <SettingItem
              title="Email"
              description="user@example.com"
              value={<AdaptiveText variant="body" style={{ color: '#666' }}>user@example.com</AdaptiveText>}
            />
            <SettingItem
              title="Subscription"
              description="Pro Plan"
              value={<AdaptiveButton variant="outline" size="small">Manage</AdaptiveButton>}
              onPress={() => {}}
            />
          </View>

          {/* Sync Section */}
          <View style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginHorizontal: 16, marginBottom: 8 }}>
              Sync & Storage
            </AdaptiveText>
            <SettingItem
              title="Last Sync"
              description={syncState.isSyncing ? 'Syncing...' : formatLastSync(syncState.lastSyncAt)}
              value={
                <AdaptiveButton
                  variant="primary"
                  size="small"
                  onPress={handleSyncNow}
                  loading={syncState.isSyncing}
                >
                  Sync Now
                </AdaptiveButton>
              }
            />
            <SettingItem
              title="Pending Changes"
              description={`${syncState.pendingChanges.length} items waiting to sync`}
              value={<AdaptiveText variant="body">{syncState.pendingChanges.length}</AdaptiveText>}
            />
            <SettingItem
              title="Clear Cache"
              description="Remove all local data"
              onPress={handleClearCache}
              danger
            />
          </View>

          {/* Preferences Section */}
          <View style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginHorizontal: 16, marginBottom: 8 }}>
              Preferences
            </AdaptiveText>
            <SettingItem
              title="Notifications"
              description="Receive push notifications"
              value={
                <Switch
                  value={notifications}
                  onValueChange={setNotifications}
                  trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                />
              }
            />
            <SettingItem
              title="Dark Mode"
              description="Use dark theme"
              value={
                <Switch
                  value={darkMode}
                  onValueChange={setDarkMode}
                  trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                />
              }
            />
            <SettingItem
              title="Analytics"
              description="Help improve the app"
              value={
                <Switch
                  value={analytics}
                  onValueChange={setAnalytics}
                  trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                />
              }
            />
          </View>

          {/* About Section */}
          <View style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginHorizontal: 16, marginBottom: 8 }}>
              About
            </AdaptiveText>
            <SettingItem
              title="Version"
              description="1.0.0"
            />
            <SettingItem
              title="Platform"
              description={platform.platform}
            />
            <SettingItem
              title="API Endpoint"
              description={API_URL}
            />
          </View>

          {/* Logout */}
          <View style={{ marginTop: 20, marginBottom: 40 }}>
            <SettingItem
              title="Logout"
              onPress={handleLogout}
              danger
            />
          </View>
        </ScrollView>
      </View>
    );
  }

  // Web implementation
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#F2F2F7' }}>
      {/* Header */}
      <div style={{ padding: 16, backgroundColor: '#FFFFFF', borderBottom: '1px solid #E5E5EA' }}>
        <AdaptiveText variant="h1">Settings</AdaptiveText>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {/* Account Section */}
          <div style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginBottom: 8 }}>Account</AdaptiveText>
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden' }}>
              <SettingItem title="Email" description="user@example.com" />
              <SettingItem
                title="Subscription"
                description="Pro Plan"
                value={<AdaptiveButton variant="outline" size="small">Manage</AdaptiveButton>}
                onPress={() => {}}
              />
            </div>
          </div>

          {/* Sync Section */}
          <div style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginBottom: 8 }}>Sync & Storage</AdaptiveText>
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden' }}>
              <SettingItem
                title="Last Sync"
                description={syncState.isSyncing ? 'Syncing...' : formatLastSync(syncState.lastSyncAt)}
                value={
                  <AdaptiveButton
                    variant="primary"
                    size="small"
                    onPress={handleSyncNow}
                    loading={syncState.isSyncing}
                  >
                    Sync Now
                  </AdaptiveButton>
                }
              />
              <SettingItem
                title="Pending Changes"
                description={`${syncState.pendingChanges.length} items waiting to sync`}
              />
              <SettingItem
                title="Clear Cache"
                description="Remove all local data"
                onPress={handleClearCache}
                danger
              />
            </div>
          </div>

          {/* Preferences Section */}
          <div style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginBottom: 8 }}>Preferences</AdaptiveText>
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden' }}>
              <SettingItem
                title="Notifications"
                description="Receive push notifications"
                value={
                  <label style={{ position: 'relative', display: 'inline-block', width: 50, height: 26 }}>
                    <input
                      type="checkbox"
                      checked={notifications}
                      onChange={(e) => setNotifications(e.target.checked)}
                      style={{ opacity: 0, width: 0, height: 0 }}
                    />
                    <span style={{
                      position: 'absolute',
                      cursor: 'pointer',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      backgroundColor: notifications ? '#34C759' : '#E5E5EA',
                      transition: '0.3s',
                      borderRadius: 26,
                    }}>
                      <span style={{
                        position: 'absolute',
                        content: '""',
                        height: 22,
                        width: 22,
                        left: notifications ? 26 : 2,
                        bottom: 2,
                        backgroundColor: 'white',
                        transition: '0.3s',
                        borderRadius: '50%',
                      }} />
                    </span>
                  </label>
                }
              />
              <SettingItem
                title="Dark Mode"
                description="Use dark theme"
                value={
                  <label style={{ position: 'relative', display: 'inline-block', width: 50, height: 26 }}>
                    <input
                      type="checkbox"
                      checked={darkMode}
                      onChange={(e) => setDarkMode(e.target.checked)}
                      style={{ opacity: 0, width: 0, height: 0 }}
                    />
                    <span style={{
                      position: 'absolute',
                      cursor: 'pointer',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      backgroundColor: darkMode ? '#34C759' : '#E5E5EA',
                      transition: '0.3s',
                      borderRadius: 26,
                    }}>
                      <span style={{
                        position: 'absolute',
                        content: '""',
                        height: 22,
                        width: 22,
                        left: darkMode ? 26 : 2,
                        bottom: 2,
                        backgroundColor: 'white',
                        transition: '0.3s',
                        borderRadius: '50%',
                      }} />
                    </span>
                  </label>
                }
              />
            </div>
          </div>

          {/* About Section */}
          <div style={{ marginTop: 20 }}>
            <AdaptiveText variant="label" style={{ marginBottom: 8 }}>About</AdaptiveText>
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden' }}>
              <SettingItem title="Version" description="1.0.0" />
              <SettingItem title="Platform" description={platform.platform} />
              <SettingItem title="API Endpoint" description={API_URL} />
            </div>
          </div>

          {/* Logout */}
          <div style={{ marginTop: 20, marginBottom: 40 }}>
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden' }}>
              <SettingItem title="Logout" onPress={handleLogout} danger />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsScreen;
