import { BaseAPIService } from './base';
import apiClient from './base';

export interface Sprint {
  id: string;
  name: string;
  goal?: string;
  project: string;
  start_date: string;
  end_date: string;
  status: 'planned' | 'active' | 'completed';
  velocity?: number;
  created_at: string;
  updated_at: string;
}

export interface SprintTask {
  id: string;
  sprint: string;
  task: string;
  story_points?: number;
  added_at: string;
}

class SprintService extends BaseAPIService<Sprint> {
  constructor() {
    super('/sprints/');
  }

  async start(sprintId: string): Promise<Sprint> {
    const response = await apiClient.post<Sprint>(`${this.endpoint}${sprintId}/start/`);
    return response.data;
  }

  async complete(sprintId: string): Promise<Sprint> {
    const response = await apiClient.post<Sprint>(`${this.endpoint}${sprintId}/complete/`);
    return response.data;
  }

  async addTask(sprintId: string, taskId: string, storyPoints?: number): Promise<SprintTask> {
    const response = await apiClient.post<SprintTask>(`${this.endpoint}${sprintId}/tasks/`, {
      task_id: taskId,
      story_points: storyPoints,
    });
    return response.data;
  }

  async removeTask(sprintId: string, taskId: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${sprintId}/tasks/${taskId}/`);
  }

  async getTasks(sprintId: string): Promise<SprintTask[]> {
    const response = await apiClient.get<SprintTask[]>(`${this.endpoint}${sprintId}/tasks/`);
    return response.data;
  }

  async getVelocity(sprintId: string): Promise<{ velocity: number }> {
    const response = await apiClient.get<{ velocity: number }>(
      `${this.endpoint}${sprintId}/velocity/`
    );
    return response.data;
  }
}

export const sprintService = new SprintService();
