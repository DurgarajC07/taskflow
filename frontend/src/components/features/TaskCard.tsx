import { Calendar, MessageSquare, Paperclip, MoreVertical } from 'lucide-react';
import { Card, Avatar, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';

interface TaskCardProps {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignees?: Array<{ id: string; name: string; avatar?: string }>;
  dueDate?: string;
  commentsCount?: number;
  attachmentsCount?: number;
  labels?: Array<{ id: string; name: string; color: string }>;
  onClick?: () => void;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
  className?: string;
}

const TaskCard: React.FC<TaskCardProps> = ({
  id,
  title,
  description,
  priority,
  assignees = [],
  dueDate,
  commentsCount = 0,
  attachmentsCount = 0,
  labels = [],
  onClick,
  onDragStart,
  onDragEnd,
  className,
}) => {
  const priorityColors = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    critical: 'danger',
  } as const;

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', id);
    if (onDragStart) onDragStart(e);
  };

  return (
    <Card
      variant="bordered"
      padding="md"
      hoverable
      draggable
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      onClick={onClick}
      className={cn('cursor-pointer group', className)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <Badge variant={priorityColors[priority]} size="sm">
          {priority}
        </Badge>
        <button
          onClick={(e) => {
            e.stopPropagation();
            // Handle menu click
          }}
          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded transition-opacity"
        >
          <MoreVertical className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-gray-900 mb-2 line-clamp-2">
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-xs text-gray-600 mb-3 line-clamp-2">{description}</p>
      )}

      {/* Labels */}
      {labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {labels.map((label) => (
            <span
              key={label.id}
              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
              style={{
                backgroundColor: `${label.color}20`,
                color: label.color,
              }}
            >
              {label.name}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
        {/* Left side - Metadata */}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {dueDate && (
            <div className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>{dueDate}</span>
            </div>
          )}
          {commentsCount > 0 && (
            <div className="flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>{commentsCount}</span>
            </div>
          )}
          {attachmentsCount > 0 && (
            <div className="flex items-center gap-1">
              <Paperclip className="w-3.5 h-3.5" />
              <span>{attachmentsCount}</span>
            </div>
          )}
        </div>

        {/* Right side - Assignees */}
        {assignees.length > 0 && (
          <div className="flex -space-x-2">
            {assignees.slice(0, 3).map((assignee) => (
              <Avatar
                key={assignee.id}
                src={assignee.avatar}
                name={assignee.name}
                size="xs"
                className="ring-2 ring-white"
              />
            ))}
            {assignees.length > 3 && (
              <div className="w-6 h-6 rounded-full bg-gray-200 ring-2 ring-white flex items-center justify-center text-xs font-medium text-gray-600">
                +{assignees.length - 3}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default TaskCard;
