import { apiClient } from './base';
import type { Task, CreateTaskInput, UpdateTaskInput, TaskFilters } from '../../features/tasks/types';
import type { PaginatedResponse, QueryParams } from '../../types/api';

class TasksAPI {
  private baseUrl = '/tasks';

  async getAll(filters?: TaskFilters): Promise<Task[]> {
    const params: QueryParams = {};
    
    if (filters?.projectId) params.project = filters.projectId;
    if (filters?.sectionId) params.section = filters.sectionId;
    if (filters?.statusId) params.status = filters.statusId;
    if (filters?.assigneeId) params.assignee = filters.assigneeId;
    if (filters?.priority) params.priority = filters.priority;
    if (filters?.type) params.type = filters.type;
    if (filters?.labels) params.labels = filters.labels.join(',');
    if (filters?.search) params.search = filters.search;
    if (filters?.isArchived !== undefined) params.is_archived = filters.isArchived;
    if (filters?.isBlocked !== undefined) params.is_blocked = filters.isBlocked;

    const response = await apiClient.get<PaginatedResponse<Task>>(
      `${this.baseUrl}/`,
      params
    );
    return response.results;
  }

  async getById(id: string): Promise<Task> {
    return apiClient.get<Task>(`${this.baseUrl}/${id}/`);
  }

  async create(data: CreateTaskInput): Promise<Task> {
    return apiClient.post<Task>(`${this.baseUrl}/`, data);
  }

  async update(id: string, data: Partial<UpdateTaskInput>): Promise<Task> {
    return apiClient.patch<Task>(`${this.baseUrl}/${id}/`, data);
  }

  async delete(id: string): Promise<void> {
    return apiClient.delete<void>(`${this.baseUrl}/${id}/`);
  }

  async updateStatus(id: string, statusId: string): Promise<Task> {
    return apiClient.patch<Task>(`${this.baseUrl}/${id}/`, { status_id: statusId });
  }

  async assign(id: string, userId: string): Promise<Task> {
    return apiClient.patch<Task>(`${this.baseUrl}/${id}/`, { assignee_id: userId });
  }

  async addLabel(id: string, label: string): Promise<Task> {
    return apiClient.post<Task>(`${this.baseUrl}/${id}/labels/`, { label });
  }

  async removeLabel(id: string, label: string): Promise<Task> {
    return apiClient.delete<Task>(`${this.baseUrl}/${id}/labels/${label}/`);
  }

  async addWatcher(id: string, userId: string): Promise<void> {
    return apiClient.post(`${this.baseUrl}/${id}/watchers/`, { user_id: userId });
  }

  async removeWatcher(id: string, userId: string): Promise<void> {
    return apiClient.delete(`${this.baseUrl}/${id}/watchers/${userId}/`);
  }

  async getComments(id: string): Promise<any[]> {
    return apiClient.get(`${this.baseUrl}/${id}/comments/`);
  }

  async addComment(id: string, content: string): Promise<any> {
    return apiClient.post(`${this.baseUrl}/${id}/comments/`, { content });
  }

  async getAttachments(id: string): Promise<any[]> {
    return apiClient.get(`${this.baseUrl}/${id}/attachments/`);
  }

  async uploadAttachment(id: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload(`${this.baseUrl}/${id}/attachments/`, formData);
  }

  async getActivity(id: string): Promise<any[]> {
    return apiClient.get(`${this.baseUrl}/${id}/activity/`);
  }

  async logTime(id: string, minutes: number, description?: string): Promise<any> {
    return apiClient.post(`${this.baseUrl}/${id}/time-logs/`, {
      time_spent: minutes,
      description,
    });
  }
}

export const tasksAPI = new TasksAPI();
