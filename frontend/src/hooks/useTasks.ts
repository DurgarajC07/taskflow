import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { taskService } from '@/services/api';
import type { Task, TimeEntry } from '@/services/api/tasks';
import type { QueryParams } from '@/services/api/base';

// Query keys
export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (params?: QueryParams) => [...taskKeys.lists(), params] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
  comments: (id: string) => [...taskKeys.detail(id), 'comments'] as const,
  timeEntries: (id: string) => [...taskKeys.detail(id), 'timeEntries'] as const,
};

// Queries
export const useTasks = (params?: QueryParams) => {
  return useQuery({
    queryKey: taskKeys.list(params),
    queryFn: () => taskService.list(params),
    staleTime: 30000, // 30 seconds
  });
};

export const useTask = (id: string, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: taskKeys.detail(id),
    queryFn: () => taskService.retrieve(id),
    enabled: options?.enabled ?? !!id,
    ...options,
  });
};

export const useTaskComments = (taskId: string) => {
  return useQuery({
    queryKey: taskKeys.comments(taskId),
    queryFn: () => taskService.getComments(taskId),
    enabled: !!taskId,
  });
};

export const useTaskTimeEntries = (taskId: string) => {
  return useQuery({
    queryKey: taskKeys.timeEntries(taskId),
    queryFn: () => taskService.getTimeEntries(taskId),
    enabled: !!taskId,
  });
};

// Mutations
export const useCreateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Task>) => taskService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
};

export const useUpdateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Task> }) =>
      taskService.partialUpdate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
};

export const useDeleteTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => taskService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
};

export const useAssignUsers = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, userIds }: { taskId: string; userIds: string[] }) =>
      taskService.assignUsers(taskId, userIds),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
};

export const useChangeTaskStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      taskService.changeStatus(taskId, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.taskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
};

export const useAddComment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, content, parentId }: { taskId: string; content: string; parentId?: string }) =>
      taskService.addComment(taskId, content, parentId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.comments(variables.taskId) });
    },
  });
};

export const useAddReaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, reactionType }: { taskId: string; reactionType: string }) =>
      taskService.addReaction(taskId, reactionType),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.taskId) });
    },
  });
};

export const useLogTime = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: Partial<TimeEntry> }) =>
      taskService.logTime(taskId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: taskKeys.timeEntries(variables.taskId) });
    },
  });
};
