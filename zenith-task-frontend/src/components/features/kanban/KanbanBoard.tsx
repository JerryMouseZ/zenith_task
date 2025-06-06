'use client';

import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';
import { Task, TaskReorderItem } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import KanbanColumn, { KanbanColumnData } from './KanbanColumn';
import KanbanCard from './KanbanCard'; // For DragOverlay
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Loader2, PlusCircle } from 'lucide-react';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners, // Using closestCorners for now, can test rectIntersection
  // rectIntersection,
} from '@dnd-kit/core';
import { SortableContext, horizontalListSortingStrategy, arrayMove, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { createPortal } from 'react-dom';
import TaskDetailModal from '@/components/features/task/TaskDetailModal';

// Define your columns
const defaultColumns: KanbanColumnData[] = [
  { id: 'todo', title: 'To Do' },
  { id: 'inprogress', title: 'In Progress' },
  { id: 'done', title: 'Done' },
];

const tasksFetcher = (url: string) => apiClient.get<Task[]>(url);

interface KanbanBoardProps {
  projectId?: number | null;
  // onTaskClick is now handled internally to open the modal
  onAddTaskClick?: (status?: string) => void;
}

export default function KanbanBoard({ projectId, onAddTaskClick }: KanbanBoardProps) {
  const tasksUrl = projectId ? `/tasks/?project_id=${projectId}` : '/tasks'; // Corrected URL
  const { data: fetchedTasks, error, isLoading: tasksAreLoadingSWR, mutate: mutateSWRTasks } = useSWR<Task[]>(tasksUrl, tasksFetcher);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [columns, setColumns] = useState<KanbanColumnData[]>(defaultColumns);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [activeColumn, setActiveColumn] = useState<KanbanColumnData | null>(null);
  const [selectedTaskIdForModal, setSelectedTaskIdForModal] = useState<number | null>(null);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

  useEffect(() => {
    if (fetchedTasks) {
      setTasks(fetchedTasks);
    }
  }, [fetchedTasks]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 10, // pixels, increased from 3
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const tasksByColumn = useMemo(() => {
    const grouped: { [key: string]: Task[] } = {};
    columns.forEach(col => grouped[col.id] = []);
    tasks.forEach((task) => {
      const status = task.status && columns.find(c => c.id === task.status) ? task.status : 'todo';
      grouped[status].push(task);
    });
    for (const colId in grouped) {
      // Sort by order_in_list, then by ID for stable sort if order_in_list is same or null
      grouped[colId].sort((a, b) => {
        const orderA = a.order_in_list ?? Infinity;
        const orderB = b.order_in_list ?? Infinity;
        if (orderA === orderB) {
          return a.id - b.id; // Assuming id is a number
        }
        return orderA - orderB;
      });
    }
    return grouped;
  }, [tasks, columns]);

  const handleTaskCardClick = (taskId: number) => {
    setSelectedTaskIdForModal(taskId);
    setIsTaskModalOpen(true);
  };


  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    if (active.data.current?.type === 'Task') {
      setActiveTask(active.data.current.task);
    }
    // Column dragging not implemented in this version
    // if (active.data.current?.type === 'Column') {
    //   setActiveColumn(active.data.current.column);
    // }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const isActiveTask = active.data.current?.type === 'Task';
    if (!isActiveTask) return;

    const activeTaskData = active.data.current?.task as Task;
    const overId = over.id;
    const overData = over.data.current;

    // Determine the target column ID
    let targetColumnId = overData?.type === 'Column' ? overId as string : overData?.task.status;
    if (!targetColumnId) return;


    setTasks(prevTasks => {
      const activeIndex = prevTasks.findIndex(t => t.id === active.id);
      if (activeIndex === -1) return prevTasks;

      let newTasks = [...prevTasks];
      const draggedTask = { ...newTasks[activeIndex], status: targetColumnId };

      newTasks.splice(activeIndex, 1); // Remove dragged task

      // Find the index to insert in the target column
      let overTaskIndexInAllTasks = -1;
      if (overData?.type === 'Task') {
         overTaskIndexInAllTasks = newTasks.findIndex(t => t.id === overData.task.id);
      } else { // Dropping on a column
        // Find the last task in the target column or set to end of list if column is empty
        const tasksInTargetColumn = newTasks.filter(t => t.status === targetColumnId);
        if (tasksInTargetColumn.length > 0) {
            overTaskIndexInAllTasks = newTasks.findIndex(t => t.id === tasksInTargetColumn[tasksInTargetColumn.length -1].id) +1;
        } else {
            overTaskIndexInAllTasks = newTasks.length; // add to the end if column is empty
        }
      }

      if (overTaskIndexInAllTasks !== -1) {
          newTasks.splice(overTaskIndexInAllTasks, 0, draggedTask);
      } else {
          // Fallback: if overTask is not found (e.g. dropping in empty space of a column not at the end)
          // just add to the list, status already updated. Sorting will fix later.
          // Or, find the column's tasks and insert based on relative position to over.rect
          newTasks.push(draggedTask);
      }
      return newTasks;
    });
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const isActiveTask = active.data.current?.type === 'Task';
    if (!isActiveTask) return;

    const activeTaskId = active.id as number;
    // originalTask is from fetchedTasks, representing state before any drag operations in this session
    const originalTaskFromFetch = fetchedTasks?.find(t => t.id === activeTaskId);
    if (!originalTaskFromFetch) return; // Should not happen if tasks are loaded

    // Determine the target status for the dragged task
    let targetStatus = active.data.current?.task.status; // Initial status of the dragged task
    const overData = over.data.current;
    if (overData?.type === 'Column') {
      targetStatus = over.id as string;
    } else if (overData?.type === 'Task') {
      targetStatus = overData.task.status; // Task is dropped onto another task, inherits its status
    }

    // `tasks` state is already updated by `handleDragOver` to reflect the visual position.
    // Now, ensure the status of the dragged task is correctly set in our local `tasks` copy.
    let currentTasksSnapshot = [...tasks];
    const activeTaskIndex = currentTasksSnapshot.findIndex(t => t.id === activeTaskId);

    if (activeTaskIndex !== -1) {
      if (currentTasksSnapshot[activeTaskIndex].status !== targetStatus) {
        currentTasksSnapshot[activeTaskIndex] = {
          ...currentTasksSnapshot[activeTaskIndex],
          status: targetStatus,
        };
      }
    } else {
      // This case should ideally not happen if handleDragOver is robust
      console.warn('Active task not found in current snapshot during drag end.');
      return;
    }
    
    // Regenerate the final ordered list based on the snapshot that includes the correct status for the dragged item
    // This step is crucial if changing status also implies moving between visual groups that handleDragOver might not fully resolve.
    // For now, we assume handleDragOver has placed it in the correct visual list, and we've just updated its status.

    const reorderPayload: TaskReorderItem[] = [];
    const tasksGroupedByFinalStatus: { [key: string]: Task[] } = {};

    currentTasksSnapshot.forEach(task => {
      const statusIsValid = defaultColumns.some(col => col.id === task.status);
      const status = (task.status && statusIsValid) ? task.status : defaultColumns[0].id;
      if (!tasksGroupedByFinalStatus[status]) {
        tasksGroupedByFinalStatus[status] = [];
      }
      tasksGroupedByFinalStatus[status].push(task);
    });

    Object.keys(tasksGroupedByFinalStatus).forEach(statusKey => {
      tasksGroupedByFinalStatus[statusKey].forEach((task, index) => {
        reorderPayload.push({
          task_id: task.id,
          new_status: statusKey,
          new_order_in_list: index,
        });
      });
    });

    let changeOccurred = false;
    if (!fetchedTasks || reorderPayload.length !== fetchedTasks.length) {
      changeOccurred = true; 
    } else {
      const originalTaskStateMap = new Map<number, { status: string; order: number }>();
      const originalGroupedByStatus: { [key: string]: Task[] } = {};

      (fetchedTasks || []).forEach(ot => {
        const statusIsValid = defaultColumns.some(col => col.id === ot.status);
        const status = (ot.status && statusIsValid) ? ot.status : defaultColumns[0].id;
        if (!originalGroupedByStatus[status]) {
          originalGroupedByStatus[status] = [];
        }
        originalGroupedByStatus[status].push(ot);
      });

      Object.keys(originalGroupedByStatus).forEach(statusKey => {
        originalGroupedByStatus[statusKey]
          .sort((a, b) => (a.order_in_list ?? Infinity) - (b.order_in_list ?? Infinity))
          .forEach((task, index) => {
            originalTaskStateMap.set(task.id, { status: statusKey, order: index });
          });
      });

      for (const item of reorderPayload) {
        const originalState = originalTaskStateMap.get(item.task_id);
        if (!originalState || originalState.status !== item.new_status || originalState.order !== item.new_order_in_list) {
          changeOccurred = true;
          break;
        }
      }
    }

    if (changeOccurred) {
      // The `tasks` state was already updated optimistically by `handleDragOver` and potentially refined above.
      // No need to call setTasks(currentTasksSnapshot) again unless it was further modified here.
      try {
        console.log('Submitting task reorder payload:', reorderPayload);
        await apiClient.put<unknown, TaskReorderItem[]>('/tasks/reorder', reorderPayload);
        mutateSWRTasks(); // Revalidate SWR cache to get authoritative state
      } catch (apiError) {
        console.error('Failed to reorder tasks:', apiError);
        setTasks(fetchedTasks || []); // Revert optimistic update to last known good state
        // TODO: Show an error toast/message to the user
      }
    }
  };

  if (tasksAreLoadingSWR && !fetchedTasks) {
    return ( <div className="flex justify-center items-center py-20"><Loader2 className="h-12 w-12 animate-spin text-primary" /></div> );
  }
  if (error) {
  return (
    <div className="flex justify-center items-center py-20">
      <Loader2 className="h-12 w-12 animate-spin text-primary" />
    </div>
  );
}
if (error) {
  return (
    <Alert variant="destructive" className="my-4">
      <AlertTitle>Error Loading Tasks</AlertTitle>
      <AlertDescription>{error.message || 'An unknown error occurred.'}</AlertDescription>
    </Alert>
  );
}

if (!fetchedTasks && !tasksAreLoadingSWR && !error) { // After loading and no error, if fetchedTasks is still undefined (e.g. API returns null)
    return (
      <div className="text-center py-10">
        <p className="text-lg text-muted-foreground">No task data available.</p>
      </div>
    );
}

// If tasks are loaded (or fetchedTasks is an empty array) but tasks state is empty (e.g. after filtering or if project has no tasks)
if (tasks.length === 0 && !tasksAreLoadingSWR) { 
  return (
    <div className="text-center py-10">
      <p className="text-lg text-muted-foreground">No tasks to display for this project.</p>
      {/* Optionally, add a button or prompt to create the first task */}
      {onAddTaskClick && projectId && (
        <Button onClick={() => onAddTaskClick('todo')} className="mt-4">
          <PlusCircle className="mr-2 h-4 w-4" /> Add New Task
        </Button>
      )}
    </div>
  );
}

return (
  <DndContext
    sensors={sensors}
    collisionDetection={closestCorners}
    onDragStart={handleDragStart}
    onDragOver={handleDragOver}
    onDragEnd={handleDragEnd}
  >
    <div className="flex space-x-4 overflow-x-auto p-1 pb-4 h-[calc(100vh-200px)] items-start pretty-scrollbar">
      <SortableContext items={columns.map(c => c.id)} strategy={horizontalListSortingStrategy}>
        {columns.map((column) => (
          <KanbanColumn
            key={column.id}
            column={column}
            tasks={tasksByColumn[column.id] || []}
            onCardClick={(task) => handleTaskCardClick(task.id)}
            onAddTaskClick={(status) => onAddTaskClick?.(status)} // Pass down onAddTaskClick
          />
        ))}
      </SortableContext>
    </div>

    {typeof document !== 'undefined' && createPortal(
      <DragOverlay dropAnimation={null}>
        {activeTask ? <KanbanCard task={activeTask} isOverlay /> : null}
      </DragOverlay>,
      document.body
    )}

    <TaskDetailModal
      taskId={selectedTaskIdForModal}
      isOpen={isTaskModalOpen}
      onOpenChange={setIsTaskModalOpen}
      // onTaskUpdated={() => mutateSWRTasks()} // Optional: to force re-fetch/re-render of board tasks
    />
  </DndContext>
);
}
