import { useState } from 'react';
import { Plus, Filter, Search } from 'lucide-react';
import { MainLayout } from '@/components/layout';
import { Button, Input, Loading, Modal } from '@/components/ui';
import { KanbanBoard } from '@/components/features';
import { useTasks, useUpdateTask, useCreateTask } from '@/hooks';
import type { Task } from '@/services/api/tasks';

const BoardPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'medium' as const,
  });

  const { data: tasksData, isLoading } = useTasks({ page_size: 100 });
  const updateTask = useUpdateTask();
  const createTask = useCreateTask();

  const tasks = tasksData?.results || [];

  // Group tasks by status into columns
  const columns = [
    { id: 'todo', title: 'To Do', color: '#94a3b8', tasks: [] as any[] },
    { id: 'in_progress', title: 'In Progress', color: '#3b82f6', tasks: [] as any[] },
    { id: 'in_review', title: 'Review', color: '#f59e0b', tasks: [] as any[] },
    { id: 'done', title: 'Done', color: '#10b981', tasks: [] as any[] },
  ];

  // Map tasks to columns
  tasks.forEach((task: Task) => {
    const statusType = typeof task.status === 'string' ? task.status : task.status?.type;
    const column = columns.find(col => col.id === statusType);
    if (column) {
      column.tasks.push({
        id: task.id,
        title: task.title,
        description: task.description,
        status: statusType,
        priority: task.priority,
        assignees: task.assignees || [],
        dueDate: task.due_date ? new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : undefined,
        commentsCount: task.comments_count || 0,
        attachmentsCount: task.attachments_count || 0,
        labels: task.labels || [],
      });
    }
  });

  const handleTaskMove = async (taskId: string, _fromColumn: string, toColumn: string) => {
    try {
      await updateTask.mutateAsync({
        id: taskId,
        data: { status: toColumn }
      });
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleTaskClick = (task: any) => {
    console.log('Task clicked:', task);
    // TODO: Open task detail modal
  };

  const handleAddTask = (_columnId: string) => {
    setShowCreateModal(true);
  };

  const handleCreateTask = async () => {
    if (!newTask.title.trim()) return;

    try {
      await createTask.mutateAsync(newTask);
      setShowCreateModal(false);
      setNewTask({ title: '', description: '', priority: 'medium' });
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <Loading text="Loading board..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Project Board</h1>
            <p className="text-sm text-gray-500 mt-1">Manage your tasks with drag and drop</p>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4" />
            Create Task
          </Button>
        </div>

        {/* Filters & Search */}
        <div className="flex items-center gap-4 bg-white p-4 rounded-lg border border-gray-200">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline">
            <Filter className="w-4 h-4" />
            More Filters
          </Button>
        </div>

        {/* Kanban Board */}
        <KanbanBoard
          columns={columns}
          onTaskMove={handleTaskMove}
          onTaskClick={handleTaskClick}
          onAddTask={handleAddTask}
        />

        {/* Create Task Modal */}
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create New Task"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task Title *
              </label>
              <Input
                placeholder="Enter task title"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                placeholder="Enter task description"
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={newTask.priority}
                onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleCreateTask}
                disabled={!newTask.title.trim() || createTask.isPending}
              >
                {createTask.isPending ? 'Creating...' : 'Create Task'}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </MainLayout>
  );
};

export default BoardPage;
