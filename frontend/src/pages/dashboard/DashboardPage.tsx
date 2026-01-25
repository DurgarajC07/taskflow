import {
  TrendingUp,
  CheckCircle,
  Clock,
  AlertCircle,
  Users,
  Folder,
  Calendar,
  Activity,
} from 'lucide-react';
import { useState } from 'react';
import { MainLayout } from '@/components/layout';
import { Card, Badge, Loading, EmptyState } from '@/components/ui';
import { TaskDetailModal } from '@/components/features/TaskDetailModal';
import { useTasks, useProjects, useCurrentUser } from '@/hooks';
import { useAuthStore } from '@/store/authStore';
import type { Task } from '@/services/api/tasks';

const DashboardPage = () => {
  const user = useAuthStore((state) => state.user);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const { data: currentUser } = useCurrentUser();
  const { data: tasksData, isLoading: isLoadingTasks } = useTasks({ page_size: 100 });
  const { data: projectsData, isLoading: isLoadingProjects } = useProjects({ page_size: 100 });

  const tasks = tasksData?.results || [];
  const projects = projectsData?.results || [];

  // Calculate stats from real data
  const stats = [
    {
      label: 'Total Tasks',
      value: tasks.length.toString(),
      change: '+12%',
      icon: CheckCircle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'In Progress',
      value: tasks.filter((t: Task) => {
        if (typeof t.status === 'string') return t.status === 'in_progress';
        return t.status?.type === 'in_progress';
      }).length.toString(),
      change: '+4',
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      label: 'Completed',
      value: tasks.filter((t: Task) => {
        if (typeof t.status === 'string') return t.status === 'done';
        return t.status?.type === 'done';
      }).length.toString(),
      change: '+8',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Overdue',
      value: tasks.filter((t: Task) => {
        const isDone = typeof t.status === 'string' ? t.status === 'done' : t.status?.type === 'done';
        return t.due_date && new Date(t.due_date) < new Date() && !isDone;
      }).length.toString(),
      change: '-2',
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ];

  // Get upcoming deadlines from real tasks
  const upcomingDeadlines = tasks
    .filter((task: Task) => {
      const isDone = typeof task.status === 'string' ? task.status === 'done' : task.status?.type === 'done';
      return task.due_date && !isDone;
    })
    .sort((a: Task, b: Task) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime())
    .slice(0, 5)
    .map((task: Task) => ({
      id: task.id,
      title: task.title,
      project: task.project?.name || 'No Project',
      dueDate: new Date(task.due_date!).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      priority: task.priority,
    }));

  const priorityColors = {
    low: 'default' as const,
    medium: 'warning' as const,
    high: 'danger' as const,
    urgent: 'danger' as const,
  };

  if (isLoadingTasks || isLoadingProjects) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Loading size="lg" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {currentUser?.first_name || user?.first_name || 'User'}! 👋
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Here's what's happening with your projects today
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <Card key={stat.label} variant="bordered" padding="lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                  <p
                    className={`text-sm mt-2 ${
                      stat.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {stat.change} from last week
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Tasks */}
          <div className="lg:col-span-2">
            <Card variant="bordered" padding="none">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Recent Tasks
                  </h2>
                  <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                    View all
                  </button>
                </div>
              </div>
              <div className="divide-y divide-gray-200">
                {tasks.length === 0 ? (
                  <div className="p-8">
                    <EmptyState
                      title="No tasks yet"
                      description="Create your first task to get started"
                      icon={CheckCircle}
                    />
                  </div>
                ) : (
                  tasks.slice(0, 5).map((task: Task) => (
                    <div
                      key={task.id}
                      className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => setSelectedTaskId(task.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm font-medium text-gray-900">{task.title}</p>
                            <Badge variant={priorityColors[task.priority as keyof typeof priorityColors]}>
                              {task.priority}
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-500">
                            {task.project?.name || 'No Project'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>

          {/* Upcoming Deadlines */}
          <div>
            <Card variant="bordered" padding="none">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Upcoming Deadlines
                </h2>
              </div>
              <div className="divide-y divide-gray-200">
                {upcomingDeadlines.length === 0 ? (
                  <div className="p-8">
                    <EmptyState
                      title="No upcoming deadlines"
                      description="All caught up!"
                      icon={Calendar}
                    />
                  </div>
                ) : (
                  upcomingDeadlines.map((task: { id: string; title: string; project: string; dueDate: string; priority: string }) => (
                    <div
                      key={task.id}
                      className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => setSelectedTaskId(task.id)}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="text-sm font-medium text-gray-900">{task.title}</h3>
                        <Badge variant={priorityColors[task.priority as keyof typeof priorityColors]} size="sm">
                          {task.priority}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600 mb-2">{task.project}</p>
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Calendar className="w-3 h-3" />
                        <span>{task.dueDate}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card
            variant="bordered"
            padding="lg"
            hoverable
            className="cursor-pointer group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                <Folder className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">My Projects</h3>
                <p className="text-sm text-gray-500">{projects.length} active projects</p>
              </div>
            </div>
          </Card>

          <Card
            variant="bordered"
            padding="lg"
            hoverable
            className="cursor-pointer group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-50 rounded-lg group-hover:bg-green-100 transition-colors">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">My Team</h3>
                <p className="text-sm text-gray-500">View team members</p>
              </div>
            </div>
          </Card>

          <Card
            variant="bordered"
            padding="lg"
            hoverable
            className="cursor-pointer group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-50 rounded-lg group-hover:bg-purple-100 transition-colors">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Reports</h3>
                <p className="text-sm text-gray-500">View analytics</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Task Detail Modal */}
      {selectedTaskId && (
        <TaskDetailModal
          taskId={selectedTaskId}
          isOpen={!!selectedTaskId}
          onClose={() => setSelectedTaskId(null)}
        />
      )}
    </MainLayout>
  );
};

export default DashboardPage;
