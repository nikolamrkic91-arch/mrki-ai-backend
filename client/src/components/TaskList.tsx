/**
 * Task List Component
 * Displays a list of tasks with platform-adaptive styling
 */

import React from 'react';
import { Task, TaskStatus } from '@shared/types';
import AdaptiveView from './AdaptiveView';
import AdaptiveText from './AdaptiveText';
import AdaptiveButton from './AdaptiveButton';

interface TaskListProps {
  tasks: Task[];
  onTaskPress?: (task: Task) => void;
  onTaskCancel?: (task: Task) => void;
  onTaskRetry?: (task: Task) => void;
  loading?: boolean;
  emptyMessage?: string;
}

const statusColors: Record<TaskStatus, string> = {
  pending: '#8E8E93',
  queued: '#5856D6',
  running: '#007AFF',
  paused: '#FF9500',
  completed: '#34C759',
  failed: '#FF3B30',
  cancelled: '#C7C7CC',
};

const statusLabels: Record<TaskStatus, string> = {
  pending: 'Pending',
  queued: 'Queued',
  running: 'Running',
  paused: 'Paused',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

interface TaskItemProps {
  task: Task;
  onPress?: (task: Task) => void;
  onCancel?: (task: Task) => void;
  onRetry?: (task: Task) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, onPress, onCancel, onRetry }) => {
  const statusColor = statusColors[task.status];
  const statusLabel = statusLabels[task.status];
  const isActive = task.status === 'running' || task.status === 'queued' || task.status === 'pending';

  const containerStyle = {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  };

  const statusIndicatorStyle = {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: statusColor,
    marginRight: 12,
  };

  const contentStyle = {
    flex: 1,
  };

  const actionsStyle = {
    flexDirection: 'row',
    gap: 8,
  };

  const formatDuration = (start?: string, end?: string): string => {
    if (!start) return '-';
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = Math.floor((endTime - startTime) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  if (isReactNative) {
    const { View, TouchableOpacity } = require('react-native');

    return (
      <TouchableOpacity onPress={() => onPress?.(task)} activeOpacity={0.7}>
        <View style={containerStyle}>
          <View style={statusIndicatorStyle} />
          <View style={contentStyle}>
            <AdaptiveText variant="body" numberOfLines={1} style={{ fontWeight: '600' }}>
              {task.title}
            </AdaptiveText>
            <AdaptiveText variant="caption" numberOfLines={1} style={{ color: '#666', marginTop: 2 }}>
              {statusLabel} • {formatDuration(task.startedAt, task.completedAt)}
            </AdaptiveText>
            {task.error && (
              <AdaptiveText variant="caption" numberOfLines={2} style={{ color: '#FF3B30', marginTop: 4 }}>
                {task.error}
              </AdaptiveText>
            )}
          </View>
          <View style={actionsStyle}>
            {isActive && onCancel && (
              <AdaptiveButton variant="ghost" size="small" onPress={() => onCancel(task)}>
                Cancel
              </AdaptiveButton>
            )}
            {(task.status === 'failed' || task.status === 'cancelled') && onRetry && (
              <AdaptiveButton variant="primary" size="small" onPress={() => onRetry(task)}>
                Retry
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
      onClick={() => onPress?.(task)}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: 12,
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #E5E5EA',
        cursor: onPress ? 'pointer' : 'default',
        transition: 'background-color 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#F2F2F7';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = '#FFFFFF';
      }}
      data-testid={`task-item-${task.id}`}
    >
      <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: statusColor, marginRight: 12 }} />
      <div style={{ flex: 1 }}>
        <AdaptiveText variant="body" numberOfLines={1} style={{ fontWeight: 600 }}>
          {task.title}
        </AdaptiveText>
        <AdaptiveText variant="caption" style={{ color: '#666', marginTop: 2 }}>
          {statusLabel} • {formatDuration(task.startedAt, task.completedAt)}
        </AdaptiveText>
        {task.error && (
          <AdaptiveText variant="caption" numberOfLines={2} style={{ color: '#FF3B30', marginTop: 4 }}>
            {task.error}
          </AdaptiveText>
        )}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        {isActive && onCancel && (
          <AdaptiveButton variant="ghost" size="small" onPress={() => onCancel(task)}>
            Cancel
          </AdaptiveButton>
        )}
        {(task.status === 'failed' || task.status === 'cancelled') && onRetry && (
          <AdaptiveButton variant="primary" size="small" onPress={() => onRetry(task)}>
            Retry
          </AdaptiveButton>
        )}
      </div>
    </div>
  );
};

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  onTaskPress,
  onTaskCancel,
  onTaskRetry,
  loading = false,
  emptyMessage = 'No tasks yet',
}) => {
  if (loading) {
    return (
      <AdaptiveView style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 }}>
        <AdaptiveText variant="body" style={{ color: '#666' }}>
          Loading tasks...
        </AdaptiveText>
      </AdaptiveView>
    );
  }

  if (tasks.length === 0) {
    return (
      <AdaptiveView style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 }}>
        <AdaptiveText variant="body" style={{ color: '#999', textAlign: 'center' }}>
          {emptyMessage}
        </AdaptiveText>
      </AdaptiveView>
    );
  }

  const containerStyle = {
    flex: 1,
    backgroundColor: '#F2F2F7',
  };

  if (isReactNative) {
    const { FlatList } = require('react-native');

    return (
      <FlatList
        data={tasks}
        keyExtractor={(item: Task) => item.id}
        renderItem={({ item }: { item: Task }) => (
          <TaskItem
            task={item}
            onPress={onTaskPress}
            onCancel={onTaskCancel}
            onRetry={onTaskRetry}
          />
        )}
        contentContainerStyle={{ paddingVertical: 8 }}
      />
    );
  }

  // Web implementation
  return (
    <div style={{ flex: 1, backgroundColor: '#F2F2F7', overflow: 'auto' }}>
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onPress={onTaskPress}
          onCancel={onTaskCancel}
          onRetry={onTaskRetry}
        />
      ))}
    </div>
  );
};

export default TaskList;
