// Export all API services
export { authService } from './auth';
export { taskService } from './tasks';
export { projectService } from './projects';
export { teamService } from './teams';
export { sprintService } from './sprints';
export { notificationService } from './notifications';
export { organizationService } from './organizations';
export { default as apiClient } from './base';

// Export types from base
export type { PaginatedResponse, QueryParams, User, Organization } from './base';

// Export types from auth
export type { LoginCredentials, RegisterData, AuthResponse } from './auth';

// Export types from tasks
export type { Task, TaskComment, TaskReaction, TimeEntry, TaskStatus } from './tasks';

// Export types from projects
export type { Project, ProjectMember, Label } from './projects';

// Export types from teams
export type { Team, TeamMember } from './teams';

// Export types from sprints
export type { Sprint, SprintTask } from './sprints';

// Export types from notifications
export type { Notification, NotificationPreference } from './notifications';

// Export types from organizations
export type { OrganizationMember } from './organizations';
