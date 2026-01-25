import axios, { type AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Generic API methods
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  page_size: number;
  total_pages: number;
  current_page: number;
  results: T[];
}

export interface QueryParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  search?: string;
  [key: string]: any;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  name?: string;
  avatar?: string;
  timezone?: string;
  language?: string;
  notification_settings?: Record<string, any>;
  working_hours?: Record<string, any>;
  last_activity?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo?: string;
  owner?: User;
  billing_plan?: string;
  member_limit?: number;
  storage_limit?: number;
  storage_used?: number;
  settings?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export class BaseAPIService<T = any> {
  protected endpoint: string;
  
  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }

  async list(params?: QueryParams): Promise<PaginatedResponse<T>> {
    const response = await apiClient.get<PaginatedResponse<T>>(this.endpoint, { params });
    return response.data;
  }

  async retrieve(id: string): Promise<T> {
    const response = await apiClient.get<T>(`${this.endpoint}${id}/`);
    return response.data;
  }

  async create(data: Partial<T>): Promise<T> {
    const response = await apiClient.post<T>(this.endpoint, data);
    return response.data;
  }

  async update(id: string, data: Partial<T>): Promise<T> {
    const response = await apiClient.put<T>(`${this.endpoint}${id}/`, data);
    return response.data;
  }

  async partialUpdate(id: string, data: Partial<T>): Promise<T> {
    const response = await apiClient.patch<T>(`${this.endpoint}${id}/`, data);
    return response.data;
  }

  async delete(id: string): Promise<void> {
    await apiClient.delete(`${this.endpoint}${id}/`);
  }

  async bulkDelete(ids: string[]): Promise<void> {
    await apiClient.post(`${this.endpoint}bulk_delete/`, { ids });
  }
}

export default apiClient;
