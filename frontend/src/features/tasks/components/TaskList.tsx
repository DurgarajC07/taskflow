import type { Task } from '../types';
import { TaskCard } from './TaskCard';
import { spacing, colors } from '../../../lib/design-tokens';

interface TaskListProps {
  tasks: Task[];
  isLoading?: boolean;
  onTaskClick?: (task: Task) => void;
  emptyMessage?: string;
}

export const TaskList = ({
  tasks,
  isLoading,
  onTaskClick,
  emptyMessage = 'No tasks found',
}: TaskListProps) => {
  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing[3] }}>
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            style={{
              height: '120px',
              backgroundColor: colors.neutral[100],
              borderRadius: '0.5rem',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}
          />
        ))}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div
        style={{
          textAlign: 'center',
          padding: spacing[12],
          color: colors.neutral[500],
        }}
      >
        <p style={{ fontSize: '0.875rem' }}>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing[3] }}>
      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} onClick={onTaskClick} />
      ))}
    </div>
  );
};
