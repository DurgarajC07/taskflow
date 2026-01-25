import { Users, Calendar, CheckCircle, MoreVertical } from 'lucide-react';
import { Card, Avatar, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';

interface ProjectCardProps {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'on-hold' | 'completed';
  progress: number;
  members: Array<{ id: string; name: string; avatar?: string }>;
  tasksTotal: number;
  tasksCompleted: number;
  dueDate?: string;
  onClick?: () => void;
  className?: string;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  _id,
  name,
  description,
  status,
  progress,
  members,
  tasksTotal,
  tasksCompleted,
  dueDate,
  onClick,
  className,
}) => {
  const statusColors = {
    active: 'success',
    'on-hold': 'warning',
    completed: 'info',
  } as const;

  return (
    <Card
      variant="bordered"
      padding="lg"
      hoverable
      onClick={onClick}
      className={cn('cursor-pointer group', className)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{name}</h3>
          <Badge variant={statusColors[status]} size="sm">
            {status}
          </Badge>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            // Handle menu
          }}
          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded transition-opacity"
        >
          <MoreVertical className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Description */}
      {description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{description}</p>
      )}

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-gray-600">Progress</span>
          <span className="font-medium text-gray-900">{progress}%</span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4 pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2 text-sm">
          <CheckCircle className="w-4 h-4 text-gray-500" />
          <span className="text-gray-600">
            {tasksCompleted}/{tasksTotal} Tasks
          </span>
        </div>
        {dueDate && (
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">{dueDate}</span>
          </div>
        )}
      </div>

      {/* Footer - Team Members */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">{members.length} members</span>
        </div>
        <div className="flex -space-x-2">
          {members.slice(0, 5).map((member) => (
            <Avatar
              key={member.id}
              src={member.avatar}
              name={member.name}
              size="sm"
              className="ring-2 ring-white"
            />
          ))}
          {members.length > 5 && (
            <div className="w-8 h-8 rounded-full bg-gray-200 ring-2 ring-white flex items-center justify-center text-xs font-medium text-gray-600">
              +{members.length - 5}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default ProjectCard;
