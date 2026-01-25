import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectService } from '@/services/api';
import type { Project } from '@/services/api/projects';
import type { QueryParams } from '@/services/api/base';

export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (params?: QueryParams) => [...projectKeys.lists(), params] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
  members: (id: string) => [...projectKeys.detail(id), 'members'] as const,
  labels: (id: string) => [...projectKeys.detail(id), 'labels'] as const,
};

export const useProjects = (params?: QueryParams) => {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectService.list(params),
  });
};

export const useProject = (id: string) => {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectService.retrieve(id),
    enabled: !!id,
  });
};

export const useProjectMembers = (projectId: string) => {
  return useQuery({
    queryKey: projectKeys.members(projectId),
    queryFn: () => projectService.getMembers(projectId),
    enabled: !!projectId,
  });
};

export const useProjectLabels = (projectId: string) => {
  return useQuery({
    queryKey: projectKeys.labels(projectId),
    queryFn: () => projectService.getLabels(projectId),
    enabled: !!projectId,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Project>) => projectService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      projectService.partialUpdate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => projectService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
};

export const useAddProjectMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, userId, role }: { projectId: string; userId: string; role: string }) =>
      projectService.addMember(projectId, userId, role),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.members(variables.projectId) });
    },
  });
};

export const useRemoveProjectMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, memberId }: { projectId: string; memberId: string }) =>
      projectService.removeMember(projectId, memberId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.members(variables.projectId) });
    },
  });
};
