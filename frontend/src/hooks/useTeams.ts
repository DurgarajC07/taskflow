import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { teamService } from '@/services/api';
import type { Team } from '@/services/api/teams';
import type { QueryParams } from '@/services/api/base';

export const teamKeys = {
  all: ['teams'] as const,
  lists: () => [...teamKeys.all, 'list'] as const,
  list: (params?: QueryParams) => [...teamKeys.lists(), params] as const,
  details: () => [...teamKeys.all, 'detail'] as const,
  detail: (id: string) => [...teamKeys.details(), id] as const,
  members: (id: string) => [...teamKeys.detail(id), 'members'] as const,
};

export const useTeams = (params?: QueryParams) => {
  return useQuery({
    queryKey: teamKeys.list(params),
    queryFn: () => teamService.list(params),
    staleTime: 30000,
  });
};

export const useTeam = (id: string) => {
  return useQuery({
    queryKey: teamKeys.detail(id),
    queryFn: () => teamService.retrieve(id),
    enabled: !!id,
  });
};

export const useTeamMembers = (teamId: string) => {
  return useQuery({
    queryKey: teamKeys.members(teamId),
    queryFn: () => teamService.getMembers(teamId),
    enabled: !!teamId,
  });
};

export const useCreateTeam = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Team>) => teamService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
    },
  });
};

export const useUpdateTeam = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Team> }) =>
      teamService.partialUpdate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
    },
  });
};

export const useDeleteTeam = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => teamService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.lists() });
    },
  });
};

export const useAddTeamMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, userId, role }: { teamId: string; userId: string; role: string }) =>
      teamService.addMember(teamId, userId, role),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: teamKeys.members(variables.teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(variables.teamId) });
    },
  });
};

export const useRemoveTeamMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, memberId }: { teamId: string; memberId: string }) =>
      teamService.removeMember(teamId, memberId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: teamKeys.members(variables.teamId) });
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(variables.teamId) });
    },
  });
};
