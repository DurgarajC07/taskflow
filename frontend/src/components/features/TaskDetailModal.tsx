import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { Loading } from '@/components/ui/Loading';
import {
  useTask,
  useUpdateTask,
  useDeleteTask,
  useTaskComments,
  useAddComment,
  useChangeTaskStatus,
  useTaskTimeEntries,
  useLogTime,
} from '@/hooks';
import type { Task, TaskComment, TimeEntry } from '@/services/api/tasks';
import type { User } from '@/services/api/base';

interface TaskDetailModalProps {
  taskId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const TaskDetailModal = ({ taskId, isOpen, onClose }: TaskDetailModalProps) => {
  const { data: task, isLoading } = useTask(taskId);
  const { data: comments } = useTaskComments(taskId);
  const { data: timeEntries } = useTaskTimeEntries(taskId);
  
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const addComment = useAddComment();
  const changeStatus = useChangeTaskStatus();
  const logTime = useLogTime();

  const [isEditing, setIsEditing] = useState(false);
  const [editedTask, setEditedTask] = useState<Partial<Task>>({});
  const [newComment, setNewComment] = useState('');
  const [timeLog, setTimeLog] = useState({ hours: 0, description: '' });

  if (isLoading) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="Loading..." size="lg">
        <Loading />
      </Modal>
    );
  }

  if (!task) return null;

  const handleSave = () => {
    updateTask.mutate(
      { id: taskId, data: editedTask },
      {
        onSuccess: () => {
          setIsEditing(false);
          setEditedTask({});
        },
      }
    );
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this task?')) {
      deleteTask.mutate(taskId, {
        onSuccess: () => onClose(),
      });
    }
  };

  const handleAddComment = () => {
    if (newComment.trim()) {
      addComment.mutate(
        { taskId, content: newComment },
        {
          onSuccess: () => setNewComment(''),
        }
      );
    }
  };

  const handleStatusChange = (status: string) => {
    changeStatus.mutate({ taskId, status });
  };

  const handleLogTime = () => {
    if (timeLog.hours > 0) {
      logTime.mutate(
        {
          taskId,
          data: {
            hours: timeLog.hours,
            description: timeLog.description,
            billable: true,
            logged_at: new Date().toISOString(),
          },
        },
        {
          onSuccess: () => setTimeLog({ hours: 0, description: '' }),
        }
      );
    }
  };

  const priorityColors = {
    low: 'bg-gray-100 text-gray-700',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  };

  // Get status value - handle both string and object types
  const getStatusValue = () => {
    if (typeof task.status === 'string') return task.status;
    return task.status?.id || '';
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Task' : task.title}
      size="xl"
    >
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-4">
            {isEditing ? (
              <Input
                value={editedTask.title ?? task.title}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditedTask({ ...editedTask, title: e.target.value })}
                className="text-xl font-semibold"
                placeholder="Task title"
              />
            ) : (
              <h2 className="text-2xl font-bold text-gray-900">{task.title}</h2>
            )}

            <div className="flex items-center gap-2">
              <Select
                value={getStatusValue()}
                onChange={(newStatus: string | string[]) => {
                  if (typeof newStatus === 'string') {
                    handleStatusChange(newStatus);
                  }
                }}
                disabled={isEditing}
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="in_review">In Review</option>
                <option value="done">Done</option>
              </Select>

              <Badge className={priorityColors[task.priority as keyof typeof priorityColors]}>
                {task.priority}
              </Badge>
            </div>
          </div>

          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button onClick={handleSave} disabled={updateTask.isPending}>
                  Save
                </Button>
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  Edit
                </Button>
                <Button
                  variant="outline"
                  onClick={handleDelete}
                  disabled={deleteTask.isPending}
                  className="text-red-600 hover:bg-red-50"
                >
                  Delete
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Description Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Description</h3>
          {isEditing ? (
            <textarea
              value={editedTask.description ?? task.description}
              onChange={(e) => setEditedTask({ ...editedTask, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              placeholder="Task description"
            />
          ) : (
            <p className="text-gray-600">{task.description || 'No description provided'}</p>
          )}
        </div>

        {/* Assignees Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Assignees</h3>
          <div className="flex flex-wrap gap-2">
            {task.assignees?.map((assignee: User) => (
              <div key={assignee.id} className="flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1">
                <Avatar src={assignee.avatar} name={assignee.first_name + ' ' + assignee.last_name} size="sm" />
                <span className="text-sm">{assignee.first_name} {assignee.last_name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Due Date and Tags */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Due Date</h3>
            {isEditing ? (
              <Input
                type="date"
                value={editedTask.due_date ?? task.due_date ?? ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditedTask({ ...editedTask, due_date: e.target.value })}
              />
            ) : (
              <p className="text-gray-600">
                {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}
              </p>
            )}
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {task.tags?.map((tag: string, index: number) => (
                <Badge key={index} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {/* Time Tracking Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Time Tracking</h3>
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                type="number"
                placeholder="Hours"
                value={timeLog.hours || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTimeLog({ ...timeLog, hours: parseFloat(e.target.value) || 0 })}
                className="w-24"
              />
              <Input
                placeholder="Description"
                value={timeLog.description}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTimeLog({ ...timeLog, description: e.target.value })}
                className="flex-1"
              />
              <Button onClick={handleLogTime} disabled={logTime.isPending}>
                Log Time
              </Button>
            </div>

            {timeEntries && timeEntries.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-sm font-medium">
                  Total: {timeEntries.reduce((sum: number, entry: TimeEntry) => sum + entry.hours, 0)} hours
                </p>
                {timeEntries.slice(0, 5).map((entry: TimeEntry, index: number) => (
                  <div key={index} className="text-sm text-gray-600 flex justify-between">
                    <span>{entry.description}</span>
                    <span>{entry.hours}h</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Comments Section */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Comments</h3>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewComment(e.target.value)}
                onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleAddComment()}
                className="flex-1"
              />
              <Button onClick={handleAddComment} disabled={addComment.isPending}>
                Comment
              </Button>
            </div>

            <div className="space-y-3 max-h-64 overflow-y-auto">
              {comments?.map((comment: TaskComment) => (
                <div key={comment.id} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
                  <Avatar src={comment.author?.avatar || comment.user?.avatar} name={comment.author?.name || comment.user?.name || 'User'} size="sm" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">{comment.author?.name || comment.user?.name || 'User'}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(comment.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{comment.content}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};
