import { BaseAPIService } from './base';
import apiClient from './base';

export interface Team {
  id: string;
  name: string;
  description?: string;
  organization: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  team: string;
  user: string;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
}

class TeamService extends BaseAPIService<Team> {
  constructor() {
    super('/teams/');
  }

  async getMembers(teamId: string): Promise<TeamMember[]> {
    const response = await apiClient.get<TeamMember[]>(`${this.endpoint}${teamId}/members/`);
    return response.data;
  }

  async addMember(teamId: string, userId: string, role: string): Promise<TeamMember> {
    const response = await apiClient.post<TeamMember>(`${this.endpoint}${teamId}/members/`, {
      user_id: userId,
      role,
    });
    return response.data;
  }

  async removeMember(teamId: string, memberId: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${teamId}/members/${memberId}/`);
  }

  async updateMemberRole(teamId: string, memberId: string, role: string): Promise<TeamMember> {
    const response = await apiClient.patch<TeamMember>(
      `${this.endpoint}${teamId}/members/${memberId}/`,
      { role }
    );
    return response.data;
  }
}

export const teamService = new TeamService();
