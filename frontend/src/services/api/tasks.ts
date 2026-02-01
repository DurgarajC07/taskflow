import { BaseAPIService, type User } from './base';
import apiClient from './base';

export interface TaskStatus {
  id: string;
  name: string;
  type: 'todo' | 'in_progress' | 'done' | 'canceled';
  color: string;
}

export interface Task {
  id: string;
  task_number: number;
  task_key: string;
  title: string;
  description?: string;
  status: TaskStatus | string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  type?: 'task' | 'bug' | 'feature' | 'epic' | 'story' | 'subtask';
  project?: {
    id: string;
    name: string;
    key: string;
  };
  section?: {
    id: string;
    name: string;
  };
  parent_task?: string | null;
  assignees?: User[];
  reporter?: User;
  created_by?: User;
  due_date?: string;
  start_date?: string;
  completed_at?: string;
  story_points?: number;
  time_estimate?: number;
  time_logged?: number;
  estimated_hours?: number;
  actual_hours?: number;
  labels?: Array<{
    id: string;
    name: string;
    color: string;
  }>;
  tags?: string[];
  attachments_count?: number;
  comments_count?: number;
  subtasks_count?: number;
  watchers_count?: number;
  is_archived: boolean;
  is_blocked: boolean;
  blocking_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskComment {
  id: string;
  task: string;
  author: User;
  user?: User;
  content: string;
  parent?: string;
  mentions?: string[];
  is_edited: boolean;
  edited_at?: string;
  is_internal: boolean;
  reaction_count: number;
  created_at: string;
  updated_at: string;
}

export interface TaskReaction {
  id: string;
  task: string;
  user: string;
  reaction_type: string;
  created_at: string;
}

export interface TimeEntry {
  id?: string;
  task?: string;
  user?: string | User;
  hours: number;
  description?: string;
  is_billable: boolean;
  billable?: boolean;
  date: string;
  logged_at?: string;
  created_at?: string;
  updated_at?: string;
}

class TaskService extends BaseAPIService<Task> {
  constructor() {
    super('/tasks/');
  }

  async assignUsers(taskId: string, userIds: string[]): Promise<Task> {
    const response = await apiClient.post<Task>(`${this.endpoint}${taskId}/assign/`, {
      user_ids: userIds,
    });
    return response.data;
  }

  async unassignUsers(taskId: string, userIds: string[]): Promise<Task> {
    const response = await apiClient.post<Task>(`${this.endpoint}${taskId}/unassign/`, {
      user_ids: userIds,
    });
    return response.data;
  }

  async changeStatus(taskId: string, status: string): Promise<Task> {
    const response = await apiClient.post<Task>(`${this.endpoint}${taskId}/change_status/`, {
      status,
    });
    return response.data;
  }

  async addComment(taskId: string, content: string, parentId?: string): Promise<TaskComment> {
    const response = await apiClient.post<TaskComment>(`${this.endpoint}${taskId}/comments/`, {
      content,
      parent: parentId,
    });
    return response.data;
  }

  async getComments(taskId: string): Promise<TaskComment[]> {
    const response = await apiClient.get<TaskComment[]>(`${this.endpoint}${taskId}/comments/`);
    return response.data;
  }

  async addReaction(taskId: string, reactionType: string): Promise<TaskReaction> {
    const response = await apiClient.post<TaskReaction>(`${this.endpoint}${taskId}/reactions/`, {
      reaction_type: reactionType,
    });
    return response.data;
  }

  async removeReaction(taskId: string, reactionId: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${taskId}/reactions/${reactionId}/`);
  }

  async logTime(taskId: string, data: Partial<TimeEntry>): Promise<TimeEntry> {
    const response = await apiClient.post<TimeEntry>(`${this.endpoint}${taskId}/time_entries/`, data);
    return response.data;
  }

  async getTimeEntries(taskId: string): Promise<TimeEntry[]> {
    const response = await apiClient.get<TimeEntry[]>(`${this.endpoint}${taskId}/time_entries/`);
    return response.data;
  }
}

export const taskService = new TaskService();

// New API client for feature slice
class TasksAPI {
  private baseUrl = '/tasks';

  async getAll(filters?: TaskFilters): Promise<FeatureTask[]> {
    const params: any = {};
    if (filters?.projectId) params.project = filters.projectId;
    if (filters?.statusId) params.status = filters.statusId;
    if (filters?.assigneeId) params.assignee = filters.assigneeId;
    if (filters?.search) params.search = filters.search;
    
    const response = await apiClient.get<PaginatedResponse<any>>(`${this.baseUrl}/`, { params });
    return response.data.results.map((t: any) => this.mapTask(t));
  }

  async getById(id: string): Promise<FeatureTask> {
    const response = await apiClient.get<any>(`${this.baseUrl}/${id}/`);
    return this.mapTask(response.data);
  }

  async create(data: CreateTaskInput): Promise<FeatureTask> {
    const response = await apiClient.post<any>(`${this.baseUrl}/`, data);
    return this.getById(response.data.id);
  }

  async update(id: string, data: Partial<UpdateTaskInput>): Promise<FeatureTask> {
    const response = await apiClient.patch<any>(`${this.baseUrl}/${id}/`, data);
    return this.getById(response.data.id);
  }

  async delete(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}/`);
  }

  private mapTask(t: any): FeatureTask {
    return {
      id: t.id,
      projectId: t.project,
      sectionId: t.section,
      parentTaskId: t.parent_task,
      taskNumber: t.task_number,
      taskKey: t.task_key || `TASK-${t.task_number}`,
      title: t.title,
      description: t.description,
      type: t.type || 'task',
      status: typeof t.status === 'object' ? t.status : { id: t.status, name: 'Unknown', type: 'todo', color: '#gray' },
      priority: t.priority || 'medium',
      severity: t.severity,
      storyPoints: t.story_points,
      timeEstimate: t.time_estimate,
      timeLogged: t.time_logged || 0,
      reporter: t.reporter || { id: '', name: 'Unknown', email: '' },
      assignee: t.assignee,
      dueDate: t.due_date,
      startDate: t.start_date,
      completedAt: t.completed_at,
      labels: t.labels || [],
      attachmentsCount: t.attachments_count || 0,
      commentsCount: t.comments_count || 0,
      subtasksCount: t.subtasks_count || 0,
      watchersCount: t.watchers_count || 0,
      isArchived: t.is_archived || false,
      isBlocked: t.is_blocked || false,
      blockingReason: t.blocking_reason,
      createdAt: t.created_at,
      updatedAt: t.updated_at,
    };
  }
}

export const tasksAPI = new TasksAPI();
