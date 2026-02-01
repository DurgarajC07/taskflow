import { Calendar, MessageSquare, Paperclip, User } from 'lucide-react';
import type { Task } from '../types';
import { colors, spacing, shadows, borderRadius } from '../../../lib/design-tokens';

interface TaskCardProps {
  task: Task;
  onClick?: (task: Task) => void;
  isDragging?: boolean;
}

export const TaskCard = ({ task, onClick, isDragging }: TaskCardProps) => {
  const getPriorityColor = (priority: Task['priority']) => {
    const priorityColors = {
      lowest: colors.neutral[400],
      low: colors.brand[500],
      medium: colors.warning[500],
      high: colors.warning[600],
      highest: colors.error[600],
    };
    return priorityColors[priority];
  };

  return (
    <div
      onClick={() => onClick?.(task)}
      style={{
        backgroundColor: 'white',
        border: `1px solid ${colors.neutral[200]}`,
        borderLeft: `3px solid ${getPriorityColor(task.priority)}`,
        borderRadius: borderRadius.md,
        padding: spacing[4],
        cursor: 'pointer',
        transition: 'all 150ms',
        boxShadow: isDragging ? shadows.lg : shadows.sm,
        opacity: isDragging ? 0.5 : 1,
      }}
      onMouseEnter={(e) => {
        if (!isDragging) {
          e.currentTarget.style.boxShadow = shadows.md;
          e.currentTarget.style.transform = 'translateY(-2px)';
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = shadows.sm;
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div style={{ marginBottom: spacing[2] }}>
        <span
          style={{
            fontSize: '0.75rem',
            color: colors.neutral[500],
            fontWeight: 500,
          }}
        >
          {task.taskKey}
        </span>
      </div>

      <h4
        style={{
          fontSize: '0.875rem',
          fontWeight: 500,
          color: colors.neutral[900],
          marginBottom: spacing[3],
          lineHeight: 1.5,
        }}
      >
        {task.title}
      </h4>

      {task.labels.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: spacing[2],
            marginBottom: spacing[3],
          }}
        >
          {task.labels.slice(0, 3).map((label, index) => (
            <span
              key={index}
              style={{
                fontSize: '0.6875rem',
                padding: `${spacing[1]} ${spacing[2]}`,
                backgroundColor: colors.brand[100],
                color: colors.brand[700],
                borderRadius: borderRadius.base,
                fontWeight: 500,
              }}
            >
              {label}
            </span>
          ))}
          {task.labels.length > 3 && (
            <span
              style={{
                fontSize: '0.6875rem',
                padding: `${spacing[1]} ${spacing[2]}`,
                color: colors.neutral[600],
              }}
            >
              +{task.labels.length - 3}
            </span>
          )}
        </div>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          color: colors.neutral[500],
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing[3] }}>
          {task.assignee && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: spacing[1],
              }}
            >
              {task.assignee.avatar ? (
                <img
                  src={task.assignee.avatar}
                  alt={task.assignee.name}
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: borderRadius.full,
                  }}
                />
              ) : (
                <User size={16} />
              )}
            </div>
          )}

          {task.commentsCount > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: spacing[1] }}>
              <MessageSquare size={14} />
              <span>{task.commentsCount}</span>
            </div>
          )}

          {task.attachmentsCount > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: spacing[1] }}>
              <Paperclip size={14} />
              <span>{task.attachmentsCount}</span>
            </div>
          )}
        </div>

        {task.dueDate && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: spacing[1],
              color: new Date(task.dueDate) < new Date() ? colors.error[600] : colors.neutral[500],
            }}
          >
            <Calendar size={14} />
            <span>{new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
          </div>
        )}
      </div>
    </div>
  );
};
