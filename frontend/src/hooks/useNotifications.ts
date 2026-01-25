import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notificationService, type QueryParams } from '@/services/api';

export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  list: (params?: QueryParams) => [...notificationKeys.lists(), params] as const,
  unreadCount: () => [...notificationKeys.all, 'unreadCount'] as const,
  preferences: () => [...notificationKeys.all, 'preferences'] as const,
};

export const useNotifications = (params?: QueryParams) => {
  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => notificationService.list(params),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useUnreadNotificationCount = () => {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: () => notificationService.getUnreadCount(),
    refetchInterval: 30000,
  });
};

export const useNotificationPreferences = () => {
  return useQuery({
    queryKey: notificationKeys.preferences(),
    queryFn: () => notificationService.getPreferences(),
  });
};

export const useMarkNotificationAsRead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => notificationService.markAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.lists() });
      queryClient.invalidateQueries({ queryKey: notificationKeys.unreadCount() });
    },
  });
};

export const useMarkAllNotificationsAsRead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.lists() });
      queryClient.invalidateQueries({ queryKey: notificationKeys.unreadCount() });
    },
  });
};
