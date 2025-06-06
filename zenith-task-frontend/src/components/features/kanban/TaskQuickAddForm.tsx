'use client';

import { useState, useEffect } from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form'; // Added Controller
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import useSWR, { mutate } from 'swr';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiClient } from '@/lib/apiClient';
import { TaskCreate, Task, Project } from '@/types/api';
import { Loader2 } from 'lucide-react';

// Schema for task creation
const taskQuickAddSchema = z.object({
  title: z.string().min(3, { message: 'Task title must be at least 3 characters' }),
  description: z.string().optional(),
  status: z.string().optional(),
  project_id: z.string().optional(),
  priority: z.string().optional(),
});

type TaskQuickAddFormInputs = z.infer<typeof taskQuickAddSchema>;

interface TaskQuickAddFormProps {
  isOpen: boolean;
  onClose: () => void;
  initialStatus?: string;
  initialProjectId?: number;
  onTaskCreated?: (newTask: Task) => void;
}

const projectsFetcher = (url: string) => apiClient.get<Project[]>(url).then(res => res.filter(p => !p.is_archived)); // Filter archived projects

export default function TaskQuickAddForm({
  isOpen,
  onClose,
  initialStatus,
  initialProjectId,
  onTaskCreated,
}: TaskQuickAddFormProps) {
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: projects, error: projectsError } = useSWR<Project[]>('/projects', projectsFetcher); // Removed ?archived=false, fetcher handles it

  const {
    register,
    handleSubmit,
    reset,
    control, // control for react-hook-form Controller
    formState: { errors },
  } = useForm<TaskQuickAddFormInputs>({
    resolver: zodResolver(taskQuickAddSchema),
    defaultValues: {
      title: '',
      description: '',
      status: initialStatus || 'todo',
      project_id: initialProjectId ? String(initialProjectId) : undefined,
      priority: '1', // Default priority Medium
    },
  });

  useEffect(() => {
    if (isOpen) { // Reset form when dialog opens
      reset({
        title: '',
        description: '',
        status: initialStatus || 'todo',
        project_id: initialProjectId ? String(initialProjectId) : undefined,
        priority: '1',
      });
      setApiError(null); // Clear previous API errors
    }
  }, [isOpen, initialStatus, initialProjectId, reset]);

  const onSubmit: SubmitHandler<TaskQuickAddFormInputs> = async (data) => {
    setIsSubmitting(true);
    setApiError(null);

    const taskData: TaskCreate = {
      title: data.title,
      description: data.description || null,
      status: data.status || 'todo',
      project_id: data.project_id ? parseInt(data.project_id, 10) : null,
      priority: data.priority ? parseInt(data.priority, 10) : 1,
    };

    try {
      const newTask = await apiClient.post<Task, TaskCreate>('/tasks', taskData);

      mutate('/tasks');
      if (taskData.project_id) {
        mutate(`/tasks/?project_id=${taskData.project_id}`); // Corrected SWR key
      }

      // reset(); // Reset is now handled by useEffect on isOpen
      onClose();
      if (onTaskCreated) {
        onTaskCreated(newTask);
      }
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('An unexpected error occurred while creating the task.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const priorityOptions = [
    { value: '0', label: 'Low' },
    { value: '1', label: 'Medium' },
    { value: '2', label: 'High' },
    { value: '3', label: 'Urgent' },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) { onClose(); reset();} }}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Add New Task</DialogTitle>
          <DialogDescription>
            Quickly add a new task. Fill in the details below.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
          <div className="space-y-1">
            <Label htmlFor="title">Task Title</Label>
            <Input id="title" {...register('title')} autoFocus />
            {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
          </div>

          <div className="space-y-1">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea id="description" {...register('description')} rows={3} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label htmlFor="project_id">Project (Optional)</Label>
              <Controller
                name="project_id"
                control={control}
                render={({ field }) => (
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <SelectTrigger id="project_id_trigger">
                      <SelectValue placeholder="Select project" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value=""><em>No Project</em></SelectItem>
                      {projectsError && <SelectItem value="error" disabled>Error loading projects</SelectItem>}
                      {!projects && !projectsError && <SelectItem value="loading" disabled>Loading projects...</SelectItem>}
                      {projects?.map(proj => (
                        <SelectItem key={proj.id} value={String(proj.id)}>{proj.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="priority">Priority</Label>
              <Controller
                name="priority"
                control={control}
                defaultValue='1'
                render={({ field }) => (
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <SelectTrigger id="priority_trigger">
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorityOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          {initialStatus && (
            <div className="space-y-1">
              <Label>Status</Label>
              <p className="text-sm p-2 border rounded-md bg-gray-50 dark:bg-gray-800/50 text-gray-700 dark:text-gray-300">{initialStatus}</p>
              <input type="hidden" {...register('status')} value={initialStatus} />
            </div>
          )}

          {apiError && <p className="text-sm text-red-600 mt-2">{apiError}</p>}

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => { onClose(); reset();}}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
              {isSubmitting ? 'Adding Task...' : 'Add Task'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
