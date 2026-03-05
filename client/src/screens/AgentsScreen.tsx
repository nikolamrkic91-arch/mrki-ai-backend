/**
 * Agents Screen
 * Lists all agents with search and filter capabilities
 */

import React, { useState, useCallback } from 'react';
import { Agent, AgentType, AgentStatus } from '@shared/types';
import { useAgents } from '@shared/hooks/useSync';
import { useWebSocket } from '@shared/hooks/useWebSocket';
import AdaptiveView from '@components/AdaptiveView';
import AdaptiveText from '@components/AdaptiveText';
import AdaptiveButton from '@components/AdaptiveButton';
import AgentCard from '@components/AgentCard';

const WS_URL = process.env.WS_URL || 'ws://localhost:3001';

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

type FilterType = 'all' | AgentType;
type FilterStatus = 'all' | AgentStatus;

export const AgentsScreen: React.FC = () => {
  const { entities: agents, refresh, remove } = useAgents();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<FilterType>('all');
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { send } = useWebSocket({
    url: WS_URL,
    autoConnect: true,
  });

  // Filter agents
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'all' || agent.type === typeFilter;
    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const handleRunAgent = useCallback((agent: Agent) => {
    send('task_create', {
      agentId: agent.id,
      title: `Run ${agent.name}`,
      input: '',
    });
  }, [send]);

  const handleEditAgent = useCallback((agent: Agent) => {
    // Navigate to edit screen
    console.log('Edit agent:', agent.id);
  }, []);

  const handleDeleteAgent = useCallback(async (agent: Agent) => {
    // Confirm delete
    if (isReactNative) {
      const { Alert } = require('react-native');
      Alert.alert(
        'Delete Agent',
        `Are you sure you want to delete "${agent.name}"?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Delete', 
            style: 'destructive',
            onPress: async () => {
              await remove(agent.id);
              refresh();
            }
          },
        ]
      );
    } else {
      if (window.confirm(`Are you sure you want to delete "${agent.name}"?`)) {
        await remove(agent.id);
        refresh();
      }
    }
  }, [remove, refresh]);

  const handleCreateAgent = useCallback(() => {
    setShowCreateModal(true);
  }, []);

  const agentTypes: { value: FilterType; label: string }[] = [
    { value: 'all', label: 'All Types' },
    { value: 'task', label: 'Task' },
    { value: 'research', label: 'Research' },
    { value: 'code', label: 'Code' },
    { value: 'chat', label: 'Chat' },
    { value: 'custom', label: 'Custom' },
  ];

  const agentStatuses: { value: FilterStatus; label: string }[] = [
    { value: 'all', label: 'All Status' },
    { value: 'idle', label: 'Idle' },
    { value: 'running', label: 'Running' },
    { value: 'paused', label: 'Paused' },
    { value: 'error', label: 'Error' },
    { value: 'completed', label: 'Completed' },
  ];

  if (isReactNative) {
    const { View, TextInput, ScrollView, TouchableOpacity } = require('react-native');

    return (
      <View style={{ flex: 1, backgroundColor: '#F2F2F7' }}>
        {/* Header */}
        <View style={{ padding: 16, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#E5E5EA' }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <AdaptiveText variant="h1">Agents</AdaptiveText>
            <AdaptiveButton variant="primary" size="small" onPress={handleCreateAgent}>
              + New
            </AdaptiveButton>
          </View>

          {/* Search */}
          <View style={{
            flexDirection: 'row',
            alignItems: 'center',
            backgroundColor: '#F2F2F7',
            borderRadius: 10,
            paddingHorizontal: 12,
            paddingVertical: 8,
          }}>
            <TextInput
              placeholder="Search agents..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              style={{ flex: 1, fontSize: 16 }}
            />
          </View>

          {/* Filters */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 12 }}>
            {agentTypes.map(type => (
              <TouchableOpacity
                key={type.value}
                onPress={() => setTypeFilter(type.value)}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: 16,
                  backgroundColor: typeFilter === type.value ? '#007AFF' : '#E5E5EA',
                  marginRight: 8,
                }}
              >
                <AdaptiveText
                  variant="caption"
                  style={{ color: typeFilter === type.value ? '#FFFFFF' : '#000000', fontWeight: '600' }}
                >
                  {type.label}
                </AdaptiveText>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Agent List */}
        <ScrollView showsVerticalScrollIndicator={false}>
          {filteredAgents.length === 0 ? (
            <View style={{ padding: 32, alignItems: 'center' }}>
              <AdaptiveText variant="body" style={{ color: '#999', textAlign: 'center' }}>
                {searchQuery ? 'No agents match your search' : 'No agents yet. Create your first agent!'}
              </AdaptiveText>
            </View>
          ) : (
            filteredAgents.map(agent => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onPress={handleEditAgent}
                onRun={handleRunAgent}
                onEdit={handleEditAgent}
                onDelete={handleDeleteAgent}
              />
            ))
          )}
        </ScrollView>
      </View>
    );
  }

  // Web implementation
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#F2F2F7' }}>
      {/* Header */}
      <div style={{ padding: 16, backgroundColor: '#FFFFFF', borderBottom: '1px solid #E5E5EA' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <AdaptiveText variant="h1">Agents</AdaptiveText>
          <AdaptiveButton variant="primary" size="small" onPress={handleCreateAgent}>
            + New Agent
          </AdaptiveButton>
        </div>

        {/* Search and Filters */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              flex: 1,
              minWidth: 200,
              padding: '10px 12px',
              borderRadius: 10,
              border: '1px solid #E5E5EA',
              fontSize: 16,
              outline: 'none',
            }}
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as FilterType)}
            style={{
              padding: '10px 12px',
              borderRadius: 10,
              border: '1px solid #E5E5EA',
              fontSize: 16,
              backgroundColor: '#FFFFFF',
              cursor: 'pointer',
            }}
          >
            {agentTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as FilterStatus)}
            style={{
              padding: '10px 12px',
              borderRadius: 10,
              border: '1px solid #E5E5EA',
              fontSize: 16,
              backgroundColor: '#FFFFFF',
              cursor: 'pointer',
            }}
          >
            {agentStatuses.map(status => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Agent List */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {filteredAgents.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <AdaptiveText variant="body" style={{ color: '#999' }}>
              {searchQuery ? 'No agents match your search' : 'No agents yet. Create your first agent!'}
            </AdaptiveText>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 16 }}>
            {filteredAgents.map(agent => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onPress={handleEditAgent}
                onRun={handleRunAgent}
                onEdit={handleEditAgent}
                onDelete={handleDeleteAgent}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentsScreen;
