'use client'; // Required for SWR and useState/useEffect for modal

import KanbanBoard from '@/components/features/kanban/KanbanBoard';
// import TaskDetailModal from '@/components/features/task/TaskDetailModal'; // To be created
// import TaskQuickAddDialog from '@/components/features/kanban/TaskQuickAddDialog'; // To be created
import { Task } from '@/types/api';
import { useState } from 'react';
import { Button } from '@/components/ui/button'; // For global add task button
import { PlusCircle } from 'lucide-react';
import TaskQuickAddForm from '@/components/features/kanban/TaskQuickAddForm';
import TaskDetailView from '@/components/features/task/TaskDetailView'; // Import TaskDetailView
import { mutate as mutateGlobal } from 'swr'; // Alias mutate to mutateGlobal

export default function DashboardPage() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isTaskDetailOpen, setIsTaskDetailOpen] = useState(false); // State for TaskDetailView
  const [isQuickAddOpen, setIsQuickAddOpen] = useState(false);
  const [quickAddStatus, setQuickAddStatus] = useState<string | undefined>(undefined);

  const handleTaskCardClick = (task: Task) => {
    setSelectedTask(task);
    setIsTaskDetailOpen(true); // Open the TaskDetailView
  };

  const handleOpenQuickAdd = (status?: string) => {
    setQuickAddStatus(status);
    setIsQuickAddOpen(true);
    console.log('Opening quick add for status:', status);
    // This would typically open a dialog/modal for quick task creation
  };

  const handleCloseQuickAdd = () => {
    setIsQuickAddOpen(false);
    setQuickAddStatus(undefined);
  };


  return (
    <div className="h-full flex flex-col"> {/* Ensure page takes full height if Kanban board is to fill space */}
      <div className="flex justify-between items-center mb-4 px-4 pt-4 md:px-0 md:pt-0"> {/* Added padding for mobile, removed for md+ */}
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Task Dashboard</h1>
        <Button onClick={() => handleOpenQuickAdd()} size="sm">
          <PlusCircle size={18} className="mr-1 md:mr-2"/> {/* Adjusted icon margin */}
          Add Task
        </Button>
      </div>

      {/* KanbanBoard itself will have padding for its content */}
      <KanbanBoard
        onTaskClick={handleTaskCardClick}
        onAddTaskClick={handleOpenQuickAdd}
        // projectId={null} // Explicitly null for global dashboard, or pass a specific project ID
      />

      {/* {isTaskDetailModalOpen && selectedTask && (
        <TaskDetailModal
          taskId={selectedTask.id}
          isOpen={isTaskDetailModalOpen}
          onClose={() => setIsTaskDetailModalOpen(false)}
        />
      )} */}

      {/* {isQuickAddOpen && (
        <TaskQuickAddDialog
          isOpen={isQuickAddOpen}
          onClose={handleCloseQuickAdd}
          initialStatus={quickAddStatus}
          // onTaskCreated={() => { mutateTasks(); }} // Assuming mutateTasks is available from SWR in this scope or passed down
        />
      )} */}

      {isQuickAddOpen && (
        <TaskQuickAddForm
          isOpen={isQuickAddOpen}
          onClose={handleCloseQuickAdd}
          initialStatus={quickAddStatus}
          onTaskCreated={(newTask) => {
            mutateGlobal('/tasks'); // Revalidate general tasks list used by KanbanBoard
            if (newTask.project_id) {
              mutateGlobal(`/tasks/?project_id=${newTask.project_id}`);
              // For now, assuming the main '/tasks' mutation might be sufficient if it includes all tasks
              // or if the Kanban board is not filtered by project on the dashboard.
            }
          }}
        />
      )}

      {selectedTask && (
        <TaskDetailView
          taskId={selectedTask.id}
          isOpen={isTaskDetailOpen}
          onClose={() => { setIsTaskDetailOpen(false); setSelectedTask(null); }}
          onTaskUpdated={() => {
            mutateGlobal('/tasks');
            if (selectedTask.project_id) { mutateGlobal(`/tasks/?project_id=${selectedTask.project_id}`); }
          }}
        />
      )}
      <div className="mt-auto p-4 bg-yellow-100 dark:bg-yellow-900/50 border border-yellow-300 dark:border-yellow-700/50 rounded-md text-yellow-700 dark:text-yellow-300 text-xs md:text-sm mx-4 mb-4 md:mx-0 md:mb-0"> {/* Styling for dev note */}
        <p className="font-semibold">Developer Note:</p>
        <ul className="list-disc list-inside">
          <li>Drag-and-drop functionality for tasks will be implemented in the next step.</li>
          <li>Task Detail Modal and Quick Add Task Dialog are placeholders and will be implemented later.</li>
        </ul>
      </div>
    </div>
  );
}
