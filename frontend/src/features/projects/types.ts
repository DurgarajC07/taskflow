export interface Project {
  id: string;
  name: string;
  key: string;
  description?: string;
  coverImage?: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'archived';
  priority: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
  startDate?: string;
  dueDate?: string;
  progress: number;
  visibility: 'public' | 'private' | 'team';
  lead?: {
    id: string;
    name: string;
    avatar?: string;
  };
  memberCount: number;
  taskCount: number;
  completedTaskCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProjectInput {
  name: string;
  key: string;
  description?: string;
  status?: Project['status'];
  priority?: Project['priority'];
  category?: string;
  startDate?: string;
  dueDate?: string;
  visibility?: Project['visibility'];
  leadId?: string;
}

export interface UpdateProjectInput extends Partial<CreateProjectInput> {
  id: string;
}
