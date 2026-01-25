import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { sprintService, type QueryParams } from '@/services/api';
import type { Sprint, SprintTask } from '@/services/api/sprints';

export const sprintKeys = {
  all: ['sprints'] as const,
  lists: () => [...sprintKeys.all, 'list'] as const,
  list: (params?: QueryParams) => [...sprintKeys.lists(), params] as const,
  details: () => [...sprintKeys.all, 'detail'] as const,
  detail: (id: string) => [...sprintKeys.details(), id] as const,
  tasks: (id: string) => [...sprintKeys.detail(id), 'tasks'] as const,
  velocity: (id: string) => [...sprintKeys.detail(id), 'velocity'] as const,
};

export const useSprints = (params?: QueryParams) => {
  return useQuery({
    queryKey: sprintKeys.list(params),
    queryFn: () => sprintService.list(params),
    staleTime: 30000,
  });
};

export const useSprint = (id: string) => {
  return useQuery({
    queryKey: sprintKeys.detail(id),
    queryFn: () => sprintService.retrieve(id),
    enabled: !!id,
  });
};

export const useSprintTasks = (sprintId: string) => {
  return useQuery({
    queryKey: sprintKeys.tasks(sprintId),
    queryFn: () => sprintService.getTasks(sprintId),
    enabled: !!sprintId,
  });
};

export const useSprintVelocity = (sprintId: string) => {
  return useQuery({
    queryKey: sprintKeys.velocity(sprintId),
    queryFn: () => sprintService.getVelocity(sprintId),
    enabled: !!sprintId,
  });
};

export const useCreateSprint = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Sprint>) => sprintService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.lists() });
    },
  });
};

export const useUpdateSprint = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Sprint> }) =>
      sprintService.partialUpdate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: sprintKeys.lists() });
    },
  });
};

export const useDeleteSprint = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sprintService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.lists() });
    },
  });
};

export const useStartSprint = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sprintId: string) => sprintService.start(sprintId),
    onSuccess: (_, sprintId) => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.detail(sprintId) });
      queryClient.invalidateQueries({ queryKey: sprintKeys.lists() });
    },
  });
};

export const useCompleteSprint = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sprintId: string) => sprintService.complete(sprintId),
    onSuccess: (_, sprintId) => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.detail(sprintId) });
      queryClient.invalidateQueries({ queryKey: sprintKeys.lists() });
    },
  });
};

export const useAddSprintTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sprintId,
      taskId,
      storyPoints,
    }: {
      sprintId: string;
      taskId: string;
      storyPoints?: number;
    }) => sprintService.addTask(sprintId, taskId, storyPoints),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.tasks(variables.sprintId) });
      queryClient.invalidateQueries({ queryKey: sprintKeys.detail(variables.sprintId) });
    },
  });
};

export const useRemoveSprintTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sprintId, taskId }: { sprintId: string; taskId: string }) =>
      sprintService.removeTask(sprintId, taskId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: sprintKeys.tasks(variables.sprintId) });
      queryClient.invalidateQueries({ queryKey: sprintKeys.detail(variables.sprintId) });
    },
  });
};
