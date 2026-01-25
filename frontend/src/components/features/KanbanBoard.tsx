import { useState } from 'react';
import { Plus } from 'lucide-react';
import TaskCard from './TaskCard';
import { cn } from '@/lib/utils';

interface Task {
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
}

interface Column {
  id: string;
  title: string;
  tasks: Task[];
  color?: string;
}

interface KanbanBoardProps {
  columns: Column[];
  onTaskMove?: (taskId: string, fromColumn: string, toColumn: string) => void;
  onTaskClick?: (task: Task) => void;
  onAddTask?: (columnId: string) => void;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({
  columns,
  onTaskMove,
  onTaskClick,
  onAddTask,
}) => {
  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [draggedOverColumn, setDraggedOverColumn] = useState<string | null>(null);

  const handleDragStart = (taskId: string) => {
    setDraggedTask(taskId);
  };

  const handleDragEnd = () => {
    setDraggedTask(null);
    setDraggedOverColumn(null);
  };

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    setDraggedOverColumn(columnId);
  };

  const handleDrop = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain');
    
    // Find which column the task came from
    const fromColumn = columns.find((col) =>
      col.tasks.some((task) => task.id === taskId)
    );

    if (fromColumn && fromColumn.id !== columnId && onTaskMove) {
      onTaskMove(taskId, fromColumn.id, columnId);
    }

    setDraggedTask(null);
    setDraggedOverColumn(null);
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-4 h-[calc(100vh-200px)]">
      {columns.map((column) => (
        <div
          key={column.id}
          className="flex-shrink-0 w-80 bg-gray-50 rounded-lg p-4"
          onDragOver={(e) => handleDragOver(e, column.id)}
          onDrop={(e) => handleDrop(e, column.id)}
        >
          {/* Column Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {column.color && (
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: column.color }}
                />
              )}
              <h3 className="font-semibold text-gray-900">{column.title}</h3>
              <span className="text-sm text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                {column.tasks.length}
              </span>
            </div>
            <button
              onClick={() => onAddTask?.(column.id)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
            >
              <Plus className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          {/* Tasks */}
          <div
            className={cn(
              'space-y-3 min-h-[200px] transition-colors',
              draggedOverColumn === column.id && 'bg-blue-50 rounded-lg'
            )}
          >
            {column.tasks.length > 0 ? (
              column.tasks.map((task) => (
                <TaskCard
                  key={task.id}
                  {...task}
                  onClick={() => onTaskClick?.(task)}
                  onDragStart={() => handleDragStart(task.id)}
                  onDragEnd={handleDragEnd}
                  className={cn(
                    draggedTask === task.id && 'opacity-50'
                  )}
                />
              ))
            ) : (
              <div className="text-center py-8 text-sm text-gray-400">
                Drop tasks here
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default KanbanBoard;
