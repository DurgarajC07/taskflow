import { Users, Calendar, CheckCircle, MoreVertical } from 'lucide-react';
import { Card, Avatar, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';

interface ProjectCardProps {
  id: string;
  name: string;
  description?: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'archived';
  progress?: number;
  team?: any;
  start_date?: string;
  end_date?: string;
  onClick?: () => void;
  className?: string;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  name,
  description,
  status,
  progress = 0,
  end_date,
  onClick,
  className,
}) => {
  const statusMap = {
    planning: { label: 'Planning', variant: 'default' as const },
    active: { label: 'Active', variant: 'success' as const },
    on_hold: { label: 'On Hold', variant: 'warning' as const },
    completed: { label: 'Completed', variant: 'info' as const },
    archived: { label: 'Archived', variant: 'default' as const },
  };

  const statusInfo = statusMap[status] || statusMap.planning;

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
          <Badge variant={statusInfo.variant} size="sm">
            {statusInfo.label}
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
      {progress > 0 && (
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
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm">
        {end_date && (
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">
              {new Date(end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ProjectCard;
