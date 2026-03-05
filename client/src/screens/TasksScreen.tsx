/**
 * Tasks Screen
 * Lists all tasks with filtering and search
 */

import React, { useState, useCallback } from 'react';
import { Task, TaskStatus } from '@shared/types';
import { useTasks } from '@shared/hooks/useSync';
import { useWebSocket } from '@shared/hooks/useWebSocket';
import AdaptiveView from '@components/AdaptiveView';
import AdaptiveText from '@components/AdaptiveText';
import AdaptiveButton from '@components/AdaptiveButton';
import TaskList from '@components/TaskList';

const WS_URL = process.env.WS_URL || 'ws://localhost:3001';

const isReactNative = typeof navigator !== 'undefined' && navigator.product === 'ReactNative';

type FilterStatus = 'all' | TaskStatus;

export const TasksScreen: React.FC = () => {
  const { entities: tasks, refresh } = useTasks();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const { send } = useWebSocket({
    url: WS_URL,
    autoConnect: true,
  });

  // Filter and sort tasks
  const filteredTasks = tasks
    .filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           (task.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  // Group tasks by date
  const groupedTasks = filteredTasks.reduce((groups, task) => {
    const date = new Date(task.createdAt).toLocaleDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(task);
    return groups;
  }, {} as Record<string, Task[]>);

  const handleTaskPress = useCallback((task: Task) => {
    setSelectedTask(task);
  }, []);

  const handleTaskCancel = useCallback((task: Task) => {
    send('task_update', {
      taskId: task.id,
      status: 'cancelled',
    });
  }, [send]);

  const handleTaskRetry = useCallback((task: Task) => {
    send('task_create', {
      agentId: task.agentId,
      title: `Retry: ${task.title}`,
      input: task.input,
    });
  }, [send]);

  const taskStatuses: { value: FilterStatus; label: string; count?: number }[] = [
    { value: 'all', label: 'All', count: tasks.length },
    { value: 'running', label: 'Running', count: tasks.filter(t => t.status === 'running').length },
    { value: 'queued', label: 'Queued', count: tasks.filter(t => t.status === 'queued').length },
    { value: 'completed', label: 'Completed', count: tasks.filter(t => t.status === 'completed').length },
    { value: 'failed', label: 'Failed', count: tasks.filter(t => t.status === 'failed').length },
  ];

  if (isReactNative) {
    const { View, TextInput, ScrollView, TouchableOpacity } = require('react-native');

    return (
      <View style={{ flex: 1, backgroundColor: '#F2F2F7' }}>
        {/* Header */}
        <View style={{ padding: 16, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#E5E5EA' }}>
          <AdaptiveText variant="h1" style={{ marginBottom: 12 }}>Tasks</AdaptiveText>

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
              placeholder="Search tasks..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              style={{ flex: 1, fontSize: 16 }}
            />
          </View>

          {/* Status Filters */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 12 }}>
            {taskStatuses.map(status => (
              <TouchableOpacity
                key={status.value}
                onPress={() => setStatusFilter(status.value)}
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: 16,
                  backgroundColor: statusFilter === status.value ? '#007AFF' : '#E5E5EA',
                  marginRight: 8,
                }}
              >
                <AdaptiveText
                  variant="caption"
                  style={{ color: statusFilter === status.value ? '#FFFFFF' : '#000000', fontWeight: '600' }}
                >
                  {status.label}
                </AdaptiveText>
                {status.count !== undefined && status.count > 0 && (
                  <View style={{
                    backgroundColor: statusFilter === status.value ? 'rgba(255,255,255,0.3)' : '#FFFFFF',
                    borderRadius: 10,
                    paddingHorizontal: 6,
                    paddingVertical: 2,
                    marginLeft: 6,
                  }}>
                    <AdaptiveText variant="caption" style={{ fontSize: 12, fontWeight: '600' }}>
                      {status.count}
                    </AdaptiveText>
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Task List */}
        <TaskList
          tasks={filteredTasks}
          onTaskPress={handleTaskPress}
          onTaskCancel={handleTaskCancel}
          onTaskRetry={handleTaskRetry}
          emptyMessage={searchQuery ? 'No tasks match your search' : 'No tasks yet'}
        />
      </View>
    );
  }

  // Web implementation
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#F2F2F7' }}>
      {/* Header */}
      <div style={{ padding: 16, backgroundColor: '#FFFFFF', borderBottom: '1px solid #E5E5EA' }}>
        <AdaptiveText variant="h1" style={{ marginBottom: 12 }}>Tasks</AdaptiveText>

        {/* Search and Filters */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search tasks..."
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
            {taskStatuses.map(status => (
              <option key={status.value} value={status.value}>
                {status.label} {status.count ? `(${status.count})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Status Pills */}
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          {taskStatuses.map(status => (
            <button
              key={status.value}
              onClick={() => setStatusFilter(status.value)}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '6px 12px',
                borderRadius: 16,
                border: 'none',
                backgroundColor: statusFilter === status.value ? '#007AFF' : '#E5E5EA',
                color: statusFilter === status.value ? '#FFFFFF' : '#000000',
                fontWeight: 600,
                fontSize: 14,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {status.label}
              {status.count !== undefined && status.count > 0 && (
                <span style={{
                  backgroundColor: statusFilter === status.value ? 'rgba(255,255,255,0.3)' : '#FFFFFF',
                  borderRadius: 10,
                  padding: '2px 6px',
                  marginLeft: 6,
                  fontSize: 12,
                }}>
                  {status.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Task List */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <TaskList
          tasks={filteredTasks}
          onTaskPress={handleTaskPress}
          onTaskCancel={handleTaskCancel}
          onTaskRetry={handleTaskRetry}
          emptyMessage={searchQuery ? 'No tasks match your search' : 'No tasks yet'}
        />
      </div>
    </div>
  );
};

export default TasksScreen;
