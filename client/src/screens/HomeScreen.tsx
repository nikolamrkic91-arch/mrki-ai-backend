/**
 * Home Screen
 * Main dashboard showing overview of agents and tasks
 */

import React, { useEffect, useState } from 'react';
import { Agent, Task } from '@shared/types';
import { usePlatform, useNetworkStatus } from '@shared/hooks/usePlatform';
import { useAgents, useTasks } from '@shared/hooks/useSync';
import { useWebSocket } from '@shared/hooks/useWebSocket';
import AdaptiveView from '@components/AdaptiveView';
import AdaptiveText from '@components/AdaptiveText';
import AdaptiveButton from '@components/AdaptiveButton';
import AgentCard from '@components/AgentCard';
import TaskList from '@components/TaskList';

const API_URL = process.env.API_URL || 'http://localhost:3000';
const WS_URL = process.env.WS_URL || 'ws://localhost:3001';

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

export const HomeScreen: React.FC = () => {
  const platform = usePlatform();
  const network = useNetworkStatus();
  const { entities: agents, refresh: refreshAgents } = useAgents();
  const { entities: tasks, refresh: refreshTasks } = useTasks();
  
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);

  // WebSocket connection for real-time updates
  const { isConnected, send } = useWebSocket({
    url: WS_URL,
    autoConnect: true,
    onMessage: (message) => {
      if (message.type === 'agent_status') {
        refreshAgents();
      } else if (message.type === 'task_update') {
        refreshTasks();
      }
    },
  });

  useEffect(() => {
    // Filter recent tasks (last 24 hours)
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const recent = tasks
      .filter(t => new Date(t.createdAt) > oneDayAgo)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, 10);
    setRecentTasks(recent);

    // Filter active agents
    const active = agents.filter(a => a.status === 'running');
    setActiveAgents(active);
  }, [agents, tasks]);

  const handleRunAgent = (agent: Agent) => {
    send('task_create', {
      agentId: agent.id,
      title: `Run ${agent.name}`,
      input: '',
    });
  };

  const handleViewAgent = (agent: Agent) => {
    // Navigate to agent detail
    console.log('View agent:', agent.id);
  };

  const containerStyle = {
    flex: 1,
    backgroundColor: '#F2F2F7',
  };

  const headerStyle = {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  };

  const sectionStyle = {
    marginTop: 16,
  };

  const sectionHeaderStyle = {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 8,
  };

  const statsContainerStyle = {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  };

  const statCardStyle = {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  };

  if (isReactNative) {
    const { ScrollView, View } = require('react-native');

    return (
      <View style={containerStyle}>
        {/* Header */}
        <View style={headerStyle}>
          <AdaptiveText variant="h1">Mrki</AdaptiveText>
          <AdaptiveText variant="caption" style={{ color: '#666' }}>
            {network.isConnected ? (isConnected ? 'Connected' : 'Connecting...') : 'Offline'}
          </AdaptiveText>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          {/* Stats */}
          <View style={statsContainerStyle}>
            <View style={statCardStyle}>
              <AdaptiveText variant="h2" style={{ color: '#007AFF' }}>
                {agents.length}
              </AdaptiveText>
              <AdaptiveText variant="caption">Agents</AdaptiveText>
            </View>
            <View style={statCardStyle}>
              <AdaptiveText variant="h2" style={{ color: '#34C759' }}>
                {activeAgents.length}
              </AdaptiveText>
              <AdaptiveText variant="caption">Active</AdaptiveText>
            </View>
            <View style={statCardStyle}>
              <AdaptiveText variant="h2" style={{ color: '#5856D6' }}>
                {recentTasks.length}
              </AdaptiveText>
              <AdaptiveText variant="caption">Tasks (24h)</AdaptiveText>
            </View>
          </View>

          {/* Active Agents */}
          {activeAgents.length > 0 && (
            <View style={sectionStyle}>
              <View style={sectionHeaderStyle}>
                <AdaptiveText variant="h3">Active Agents</AdaptiveText>
              </View>
              {activeAgents.map(agent => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  compact
                  onPress={handleViewAgent}
                />
              ))}
            </View>
          )}

          {/* Recent Tasks */}
          <View style={sectionStyle}>
            <View style={sectionHeaderStyle}>
              <AdaptiveText variant="h3">Recent Tasks</AdaptiveText>
              <AdaptiveButton variant="ghost" size="small" onPress={() => {}}>
                View All
              </AdaptiveButton>
            </View>
            <TaskList tasks={recentTasks} emptyMessage="No tasks in the last 24 hours" />
          </View>

          {/* Quick Actions */}
          <View style={[sectionStyle, { padding: 16 }]}>
            <AdaptiveText variant="h3" style={{ marginBottom: 12 }}>
              Quick Actions
            </AdaptiveText>
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <AdaptiveButton
                variant="primary"
                size="medium"
                onPress={() => {}}
                style={{ flex: 1 }}
              >
                New Agent
              </AdaptiveButton>
              <AdaptiveButton
                variant="outline"
                size="medium"
                onPress={() => {}}
                style={{ flex: 1 }}
              >
                New Task
              </AdaptiveButton>
            </View>
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
        <AdaptiveText variant="h1">Mrki</AdaptiveText>
        <AdaptiveText variant="caption" style={{ color: '#666' }}>
          {network.isConnected ? (isConnected ? 'Connected' : 'Connecting...') : 'Offline'}
        </AdaptiveText>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {/* Stats */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
          <div style={{ flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, textAlign: 'center' }}>
            <AdaptiveText variant="h2" style={{ color: '#007AFF' }}>{agents.length}</AdaptiveText>
            <AdaptiveText variant="caption">Agents</AdaptiveText>
          </div>
          <div style={{ flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, textAlign: 'center' }}>
            <AdaptiveText variant="h2" style={{ color: '#34C759' }}>{activeAgents.length}</AdaptiveText>
            <AdaptiveText variant="caption">Active</AdaptiveText>
          </div>
          <div style={{ flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, textAlign: 'center' }}>
            <AdaptiveText variant="h2" style={{ color: '#5856D6' }}>{recentTasks.length}</AdaptiveText>
            <AdaptiveText variant="caption">Tasks (24h)</AdaptiveText>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          {/* Active Agents */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <AdaptiveText variant="h3">Active Agents</AdaptiveText>
            </div>
            {activeAgents.length > 0 ? (
              activeAgents.map(agent => (
                <AgentCard key={agent.id} agent={agent} compact onPress={handleViewAgent} />
              ))
            ) : (
              <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, padding: 24, textAlign: 'center' }}>
                <AdaptiveText variant="body" style={{ color: '#999' }}>No active agents</AdaptiveText>
              </div>
            )}
          </div>

          {/* Recent Tasks */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <AdaptiveText variant="h3">Recent Tasks</AdaptiveText>
              <AdaptiveButton variant="ghost" size="small" onPress={() => {}}>View All</AdaptiveButton>
            </div>
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden' }}>
              <TaskList tasks={recentTasks} emptyMessage="No tasks in the last 24 hours" />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
          <AdaptiveButton variant="primary" size="medium" onPress={() => {}} style={{ flex: 1 }}>
            New Agent
          </AdaptiveButton>
          <AdaptiveButton variant="outline" size="medium" onPress={() => {}} style={{ flex: 1 }}>
            New Task
          </AdaptiveButton>
        </div>
      </div>
    </div>
  );
};

export default HomeScreen;
