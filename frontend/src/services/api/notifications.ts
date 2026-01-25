import { BaseAPIService } from './base';
import apiClient from './base';

export interface Notification {
  id: string;
  user: string;
  notification_type: string;
  title: string;
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface NotificationPreference {
  id: string;
  user: string;
  notification_type: string;
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  sms_enabled: boolean;
}

class NotificationService extends BaseAPIService<Notification> {
  constructor() {
    super('/notifications/');
  }

  async markAsRead(notificationId: string): Promise<Notification> {
    const response = await apiClient.post<Notification>(
      `${this.endpoint}${notificationId}/mark_read/`
    );
    return response.data;
  }

  async markAllAsRead(): Promise<void> {
    await apiClient.post(`${this.endpoint}mark_all_read/`);
  }

  async getUnreadCount(): Promise<{ count: number }> {
    const response = await apiClient.get<{ count: number }>(`${this.endpoint}unread_count/`);
    return response.data;
  }

  async getPreferences(): Promise<NotificationPreference[]> {
    const response = await apiClient.get<NotificationPreference[]>('/notification-preferences/');
    return response.data;
  }

  async updatePreference(
    preferenceId: string,
    data: Partial<NotificationPreference>
  ): Promise<NotificationPreference> {
    const response = await apiClient.patch<NotificationPreference>(
      `/notification-preferences/${preferenceId}/`,
      data
    );
    return response.data;
  }
}

export const notificationService = new NotificationService();
