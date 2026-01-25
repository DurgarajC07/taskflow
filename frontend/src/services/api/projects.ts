import { BaseAPIService } from './base';
import apiClient from './base';

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'archived';
  organization?: string;
  team?: {
    id: string;
    name: string;
  };
  start_date?: string;
  end_date?: string;
  progress?: number;
  created_by?: {
    id: string;
    name: string;
    avatar?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface ProjectMember {
  id: string;
  project: string;
  user: string;
  role: string;
  joined_at: string;
}

export interface Label {
  id: string;
  name: string;
  color: string;
  project: string;
  usage_count: number;
}

class ProjectService extends BaseAPIService<Project> {
  constructor() {
    super('/projects/');
  }

  async getMembers(projectId: string): Promise<ProjectMember[]> {
    const response = await apiClient.get<ProjectMember[]>(`${this.endpoint}${projectId}/members/`);
    return response.data;
  }

  async addMember(projectId: string, userId: string, role: string): Promise<ProjectMember> {
    const response = await apiClient.post<ProjectMember>(`${this.endpoint}${projectId}/members/`, {
      user_id: userId,
      role,
    });
    return response.data;
  }

  async removeMember(projectId: string, memberId: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${projectId}/members/${memberId}/`);
  }

  async updateMemberRole(projectId: string, memberId: string, role: string): Promise<ProjectMember> {
    const response = await apiClient.patch<ProjectMember>(
      `${this.endpoint}${projectId}/members/${memberId}/`,
      { role }
    );
    return response.data;
  }

  async getLabels(projectId: string): Promise<Label[]> {
    const response = await apiClient.get<Label[]>(`${this.endpoint}${projectId}/labels/`);
    return response.data;
  }

  async createLabel(projectId: string, data: Partial<Label>): Promise<Label> {
    const response = await apiClient.post<Label>(`${this.endpoint}${projectId}/labels/`, data);
    return response.data;
  }

  async updateLabel(projectId: string, labelId: string, data: Partial<Label>): Promise<Label> {
    const response = await apiClient.patch<Label>(
      `${this.endpoint}${projectId}/labels/${labelId}/`,
      data
    );
    return response.data;
  }

  async deleteLabel(projectId: string, labelId: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${projectId}/labels/${labelId}/`);
  }

  async archive(projectId: string): Promise<Project> {
    const response = await apiClient.post<Project>(`${this.endpoint}${projectId}/archive/`);
    return response.data;
  }

  async unarchive(projectId: string): Promise<Project> {
    const response = await apiClient.post<Project>(`${this.endpoint}${projectId}/unarchive/`);
    return response.data;
  }
}

export const projectService = new ProjectService();
