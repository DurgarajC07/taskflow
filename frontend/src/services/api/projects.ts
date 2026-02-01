import { BaseAPIService } from './base';
import apiClient, { type PaginatedResponse } from './base';
import type { Project as FeatureProject, CreateProjectInput, UpdateProjectInput } from '../../features/projects/types';

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

// New API client for feature slice
class ProjectsAPI {
  private baseUrl = '/projects';

  async getAll(organizationId?: string): Promise<FeatureProject[]> {
    const params: any = {};
    if (organizationId) {
      params.organization = organizationId;
    }
    const response = await apiClient.get<PaginatedResponse<any>>(`${this.baseUrl}/`, { params });
    return response.data.results.map((p: any) => ({
      id: p.id,
      name: p.name,
      key: p.key || p.name.substring(0, 3).toUpperCase(),
      description: p.description,
      status: p.status,
      priority: p.priority || 'medium',
      progress: p.progress || 0,
      visibility: p.visibility || 'private',
      lead: p.created_by,
      memberCount: p.member_count || 0,
      taskCount: p.task_count || 0,
      completedTaskCount: p.completed_task_count || 0,
      createdAt: p.created_at,
      updatedAt: p.updated_at,
    }));
  }

  async getById(id: string): Promise<FeatureProject> {
    const response = await apiClient.get<any>(`${this.baseUrl}/${id}/`);
    const p = response.data;
    return {
      id: p.id,
      name: p.name,
      key: p.key || p.name.substring(0, 3).toUpperCase(),
      description: p.description,
      status: p.status,
      priority: p.priority || 'medium',
      progress: p.progress || 0,
      visibility: p.visibility || 'private',
      lead: p.created_by,
      memberCount: p.member_count || 0,
      taskCount: p.task_count || 0,
      completedTaskCount: p.completed_task_count || 0,
      createdAt: p.created_at,
      updatedAt: p.updated_at,
    };
  }

  async create(data: CreateProjectInput): Promise<FeatureProject> {
    const response = await apiClient.post<any>(`${this.baseUrl}/`, data);
    return this.getById(response.data.id);
  }

  async update(id: string, data: Partial<UpdateProjectInput>): Promise<FeatureProject> {
    const response = await apiClient.patch<any>(`${this.baseUrl}/${id}/`, data);
    return this.getById(response.data.id);
  }

  async delete(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}/`);
  }
}

export const projectsAPI = new ProjectsAPI();
