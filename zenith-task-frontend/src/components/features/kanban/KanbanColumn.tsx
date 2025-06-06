'use client';

import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Task } from '@/types/api';
import KanbanCard from './KanbanCard';
import { PlusCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface KanbanColumnData {
  id: string; // e.g., 'todo', 'inprogress', 'done'
  title: string;
}

interface KanbanColumnProps {
  column: KanbanColumnData;
  tasks: Task[];
  onCardClick: (task: Task) => void;
  onAddTaskClick?: (status: string) => void; // To open quick add form with pre-filled status
}

export default function KanbanColumn({ column, tasks, onCardClick, onAddTaskClick }: KanbanColumnProps) {
  const {
    setNodeRef,
    attributes, // For dragging entire column (optional)
    listeners,  // For dragging entire column (optional)
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: column.id,
    data: { type: 'Column', column },
    // disabled: true, // Disable dragging columns for now
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.8 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      // {...attributes} // Spread if columns are draggable. Ensure listeners are on a specific drag handle if so.
      className="flex flex-col w-80 min-w-[20rem] max-w-xs bg-gray-100 dark:bg-slate-900/70 rounded-lg shadow-md h-full max-h-full"
    >
      <div
        // {...listeners} // Example: make the header the drag handle for the column
        className="flex justify-between items-center p-3 sticky top-0 bg-gray-100 dark:bg-slate-900/70 rounded-t-lg z-10 border-b border-gray-200 dark:border-slate-700/50"
      >
        <h3 className="font-semibold text-gray-800 dark:text-gray-200">{column.title} <span className="text-sm text-gray-500 dark:text-gray-400">({tasks.length})</span></h3>
        {onAddTaskClick && (
          <Button variant="ghost" size="icon" onClick={() => onAddTaskClick(column.id)} className="text-gray-500 hover:text-primary h-7 w-7">
            <PlusCircle size={18} />
          </Button>
        )}
      </div>

      {/* Ensure this div takes remaining height and scrolls its content */}
      <div className="flex-grow overflow-y-auto p-2 space-y-0.5 pretty-scrollbar"> {/* Added pretty-scrollbar if defined globally */}
        <SortableContext items={tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <KanbanCard key={task.id} task={task} onClick={onCardClick} />
          ))}
          {/* Render a minimum height if no tasks, to ensure column is a valid drop target */}
          {tasks.length === 0 && (
            <div className="min-h-[50px]"></div>
          )}
        </SortableContext>
      </div>
    </div>
  );
}
