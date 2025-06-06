'use client';

import { useEffect, useMemo, useState } from 'react';
import useSWR, { mutate as globalMutate } from 'swr'; // use globalMutate for reordering API call
import { Task, Project, TaskReorderItem } from '@/types/api'; // Project is not used, TaskReorderItem is new
import { apiClient } from '@/lib/apiClient';
import KanbanColumn, { KanbanColumnData } from './KanbanColumn';
import KanbanCard from './KanbanCard'; // For DragOverlay
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
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

// Define your columns
const defaultColumns: KanbanColumnData[] = [
  { id: 'todo', title: 'To Do' },
  { id: 'inprogress', title: 'In Progress' },
  { id: 'done', title: 'Done' },
];

const tasksFetcher = (url: string) => apiClient.get<Task[]>(url);

interface KanbanBoardProps {
  projectId?: number | null;
  onTaskClick?: (task: Task) => void;
  onAddTaskClick?: (status?: string) => void;
}

export default function KanbanBoard({ projectId, onTaskClick, onAddTaskClick }: KanbanBoardProps) {
  const tasksUrl = projectId ? `/tasks/?project_id=${projectId}` : '/tasks'; // Corrected URL
  const { data: fetchedTasks, error, isLoading: tasksAreLoadingSWR, mutate: mutateSWRTasks } = useSWR<Task[]>(tasksUrl, tasksFetcher);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [columns, setColumns] = useState<KanbanColumnData[]>(defaultColumns);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [activeColumn, setActiveColumn] = useState<KanbanColumnData | null>(null);

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
    // setActiveColumn(null); // For column dragging

    if (!over) return;

    const isActiveTask = active.data.current?.type === 'Task';
    if (!isActiveTask) return;

    const activeTaskId = active.id as number;
    const originalTask = fetchedTasks?.find(t => t.id === activeTaskId);
    if (!originalTask) return;

    let newStatus = originalTask.status;

    // Determine the final column ID
    const overData = over.data.current;
    if (overData?.type === 'Column') {
        newStatus = over.id as string;
    } else if (overData?.type === 'Task') {
        newStatus = overData.task.status;
    }

    // Optimistically update the tasks state for immediate UI feedback
    // The order_in_list will be based on the final sorted order in 'tasks' state
    let finalTasksState = [...tasks]; // Use the current tasks state which reflects dragOver changes
    const draggedTaskIndex = finalTasksState.findIndex(t => t.id === activeTaskId);

    if (draggedTaskIndex !== -1) {
      finalTasksState[draggedTaskIndex] = {
        ...finalTasksState[draggedTaskIndex],
        status: newStatus,
      };

      // Re-calculate order for all tasks in affected columns or all tasks if simpler
      // For now, we'll assume the backend handles final order calculation based on the list of operations
      // Or, we send the whole new order for each affected column.
    }

    // Create the payload for the API
    // This simplified version sends only the changed task.
    // A more robust version would send all tasks that had their order_in_list or status changed.
    // For now, the backend /tasks/reorder is expected to handle a list of TaskReorderItem.
    // Let's build a list of all tasks with their new status and order.

    const tasksInFinalStatus = finalTasksState.filter(t => t.status === newStatus);
    const newOrderInListForActiveTask = tasksInFinalStatus.findIndex(t => t.id === activeTaskId);

    const reorderPayload: TaskReorderItem[] = [{
      task_id: activeTaskId,
      new_status: newStatus,
      new_order_in_list: newOrderInListForActiveTask,
    }];

    // If other tasks in the original column or new column were shifted, they also need their order_in_list updated.
    // This part is crucial and complex. For now, the backend is assumed to re-index the affected columns based on the one moved task.
    // A more complete frontend would calculate all affected tasks.
    // Let's refine this: the backend should ideally accept a list of task_ids in their new order for a given status.
    // Or the TaskReorderItem[] should include all tasks whose order_in_list or status changed.

    // Simplified: If the task actually moved or changed status
    if (newStatus !== originalTask.status || tasks.findIndex(t=>t.id === activeTaskId) !== fetchedTasks?.findIndex(t=>t.id === activeTaskId) ) {
       setTasks(finalTasksState); // Update UI optimistically
      try {
        console.log('Reordering tasks with payload:', reorderPayload);
        // The API should be designed to re-calculate order_in_list for affected columns
        await apiClient.put<unknown, TaskReorderItem[]>('/tasks/reorder', reorderPayload); // Assuming the endpoint name
        mutateSWRTasks(); // Revalidate SWR cache from server to get authoritative state
      } catch (apiError) {
        console.error('Failed to reorder tasks:', apiError);
        setTasks(fetchedTasks || []); // Revert to original tasks from SWR on error
        // Consider showing an error toast/message to the user
      }
    }
  };

  if (tasksAreLoadingSWR && !fetchedTasks) {
    return ( <div className="flex justify-center items-center py-20"><Loader2 className="h-12 w-12 animate-spin text-primary" /></div> );
  }
  if (error) {
    return ( <Alert variant="destructive" className="my-4"><AlertTitle>Error Loading Tasks</AlertTitle><AlertDescription>{error.message || 'An unknown error occurred.'}</AlertDescription></Alert> );
  }
   if (!tasks || tasks.length === 0 && !tasksAreLoadingSWR) { // Check tasks.length after initial load attempt
    return (
      <div className="text-center py-10">
        <p className="text-lg text-muted-foreground">No tasks found for this view.</p>
         {projectId === undefined && <p className="text-sm text-muted-foreground">Get started by adding a task.</p>}
         {projectId !== undefined && <p className="text-sm text-muted-foreground">Add tasks to this project to see them here.</p>}
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
              onCardClick={(task) => onTaskClick?.(task)}
              onAddTaskClick={(status) => onAddTaskClick?.(status)}
            />
          ))}
        </SortableContext>
      </div>
      {typeof document !== 'undefined' && createPortal(
        <DragOverlay dropAnimation={null}>
          {activeTask ? <KanbanCard task={activeTask} /> : null}
          {/* Column dragging overlay (if implemented) */}
          {/* {activeColumn ? <KanbanColumn column={activeColumn} tasks={tasksByColumn[activeColumn.id] || []} onCardClick={() => {}} /> : null} */}
        </DragOverlay>,
        document.body
      )}
    </DndContext>
  );
}
