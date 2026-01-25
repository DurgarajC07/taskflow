import { useState } from 'react';
import { Plus, Filter, Search } from 'lucide-react';
import { MainLayout } from '@/components/layout';
import { Button, Input, Select } from '@/components/ui';
import { KanbanBoard } from '@/components/features';

// Sample data
const initialColumns = [
  {
    id: 'todo',
    title: 'To Do',
    color: '#94a3b8',
    tasks: [
      {
        id: '1',
        title: 'Design new landing page',
        description: 'Create wireframes and mockups for the new landing page',
        status: 'todo',
        priority: 'high' as const,
        assignees: [
          { id: '1', name: 'John Doe', avatar: '' },
          { id: '2', name: 'Jane Smith', avatar: '' },
        ],
        dueDate: 'Mar 15',
        commentsCount: 3,
        attachmentsCount: 2,
        labels: [
          { id: '1', name: 'Design', color: '#8b5cf6' },
          { id: '2', name: 'Frontend', color: '#3b82f6' },
        ],
      },
      {
        id: '2',
        title: 'Update API documentation',
        status: 'todo',
        priority: 'medium' as const,
        assignees: [{ id: '3', name: 'Bob Wilson', avatar: '' }],
        dueDate: 'Mar 18',
        commentsCount: 1,
        labels: [{ id: '3', name: 'Documentation', color: '#10b981' }],
      },
    ],
  },
  {
    id: 'in-progress',
    title: 'In Progress',
    color: '#3b82f6',
    tasks: [
      {
        id: '3',
        title: 'Implement user authentication',
        description: 'Add JWT-based authentication with refresh tokens',
        status: 'in-progress',
        priority: 'critical' as const,
        assignees: [
          { id: '4', name: 'Alice Johnson', avatar: '' },
          { id: '5', name: 'Charlie Brown', avatar: '' },
        ],
        dueDate: 'Mar 12',
        commentsCount: 8,
        attachmentsCount: 1,
        labels: [
          { id: '4', name: 'Backend', color: '#f59e0b' },
          { id: '5', name: 'Security', color: '#ef4444' },
        ],
      },
      {
        id: '4',
        title: 'Fix mobile responsive issues',
        status: 'in-progress',
        priority: 'high' as const,
        assignees: [{ id: '1', name: 'John Doe', avatar: '' }],
        dueDate: 'Mar 14',
        commentsCount: 5,
        labels: [{ id: '2', name: 'Frontend', color: '#3b82f6' }],
      },
    ],
  },
  {
    id: 'review',
    title: 'Review',
    color: '#f59e0b',
    tasks: [
      {
        id: '5',
        title: 'Code review for payment integration',
        status: 'review',
        priority: 'high' as const,
        assignees: [
          { id: '2', name: 'Jane Smith', avatar: '' },
          { id: '3', name: 'Bob Wilson', avatar: '' },
        ],
        dueDate: 'Mar 13',
        commentsCount: 12,
        attachmentsCount: 3,
        labels: [
          { id: '4', name: 'Backend', color: '#f59e0b' },
          { id: '6', name: 'Payment', color: '#8b5cf6' },
        ],
      },
    ],
  },
  {
    id: 'done',
    title: 'Done',
    color: '#10b981',
    tasks: [
      {
        id: '6',
        title: 'Setup CI/CD pipeline',
        status: 'done',
        priority: 'medium' as const,
        assignees: [{ id: '4', name: 'Alice Johnson', avatar: '' }],
        dueDate: 'Mar 10',
        commentsCount: 4,
        labels: [{ id: '7', name: 'DevOps', color: '#06b6d4' }],
      },
      {
        id: '7',
        title: 'Database schema design',
        status: 'done',
        priority: 'low' as const,
        assignees: [{ id: '5', name: 'Charlie Brown', avatar: '' }],
        dueDate: 'Mar 08',
        commentsCount: 2,
        labels: [{ id: '4', name: 'Backend', color: '#f59e0b' }],
      },
    ],
  },
];

const BoardPage = () => {
  const [columns, setColumns] = useState(initialColumns);
  const [searchQuery, setSearchQuery] = useState('');

  const handleTaskMove = (taskId: string, fromColumn: string, toColumn: string) => {
    console.log(`Moving task ${taskId} from ${fromColumn} to ${toColumn}`);
    
    // Find the task
    const sourceColumn = columns.find((col) => col.id === fromColumn);
    const task = sourceColumn?.tasks.find((t) => t.id === taskId);
    
    if (!task) return;

    // Update columns
    const newColumns = columns.map((col) => {
      if (col.id === fromColumn) {
        return {
          ...col,
          tasks: col.tasks.filter((t) => t.id !== taskId),
        };
      }
      if (col.id === toColumn) {
        return {
          ...col,
          tasks: [...col.tasks, { ...task, status: toColumn }],
        };
      }
      return col;
    });

    setColumns(newColumns);
  };

  const handleTaskClick = (task: any) => {
    console.log('Task clicked:', task);
    // TODO: Open task detail modal
  };

  const handleAddTask = (columnId: string) => {
    console.log('Add task to column:', columnId);
    // TODO: Open create task modal
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Project Board</h1>
            <p className="text-sm text-gray-500 mt-1">Manage your tasks with drag and drop</p>
          </div>
          <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
            Create Task
          </Button>
        </div>

        {/* Filters & Search */}
        <div className="flex items-center gap-4 bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex-1">
            <Input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
          <Select
            options={[
              { label: 'All Members', value: 'all' },
              { label: 'John Doe', value: '1' },
              { label: 'Jane Smith', value: '2' },
              { label: 'Bob Wilson', value: '3' },
            ]}
            value="all"
            onChange={() => {}}
            placeholder="Filter by member"
          />
          <Select
            options={[
              { label: 'All Priorities', value: 'all' },
              { label: 'Critical', value: 'critical' },
              { label: 'High', value: 'high' },
              { label: 'Medium', value: 'medium' },
              { label: 'Low', value: 'low' },
            ]}
            value="all"
            onChange={() => {}}
            placeholder="Filter by priority"
          />
          <Button variant="outline" leftIcon={<Filter className="w-4 h-4" />}>
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
      </div>
    </MainLayout>
  );
};

export default BoardPage;
