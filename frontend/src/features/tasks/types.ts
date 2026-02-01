export interface Task {
  id: string;
  projectId: string;
  sectionId?: string;
  parentTaskId?: string;
  taskNumber: number;
  taskKey: string;
  title: string;
  description?: string;
  type: 'task' | 'bug' | 'story' | 'epic' | 'subtask';
  status: TaskStatus;
  priority: 'lowest' | 'low' | 'medium' | 'high' | 'highest';
  severity?: 'minor' | 'major' | 'critical' | 'blocker';
  storyPoints?: number;
  timeEstimate?: number;
  timeLogged: number;
  reporter: TaskUser;
  assignee?: TaskUser;
  dueDate?: string;
  startDate?: string;
  completedAt?: string;
  labels: string[];
  attachmentsCount: number;
  commentsCount: number;
  subtasksCount: number;
  watchersCount: number;
  isArchived: boolean;
  isBlocked: boolean;
  blockingReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskStatus {
  id: string;
  name: string;
  type: 'todo' | 'in_progress' | 'done' | 'canceled';
  color: string;
}

export interface TaskUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface CreateTaskInput {
  projectId: string;
  sectionId?: string;
  parentTaskId?: string;
  title: string;
  description?: string;
  type?: Task['type'];
  statusId: string;
  priority?: Task['priority'];
  severity?: Task['severity'];
  storyPoints?: number;
  timeEstimate?: number;
  assigneeId?: string;
  dueDate?: string;
  startDate?: string;
  labels?: string[];
}

export interface UpdateTaskInput extends Partial<CreateTaskInput> {
  id: string;
}

export interface TaskFilters {
  projectId?: string;
  sectionId?: string;
  statusId?: string;
  assigneeId?: string;
  priority?: Task['priority'];
  type?: Task['type'];
  labels?: string[];
  search?: string;
  isArchived?: boolean;
  isBlocked?: boolean;
}
