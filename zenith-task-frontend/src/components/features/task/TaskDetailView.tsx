'use client';

import { useState, useEffect } from 'react';
import useSWR, { mutate } from 'swr';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Task, Project } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import TaskForm from './TaskForm';
import { Loader2, Edit, CalendarDays, TagIcon as TagIconLucide, Users, Paperclip, ListChecks } from 'lucide-react'; // Renamed TagIcon to TagIconLucide
import { format, parseISO, isValid } from 'date-fns'; // For date display

interface TaskDetailViewProps {
  taskId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onTaskUpdated?: () => void;
}

const taskFetcher = (url: string) => apiClient.get<Task>(url);
const projectFetcher = (url: string) => url ? apiClient.get<Project>(url) : Promise.resolve(null);

const priorityMap: { [key:number]: string } = { 0: 'Low', 1: 'Medium', 2: 'High', 3: 'Urgent' };
const priorityColorMap: { [key:number]: string } = { // Tailwind classes
    0: 'bg-sky-500 hover:bg-sky-600',
    1: 'bg-yellow-500 hover:bg-yellow-600',
    2: 'bg-orange-500 hover:bg-orange-600',
    3: 'bg-red-600 hover:bg-red-700',
};
const statusDisplayMap: { [key:string]: string } = {
  'todo': 'To Do', 'inprogress': 'In Progress', 'done': 'Done', 'review': 'Review', 'blocked': 'Blocked'
};


export default function TaskDetailView({ taskId, isOpen, onClose, onTaskUpdated }: TaskDetailViewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [formApiError, setFormApiError] = useState<string | null>(null);
  const [isFormSubmitting, setIsFormSubmitting] = useState(false);

  const { data: task, error, isLoading, mutate: mutateTask } =
    useSWR<Task>(taskId && isOpen ? `/tasks/${taskId}` : null, taskFetcher, {
      revalidateOnFocus: false,
      // Keep previous data while loading new task, useful if taskId changes rapidly
      // keepPreviousData: true,
    });

  const { data: project } = useSWR<Project | null>(
    () => task?.project_id ? `/projects/${task.project_id}` : null, // Conditional fetch based on task data
    projectFetcher
  );

  useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
      setFormApiError(null);
    } else {
        // When dialog opens for a new task, ensure edit mode is off
        setIsEditing(false);
    }
  }, [isOpen, taskId]); // Reset edit mode if taskId changes while dialog is open

  useEffect(() => {
    // If task data is updated externally (e.g. SWR revalidation) and we are not editing,
    // it's fine. If we *were* editing, the TaskForm's own useEffect handles reset.
    // This effect is mostly to ensure if the task prop itself changes (e.g. different task ID loaded),
    // we are out of edit mode.
    setIsEditing(false);
  }, [task?.id, task?.updated_at]); // Listen to specific fields that indicate task identity or freshness


  const handleFormSubmit = (updatedTask: Task) => {
    mutateTask(updatedTask, false);
    if (onTaskUpdated) onTaskUpdated();
    setIsEditing(false);
  };

  const handleDialogClose = () => {
    if (isFormSubmitting) return;
    setIsEditing(false);
    setFormApiError(null);
    onClose();
  }

  if (!isOpen || !taskId) return null;

  if (isLoading && !task) { // Show loader only if no task data is available yet
    return (
      <Dialog open={isOpen} onOpenChange={handleDialogClose}>
        <DialogContent className="sm:max-w-2xl">
          <div className="flex items-center justify-center p-10 min-h-[200px]">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (error || !task) {
    return (
      <Dialog open={isOpen} onOpenChange={handleDialogClose}>
        <DialogContent className="sm:max-w-lg"> {/* Smaller for error */}
          <DialogHeader><DialogTitle>Error</DialogTitle></DialogHeader>
          <p className="py-4 text-red-600">{error?.message || 'Task not found.'}</p>
          <DialogFooter>
            <Button variant="outline" onClick={handleDialogClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleDialogClose}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0 border-b pb-4">
          <div className="flex justify-between items-start">
            <DialogTitle className="text-xl md:text-2xl break-words pr-2"> {/* Allow title to wrap */}
              {isEditing ? 'Edit Task:' : ''} {task.title}
            </DialogTitle>
            {!isEditing && (
              <Button variant="outline" size="sm" onClick={() => { setIsEditing(true); setFormApiError(null); }} disabled={isFormSubmitting}>
                <Edit className="h-4 w-4 mr-1" /> Edit
              </Button>
            )}
          </div>
          {!isEditing && task.description && ( // Only show description here if NOT editing
            <DialogDescription className="pt-1 whitespace-pre-wrap line-clamp-3 max-h-24 overflow-y-auto">
              {task.description}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="flex-grow overflow-y-auto pr-2 space-y-4 py-4 custom-scrollbar">
          {isEditing ? (
            <TaskForm
              task={task}
              onFormSubmit={handleFormSubmit}
              onCancel={() => { setIsEditing(false); setFormApiError(null);}}
              isSubmittingGlobal={isFormSubmitting}
              setIsSubmittingGlobal={setIsFormSubmitting}
              apiError={formApiError}
              setApiError={setFormApiError}
            />
          ) : (
            <div className="space-y-3 text-sm">
              {task.description && <p className="text-base whitespace-pre-wrap bg-slate-50 dark:bg-slate-800/50 p-3 rounded-md">{task.description}</p>}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 pt-2">
                <div><strong>Status:</strong> <Badge variant="secondary" className="capitalize">{statusDisplayMap[task.status] || task.status}</Badge></div>
                {typeof task.priority === 'number' && (
                  <div><strong>Priority:</strong> <Badge className={`${priorityColorMap[task.priority]} text-white hover:${priorityColorMap[task.priority]}`}>{priorityMap[task.priority]}</Badge></div>
                )}
                {project && <div><strong>Project:</strong> <Badge variant="outline">{project.name}</Badge></div>}
                {task.due_date && isValid(parseISO(task.due_date)) && ( // Check if date is valid before formatting
                  <div><strong>Due Date:</strong> {format(parseISO(task.due_date), "PPP")}</div>
                )}
              </div>
              <div className="border-t pt-3 mt-3">
                 <h4 className="font-semibold text-md mb-2">Details</h4>
                 <p><strong>Created:</strong> {format(parseISO(task.created_at), "PPPp")}</p>
                 <p><strong>Last Updated:</strong> {format(parseISO(task.updated_at), "PPPp")}</p>
                 {task.parent_task_id && <p><strong>Parent Task ID:</strong> {task.parent_task_id}</p>}
              </div>
            </div>
          )}
        </div>

        {!isEditing && (
          <DialogFooter className="flex-shrink-0 pt-2 border-t mt-auto"> {/* Ensure footer is at bottom */}
            <Button type="button" variant="outline" onClick={handleDialogClose}>Close</Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
