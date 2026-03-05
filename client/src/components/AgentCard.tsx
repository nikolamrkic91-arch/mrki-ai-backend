/**
 * Agent Card Component
 * Displays agent information with platform-adaptive styling
 */

import React from 'react';
import { Agent, AgentStatus } from '@shared/types';
import AdaptiveView from './AdaptiveView';
import AdaptiveText from './AdaptiveText';
import AdaptiveButton from './AdaptiveButton';

interface AgentCardProps {
  agent: Agent;
  onPress?: (agent: Agent) => void;
  onRun?: (agent: Agent) => void;
  onEdit?: (agent: Agent) => void;
  onDelete?: (agent: Agent) => void;
  compact?: boolean;
}

const statusColors: Record<AgentStatus, string> = {
  idle: '#8E8E93',
  running: '#34C759',
  paused: '#FF9500',
  error: '#FF3B30',
  completed: '#007AFF',
};

const statusLabels: Record<AgentStatus, string> = {
  idle: 'Idle',
  running: 'Running',
  paused: 'Paused',
  error: 'Error',
  completed: 'Completed',
};

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

export const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onPress,
  onRun,
  onEdit,
  onDelete,
  compact = false,
}) => {
  const statusColor = statusColors[agent.status];
  const statusLabel = statusLabels[agent.status];

  const containerStyle = {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  };

  const headerStyle = {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  };

  const statusBadgeStyle = {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${statusColor}20`,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  };

  const statusDotStyle = {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: statusColor,
    marginRight: 6,
  };

  const actionsStyle = {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 12,
    gap: 8,
  };

  if (isReactNative) {
    const { View, TouchableOpacity } = require('react-native');

    return (
      <TouchableOpacity onPress={() => onPress?.(agent)} activeOpacity={0.8}>
        <View style={containerStyle}>
          <View style={headerStyle}>
            <AdaptiveText variant="h3" numberOfLines={1} style={{ flex: 1 }}>
              {agent.name}
            </AdaptiveText>
            <View style={statusBadgeStyle}>
              <View style={statusDotStyle} />
              <AdaptiveText variant="caption" style={{ color: statusColor, fontWeight: '600' }}>
                {statusLabel}
              </AdaptiveText>
            </View>
          </View>

          <AdaptiveText variant="body" numberOfLines={compact ? 2 : 3} style={{ color: '#666', marginBottom: 8 }}>
            {agent.description}
          </AdaptiveText>

          {!compact && (
            <AdaptiveText variant="caption" style={{ color: '#999' }}>
              Type: {agent.type} • Last run: {agent.lastRunAt ? new Date(agent.lastRunAt).toLocaleDateString() : 'Never'}
            </AdaptiveText>
          )}

          <View style={actionsStyle}>
            {onRun && (
              <AdaptiveButton
                variant="primary"
                size="small"
                onPress={() => onRun(agent)}
                testID={`agent-run-${agent.id}`}
              >
                Run
              </AdaptiveButton>
            )}
            {onEdit && (
              <AdaptiveButton
                variant="outline"
                size="small"
                onPress={() => onEdit(agent)}
                testID={`agent-edit-${agent.id}`}
              >
                Edit
              </AdaptiveButton>
            )}
            {onDelete && (
              <AdaptiveButton
                variant="ghost"
                size="small"
                onPress={() => onDelete(agent)}
                testID={`agent-delete-${agent.id}`}
              >
                Delete
              </AdaptiveButton>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  }

  // Web implementation
  return (
    <div
      onClick={() => onPress?.(agent)}
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        padding: 16,
        margin: '8px 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        cursor: onPress ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
      }}
      data-testid={`agent-card-${agent.id}`}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <AdaptiveText variant="h3" numberOfLines={1} style={{ flex: 1 }}>
          {agent.name}
        </AdaptiveText>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: `${statusColor}20`,
          padding: '4px 8px',
          borderRadius: 12,
        }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: statusColor, marginRight: 6 }} />
          <AdaptiveText variant="caption" style={{ color: statusColor, fontWeight: 600 }}>
            {statusLabel}
          </AdaptiveText>
        </div>
      </div>

      <AdaptiveText variant="body" numberOfLines={compact ? 2 : 3} style={{ color: '#666', marginBottom: 8 }}>
        {agent.description}
      </AdaptiveText>

      {!compact && (
        <AdaptiveText variant="caption" style={{ color: '#999' }}>
          Type: {agent.type} • Last run: {agent.lastRunAt ? new Date(agent.lastRunAt).toLocaleDateString() : 'Never'}
        </AdaptiveText>
      )}

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12, gap: 8 }}>
        {onRun && (
          <AdaptiveButton variant="primary" size="small" onPress={() => onRun(agent)}>
            Run
          </AdaptiveButton>
        )}
        {onEdit && (
          <AdaptiveButton variant="outline" size="small" onPress={() => onEdit(agent)}>
            Edit
          </AdaptiveButton>
        )}
        {onDelete && (
          <AdaptiveButton variant="ghost" size="small" onPress={() => onDelete(agent)}>
            Delete
          </AdaptiveButton>
        )}
      </div>
    </div>
  );
};

export default AgentCard;
