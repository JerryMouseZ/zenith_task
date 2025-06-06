'use client';

import { Task } from '@/types/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge'; // For priority or tags
import { GripVertical, MessageSquare, Paperclip, CalendarDays } from 'lucide-react'; // Icons
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface KanbanCardProps {
  task: Task;
  onClick?: (task: Task) => void; // For opening task detail modal
}

export default function KanbanCard({ task, onClick }: KanbanCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id, data: { type: 'Task', task } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    // cursor: 'grab', // Managed by dnd-kit
  };

  const priorityMap: { [key: number]: string } = {
    0: 'Low',
    1: 'Medium',
    2: 'High',
    3: 'Urgent',
  };
  const priorityColorMap: { [key: number]: string } = { // Tailwind CSS classes
    0: 'bg-sky-500 hover:bg-sky-600',      // Blue for Low
    1: 'bg-yellow-500 hover:bg-yellow-600',// Yellow for Medium
    2: 'bg-orange-500 hover:bg-orange-600',// Orange for High
    3: 'bg-red-600 hover:bg-red-700',      // Red for Urgent
  };


  return (
    <div ref={setNodeRef} style={style} {...attributes} >
      <Card
        className="mb-3 bg-white dark:bg-slate-800 shadow-sm hover:shadow-md transition-shadow duration-150 cursor-pointer" // Added cursor-pointer
        onClick={() => onClick?.(task)}
      >
        <CardHeader className="p-3">
          <div className="flex justify-between items-start">
            <CardTitle className="text-sm font-medium leading-tight line-clamp-2 mr-1">{task.title}</CardTitle> {/* Added mr-1 for spacing from handle */}
            <button {...listeners} className="cursor-grab p-1 -mr-1 -mt-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 flex-shrink-0"> {/* Handle styling */}
              <GripVertical size={16} />
            </button>
          </div>
          {task.description && (
            <CardDescription className="text-xs mt-1 line-clamp-2">{task.description}</CardDescription>
          )}
        </CardHeader>
        {(task.priority !== null && typeof task.priority !== 'undefined') || task.due_date ? ( // Render CardContent only if there's content
            <CardContent className="p-3 text-xs space-y-2">
            {task.priority !== null && typeof task.priority !== 'undefined' && (
                <Badge variant="secondary" className={`mr-1 ${priorityColorMap[task.priority]} text-white text-xs px-1.5 py-0.5`}> {/* Adjusted padding/size */}
                    {priorityMap[task.priority]}
                </Badge>
            )}
            {task.due_date && (
                <div className="flex items-center text-muted-foreground">
                <CalendarDays size={14} className="mr-1" />
                <span>{new Date(task.due_date).toLocaleDateString()}</span>
                </div>
            )}
            {/* Placeholder for tags, subtasks count, attachments etc. */}
            {/* {task.tags && task.tags.length > 0 && (
                <div className="flex items-center text-muted-foreground">
                <Paperclip size={14} className="mr-1" />
                <span>{task.tags.length} tags</span>
                </div>
            )} */}
            </CardContent>
        ) : null}
        {/* <CardFooter className="p-2 text-xs flex justify-between items-center">
          <div>Assignee Placeholder</div>
          <div className="flex items-center text-muted-foreground">
            <MessageSquare size={14} className="mr-1" /> 0
          </div>
        </CardFooter> */}
      </Card>
    </div>
  );
}
