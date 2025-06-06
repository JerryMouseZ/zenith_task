'use client';

import { useEffect } from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import useSWR from 'swr';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { apiClient } from '@/lib/apiClient';
import { Task, TaskUpdate, Project } from '@/types/api';
import { Loader2, Save, CalendarIcon, X } from 'lucide-react';
import { cn } from "@/lib/utils";
import { format, parseISO, isValid } from 'date-fns'; // Added isValid

// Schema for task update
const taskUpdateSchema = z.object({
  title: z.string().min(3, { message: 'Task title must be at least 3 characters' }),
  description: z.string().nullable().optional(),
  status: z.string(),
  project_id: z.string().nullable().optional(),
  priority: z.string().nullable().optional().transform(val => val ? parseInt(val, 10) : null), // Ensure transform handles empty string or null
  due_date: z.date().nullable().optional(),
});

type TaskFormInputs = z.infer<typeof taskUpdateSchema>;

interface TaskFormProps {
  task: Task;
  onFormSubmit: (updatedTask: Task) => void;
  onCancel: () => void;
  isSubmittingGlobal: boolean; // Renamed to avoid conflict with local state if any
  setIsSubmittingGlobal: (isSubmitting: boolean) => void;
  apiError?: string | null;
  setApiError: (error: string | null) => void;
}

const projectsFetcher = (url: string) => apiClient.get<Project[]>(url).then(res => res.filter(p => !p.is_archived));
const taskStatusOptions = ['todo', 'inprogress', 'done', 'review', 'blocked'];
const priorityOptions = [
    { value: '0', label: 'Low' },
    { value: '1', label: 'Medium' },
    { value: '2', label: 'High' },
    { value: '3', label: 'Urgent' },
];

export default function TaskForm({
  task,
  onFormSubmit,
  onCancel,
  isSubmittingGlobal,
  setIsSubmittingGlobal,
  apiError,
  setApiError,
}: TaskFormProps) {
  const { data: projects } = useSWR<Project[]>('/projects', projectsFetcher);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isDirty },
  } = useForm<TaskFormInputs>({
    resolver: zodResolver(taskUpdateSchema),
    // Default values are set by useEffect below
  });

  useEffect(() => {
    if (task) {
      const parsedDueDate = task.due_date ? parseISO(task.due_date) : null;
      reset({
        title: task.title,
        description: task.description || '',
        status: task.status || 'todo',
        project_id: task.project_id ? String(task.project_id) : undefined, // use undefined for Controller with Select if no project
        priority: task.priority !== null && typeof task.priority !== "undefined" ? String(task.priority) : undefined, // use undefined for Select
        due_date: parsedDueDate && isValid(parsedDueDate) ? parsedDueDate : null,
      });
    }
  }, [task, reset]);


  const processSubmit: SubmitHandler<TaskFormInputs> = async (data) => {
    setIsSubmittingGlobal(true);
    setApiError(null);

    const updateData: TaskUpdate = {
      ...data, // Spread validated and transformed data
      project_id: data.project_id ? parseInt(data.project_id, 10) : null,
      // priority is already transformed by zod
      due_date: data.due_date ? format(data.due_date, "yyyy-MM-dd'T'HH:mm:ssXXX") : null,
    };
    // Remove undefined fields explicitly if backend expects them to be absent
    Object.keys(updateData).forEach(key => {
        if (updateData[key as keyof TaskUpdate] === undefined) {
            delete updateData[key as keyof TaskUpdate];
        }
    });


    try {
      const updatedTask = await apiClient.put<Task, TaskUpdate>(`/tasks/${task.id}`, updateData);
      onFormSubmit(updatedTask);
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('An unexpected error occurred.');
      }
    } finally {
      setIsSubmittingGlobal(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(processSubmit)} className="space-y-4 p-1">
      <div className="space-y-1">
        <Label htmlFor={`title_edit_${task.id}`}>Task Title</Label> {/* Unique ID for label */}
        <Input id={`title_edit_${task.id}`} {...register('title')} />
        {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
      </div>

      <div className="space-y-1">
        <Label htmlFor={`description_edit_${task.id}`}>Description</Label>
        <Textarea id={`description_edit_${task.id}`} {...register('description')} rows={4} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor={`status_edit_${task.id}`}>Status</Label>
          <Controller
            name="status"
            control={control}
            defaultValue={task.status || 'todo'}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                <SelectContent>
                  {taskStatusOptions.map(opt => <SelectItem key={opt} value={opt}>{opt.charAt(0).toUpperCase() + opt.slice(1)}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        <div className="space-y-1">
          <Label htmlFor={`priority_edit_${task.id}`}>Priority</Label>
          <Controller
            name="priority"
            control={control}
            defaultValue={task.priority !== null && typeof task.priority !== "undefined" ? String(task.priority) : undefined}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                value={field.value !== null && typeof field.value !== "undefined" ? String(field.value) : ""} // Ensure value is string or undefined
              >
                <SelectTrigger><SelectValue placeholder="Select priority" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value=""><em>No Priority</em></SelectItem> {/* Changed value from "null" to "" */}
                  {priorityOptions.map(opt => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor={`project_id_edit_${task.id}`}>Project</Label>
          <Controller
            name="project_id"
            control={control}
            defaultValue={task.project_id ? String(task.project_id) : undefined}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                value={field.value || ""} // Ensure value is string or undefined for Select
              >
                <SelectTrigger><SelectValue placeholder="Select project" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value=""><em>No Project</em></SelectItem> {/* Changed value from "null" to "" */}
                  {projects?.map(proj => <SelectItem key={proj.id} value={String(proj.id)}>{proj.name}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        <div className="space-y-1">
          <Label htmlFor={`due_date_edit_${task.id}`}>Due Date</Label>
          <Controller
            name="due_date"
            control={control}
            render={({ field }) => (
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("w-full justify-start text-left font-normal", !field.value && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {field.value ? format(field.value, "PPP") : <span>Pick a date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar mode="single" selected={field.value} onSelect={field.onChange} initialFocus />
                </PopoverContent>
              </Popover>
            )}
          />
        </div>
      </div>

      {apiError && <p className="text-sm text-red-600 mt-2">{apiError}</p>}

      <div className="flex justify-end space-x-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmittingGlobal}><X className="h-4 w-4 mr-1" />Cancel</Button>
        <Button type="submit" disabled={isSubmittingGlobal || !isDirty}>
          {isSubmittingGlobal && <Loader2 className="h-4 w-4 animate-spin mr-1" />} Save Changes
        </Button>
      </div>
    </form>
  );
}
