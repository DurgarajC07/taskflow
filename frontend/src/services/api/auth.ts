import apiClient from './base';
import type { User } from '@/types/user';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login/', credentials);
    const { access, refresh, user: _user } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    
    return response.data;
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register/', data);
    const { access, refresh, user: _user } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    
    return response.data;
  },

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout/', { refresh: refreshToken });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/user/');
    return response.data;
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await apiClient.patch<User>('/auth/user/', data);
    return response.data;
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  async resetPassword(email: string): Promise<void> {
    await apiClient.post('/auth/password-reset/', { email });
  },

  async confirmPasswordReset(token: string, password: string): Promise<void> {
    await apiClient.post('/auth/password-reset/confirm/', { token, password });
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
