import { BaseAPIService, type Organization, type User } from './base';
import apiClient from './base';

export interface OrganizationMember {
  id: string;
  user: User;
  organization: string;
  role: 'owner' | 'admin' | 'member' | 'guest';
  permissions?: Record<string, any>;
  invitation_status?: 'pending' | 'accepted' | 'rejected';
  joined_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

class OrganizationService extends BaseAPIService<Organization> {
  constructor() {
    super('/organizations/');
  }

  async getMembers(organizationId: string): Promise<OrganizationMember[]> {
    const response = await apiClient.get<OrganizationMember[]>(
      `${this.endpoint}${organizationId}/members/`
    );
    return response.data;
  }

  async addMember(
    organizationId: string,
    userId: string,
    role: string
  ): Promise<OrganizationMember> {
    const response = await apiClient.post<OrganizationMember>(
      `${this.endpoint}${organizationId}/members/`,
      {
        user_id: userId,
        role,
      }
    );
    return response.data;
  }

  async removeMember(organizationId: string, memberId: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${organizationId}/members/${memberId}/`);
  }

  async updateMemberRole(
    organizationId: string,
    memberId: string,
    role: string
  ): Promise<OrganizationMember> {
    const response = await apiClient.patch<OrganizationMember>(
      `${this.endpoint}${organizationId}/members/${memberId}/`,
      { role }
    );
    return response.data;
  }

  async getBySlug(slug: string): Promise<Organization> {
    const response = await apiClient.get<Organization>(`${this.endpoint}${slug}/`);
    return response.data;
  }

  async updateBySlug(slug: string, data: Partial<Organization>): Promise<Organization> {
    const response = await apiClient.patch<Organization>(`${this.endpoint}${slug}/`, data);
    return response.data;
  }

  async deleteBySlug(slug: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${slug}/`);
  }
}

export const organizationService = new OrganizationService();
export type { Organization };
