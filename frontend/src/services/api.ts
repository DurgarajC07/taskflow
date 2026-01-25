import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('Request Config:', config, 'Token:', token);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(`${API_URL}/users/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Re-export services from api/index.ts
export { 
  authService,
  taskService,
  projectService,
  teamService,
  sprintService,
  notificationService,
  organizationService,
  apiClient
} from './api/index';

// Re-export types
export type {
  PaginatedResponse,
  QueryParams,
  User,
  Organization,
  LoginCredentials,
  RegisterData,
  AuthResponse,
  Task,
  TaskComment,
  TaskReaction,
  TimeEntry,
  TaskStatus,
  Project,
  ProjectMember,
  Label,
  Team,
  TeamMember,
  Sprint,
  SprintTask,
  Notification,
  NotificationPreference,
  OrganizationMember
} from './api/index';

export default api;