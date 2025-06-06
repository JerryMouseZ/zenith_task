'use client';

import { useEffect, useState } from 'react';
import useSWR, { mutate } from 'swr';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Task, TaskUpdate, Project, TaskCreate, Comment, CommentCreate } from '@/types/api'; // Assuming TaskUpdate schema exists
import { apiClient } from '@/lib/apiClient';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
// import { DatePicker } from '@/components/ui/datepicker'; // Assuming a DatePicker component exists
import { Loader2, Edit, Save, XCircle, CalendarIcon, Trash2, CheckSquare, Square, Edit3, Trash, Ban } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { Checkbox } from '@/components/ui/checkbox';

// Define Zod schema for task update (similar to TaskForm, but for updates)
const taskUpdateSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  project_id: z.number().nullable().optional(),
  status: z.string().optional(), // Consider specific statuses: 'todo', 'inprogress', 'done'
  priority: z.number().min(0).max(3).optional(), // e.g., 0: None, 1: Low, 2: Medium, 3: High
  due_date: z.date().nullable().optional(),
  // Add other fields as needed: tags, assignee_id, etc.
});

type TaskUpdateFormInputs = z.infer<typeof taskUpdateSchema>;

interface TaskDetailModalProps {
  taskId: number | null;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  // onTaskUpdated?: () => void; // Callback to revalidate lists if needed
}

const taskFetcher = (url: string) => apiClient.get<Task>(url);
const projectsFetcher = (url: string) => apiClient.get<Project[]>(url);
const commentsFetcher = (url: string) => apiClient.get<Comment[]>(url);

export default function TaskDetailModal({ taskId, isOpen, onOpenChange }: TaskDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState('');
  const [newComment, setNewComment] = useState('');
  const [editingSubtaskId, setEditingSubtaskId] = useState<number | null>(null);
  const [editingSubtaskTitle, setEditingSubtaskTitle] = useState<string>('');

  const { data: task, error: taskError, isLoading: taskIsLoading, mutate: mutateTask } = 
    useSWR<Task>(taskId && isOpen ? `/tasks/${taskId}` : null, taskFetcher, {
      revalidateOnFocus: false, // Avoid re-fetching if modal was just closed and reopened quickly
    });

  const { data: comments, error: commentsError, isLoading: commentsLoading, mutate: mutateComments } = 
    useSWR<Comment[]>(taskId && isOpen ? `/tasks/${taskId}/comments` : null, commentsFetcher, {
      revalidateOnFocus: false,
    });

  // Fetch projects for the project_id dropdown
  const { data: projects, error: projectsError } = useSWR<Project[]>('/projects?archived=false', projectsFetcher);

  const {
    register,
    handleSubmit,
    reset,
    control, // for Select and DatePicker if using react-hook-form Controller
    setValue,
    watch, // Added watch
    formState: { errors, isSubmitting, isDirty },
  } = useForm<TaskUpdateFormInputs>({
    resolver: zodResolver(taskUpdateSchema),
  });

  useEffect(() => {
    if (task && isOpen) {
      reset({
        title: task.title,
        description: task.description || '',
        project_id: task.project_id,
        status: task.status || 'todo',
        priority: task.priority || 0,
        due_date: task.due_date ? new Date(task.due_date) : null,
      });
      setIsEditing(false); // Reset to view mode when task data changes or modal opens
      setApiError(null);
    } else if (!isOpen) {
      // Clear form when modal is closed
      reset();
      setIsEditing(false);
      setApiError(null);
    }
  }, [task, isOpen, reset]);

  const handleUpdateTask: SubmitHandler<TaskUpdateFormInputs> = async (data) => {
    if (!taskId) return;
    setApiError(null);

    const updatePayload: TaskUpdate = {
      ...data,
      due_date: data.due_date ? data.due_date.toISOString() : null,
    };

    try {
      const updatedTask = await apiClient.put<Task, TaskUpdate>(`/tasks/${taskId}`, updatePayload);
      mutateTask(updatedTask, false); // Optimistically update local SWR cache
      mutate(`/tasks/?project_id=${updatedTask.project_id}`); // Revalidate tasks for the project
      mutate('/tasks'); // Revalidate general task list if any
      setIsEditing(false);
      toast.success('Task updated successfully!');
      // onTaskUpdated?.(); // Call parent callback
      // onOpenChange(false); // Optionally close modal on success
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
        toast.error(error.message || 'Failed to update task.');
      } else {
        setApiError('An unexpected error occurred.');
        toast.error('Failed to update task.');
      }
    }
  };

  const handleDeleteTask = async () => {
    if (!taskId || !task) return;
    if (!confirm('Are you sure you want to delete this task? This action cannot be undone.')) return;

    setApiError(null);
    try {
      await apiClient.delete(`/tasks/${taskId}`);
      mutate(`/tasks/?project_id=${task.project_id}`);
      mutate('/tasks');
      toast.success('Task deleted successfully!');
      onOpenChange(false); // Close modal on successful delete
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
        toast.error(error.message || 'Failed to delete task.');
      } else {
        setApiError('Failed to delete task.');
        toast.error('Failed to delete task.');
      }
    }
  };

  const handleCancelEdit = () => {
    if (isDirty) {
      toast.info('Edit cancelled. Changes were not saved.');
    }
    setIsEditing(false);
  };

  const handleToggleEditMode = () => {
    // Only show toast if transitioning from edit mode to view mode with pending changes
    if (isEditing && isDirty) {
      toast.info('Edit cancelled. Changes were not saved.');
    }
    setIsEditing(prevIsEditing => !prevIsEditing);
  };

  const handleToggleSubtask = async (subtaskId: number, currentStatus: string) => {
    const newStatus = currentStatus === 'done' ? 'todo' : 'done';
    try {
      await apiClient.put<Task, Partial<TaskUpdate>>(`/tasks/${subtaskId}`, { status: newStatus });
      mutateTask(); // Revalidate parent task to refresh subtask list
      toast.success(`Subtask marked as ${newStatus}.`);
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message || 'Failed to update subtask status.');
      } else {
        toast.error('Failed to update subtask status.');
      }
    }
  };

  const handlePostComment = async () => {
    if (!taskId || !newComment.trim()) return;

    const commentData: CommentCreate = {
      content: newComment.trim(),
    };

    try {
      await apiClient.post<Comment, CommentCreate>(`/tasks/${taskId}/comments`, commentData);
      mutateComments(); // Revalidate comments list
      setNewComment('');
      toast.success('Comment posted successfully!');
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message || 'Failed to post comment.');
      } else {
        toast.error('Failed to post comment.');
      }
    }
  };

  const handleSetEditingSubtask = (subtask: Task) => {
    setEditingSubtaskId(subtask.id);
    setEditingSubtaskTitle(subtask.title);
  };

  const handleCancelEditSubtask = () => {
    setEditingSubtaskId(null);
    setEditingSubtaskTitle('');
  };

  const handleUpdateSubtaskTitle = async () => {
    if (!editingSubtaskId || !editingSubtaskTitle.trim()) return;
    try {
      await apiClient.put<Task, Partial<TaskUpdate>>(`/tasks/${editingSubtaskId}`, { title: editingSubtaskTitle.trim() });
      mutateTask(); // Revalidate parent task
      toast.success('Subtask title updated.');
      handleCancelEditSubtask(); // Reset editing state
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update subtask title.');
    }
  };

  const handleDeleteSubtask = async (subtaskId: number) => {
    if (!window.confirm('Are you sure you want to delete this subtask?')) return;
    try {
      await apiClient.delete(`/tasks/${subtaskId}`);
      mutateTask(); // Revalidate parent task
      toast.success('Subtask deleted.');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to delete subtask.');
    }
  };

  const handleAddSubtask = async () => {
    if (!taskId || !newSubtaskTitle.trim()) return;

    const subtaskData: TaskCreate = {
      title: newSubtaskTitle.trim(),
      parent_task_id: taskId,
      project_id: task?.project_id, // Inherit project from parent
      status: 'todo', // Default status for new subtasks
    };

    try {
      await apiClient.post<Task, TaskCreate>('/tasks', subtaskData);
      mutateTask(); // Revalidate parent task to show new subtask
      setNewSubtaskTitle('');
      toast.success('Subtask added successfully!');
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message || 'Failed to add subtask.');
      } else {
        toast.error('Failed to add subtask.');
      }
    }
  };

  const renderViewMode = () => {
    if (!task) return null;
    return (
      <div className="space-y-3">
        <p><strong className="font-medium">Description:</strong> {task.description || <span className="text-muted-foreground">N/A</span>}</p>
        <p><strong className="font-medium">Status:</strong> <span className="capitalize">{task.status || 'N/A'}</span></p>
        <p><strong className="font-medium">Priority:</strong> {typeof task.priority === 'number' && task.priority >= 0 && task.priority <= 3 ? ['None', 'Low', 'Medium', 'High'][task.priority] : <span className="text-muted-foreground">N/A</span>}</p>
        <p><strong className="font-medium">Due Date:</strong> {task.due_date ? format(new Date(task.due_date), 'PPP') : <span className="text-muted-foreground">N/A</span>}</p>
        <p><strong className="font-medium">Project:</strong> {task.project && task.project.name ? task.project.name : <span className="text-muted-foreground">None</span>}</p>
        <p className="text-xs text-muted-foreground pt-2">
          Created: {format(new Date(task.created_at), 'PPpp')} | Updated: {format(new Date(task.updated_at), 'PPpp')}
        </p>

        {/* Subtasks Section */}
        <div className="pt-4">
          <h4 className="font-medium mb-2">Subtasks</h4>
          {task.sub_tasks && task.sub_tasks.length > 0 ? (
            <ul className="space-y-2">
              {task.sub_tasks.map(subtask => (
                <li key={subtask.id} className="flex items-center space-x-2 p-2 border rounded-md bg-slate-50 dark:bg-slate-800 min-h-[50px]">
                  <Checkbox 
                    id={`subtask-${subtask.id}`}
                    checked={subtask.status === 'done'}
                    onCheckedChange={() => handleToggleSubtask(subtask.id, subtask.status)}
                    disabled={isSubmitting || editingSubtaskId === subtask.id}
                  />
                  {editingSubtaskId === subtask.id ? (
                    <>
                      <Input 
                        type="text" 
                        value={editingSubtaskTitle} 
                        onChange={(e) => setEditingSubtaskTitle(e.target.value)}
                        onKeyPress={(e) => { if (e.key === 'Enter') handleUpdateSubtaskTitle(); }}
                        className="flex-1 h-8 text-sm"
                        autoFocus
                      />
                      <Button variant="ghost" size="icon" onClick={handleUpdateSubtaskTitle} className="h-8 w-8">
                        <Save className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={handleCancelEditSubtask} className="h-8 w-8">
                        <Ban className="h-4 w-4 text-muted-foreground" />
                      </Button>
                    </>
                  ) : (
                    <>
                      <label 
                        htmlFor={`subtask-${subtask.id}`} 
                        className={`flex-1 cursor-pointer ${subtask.status === 'done' ? 'line-through text-muted-foreground' : ''}`}
                        onDoubleClick={() => { if (subtask.status !== 'done') handleSetEditingSubtask(subtask); }} // Allow edit on double click if not done
                      >
                        {subtask.title}
                      </label>
                      <Button variant="ghost" size="icon" onClick={() => handleSetEditingSubtask(subtask)} disabled={isSubmitting || subtask.status === 'done'} className="h-8 w-8">
                        <Edit3 className="h-4 w-4 text-blue-600" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => handleDeleteSubtask(subtask.id)} disabled={isSubmitting} className="h-8 w-8">
                        <Trash className="h-4 w-4 text-red-600" />
                      </Button>
                    </>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No subtasks yet.</p>
          )}
          <div className="mt-3 flex space-x-2">
            <Input 
              type="text" 
              placeholder="Add a new subtask..." 
              value={newSubtaskTitle} 
              onChange={(e) => setNewSubtaskTitle(e.target.value)}
              onKeyPress={(e) => { if (e.key === 'Enter') handleAddSubtask(); }}
            />
            <Button onClick={handleAddSubtask} disabled={!newSubtaskTitle.trim() || isSubmitting}>
              Add Subtask
            </Button>
          </div>
        </div>

        {/* Comments Section */}
        <div className="pt-4 mt-4 border-t">
          <h4 className="font-medium mb-2">Comments</h4>
          {commentsLoading && <Loader2 className="h-5 w-5 animate-spin my-2" />}
          {commentsError && <p className="text-sm text-red-500">Error loading comments.</p>}
          {comments && comments.length > 0 && (
            <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
              {comments.map(comment => (
                <div key={comment.id} className="p-2 border rounded-md bg-slate-50 dark:bg-slate-800">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-semibold">{comment.user?.full_name || `User ${comment.user_id}`}</span>
                    <span className="text-xs text-muted-foreground">{format(new Date(comment.created_at), 'PP p')}</span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
                  {/* Edit/Delete comment options can be added later */}
                </div>
              ))}
            </div>
          )}
          {comments && comments.length === 0 && !commentsLoading && (
            <p className="text-sm text-muted-foreground">No comments yet.</p>
          )}
          <div className="mt-3">
            <Textarea 
              placeholder="Add a comment..." 
              value={newComment} 
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
            />
            <Button onClick={handlePostComment} disabled={!newComment.trim() || isSubmitting || commentsLoading} className="mt-2">
              Post Comment
            </Button>
          </div>
        </div>
      </div>
    );
  };

  const renderEditMode = () => (
    <form onSubmit={handleSubmit(handleUpdateTask)} className="space-y-4">
      <div>
        <Label htmlFor="title">Title</Label>
        <Input id="title" {...register('title')} />
        {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
      </div>
      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea id="description" {...register('description')} />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="status">Status</Label>
          <Select onValueChange={(value) => setValue('status', value, { shouldDirty: true })} defaultValue={task?.status || 'todo'}>
            <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="todo">To Do</SelectItem>
              <SelectItem value="inprogress">In Progress</SelectItem>
              <SelectItem value="done">Done</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="priority">Priority</Label>
          <Select onValueChange={(value) => setValue('priority', parseInt(value), { shouldDirty: true })} defaultValue={String(task?.priority || 0)}>
            <SelectTrigger><SelectValue placeholder="Select priority" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="0">None</SelectItem>
              <SelectItem value="1">Low</SelectItem>
              <SelectItem value="2">Medium</SelectItem>
              <SelectItem value="3">High</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="project_id">Project</Label>
          <Select onValueChange={(value) => setValue('project_id', value ? parseInt(value) : null, { shouldDirty: true })} defaultValue={String(task?.project_id || '')}>
            <SelectTrigger><SelectValue placeholder="Select project (optional)" /></SelectTrigger>
            <SelectContent>
              <SelectItem value=""><em>No Project</em></SelectItem>
              {projectsError && <SelectItem value="" disabled>Error loading projects</SelectItem>}
              {!projects && !projectsError && <SelectItem value="" disabled>Loading projects...</SelectItem>}
              {projects?.map(p => <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="due_date">Due Date</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant={"outline"}
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !watch('due_date') && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {watch('due_date') ? format(watch('due_date')!, 'PPP') : <span>Pick a date</span>}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                mode="single"
                selected={watch('due_date') || undefined}
                onSelect={(date) => setValue('due_date', date || null, { shouldDirty: true })}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>
      </div>

      {apiError && <p className="text-sm text-red-600 mt-2">{apiError}</p>}

      <DialogFooter className="pt-4">
        <Button type="button" variant="outline" onClick={handleCancelEdit} disabled={isSubmitting}>Cancel</Button>
        <Button type="submit" disabled={isSubmitting || !isDirty}>
          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
          Save Changes
        </Button>
      </DialogFooter>
    </form>
  );

  if (!isOpen || !taskId) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex justify-between items-center">
            <DialogTitle className="truncate max-w-[calc(100%-100px)]">{isEditing ? 'Edit Task' : task?.title || 'Task Details'}</DialogTitle>
            {!taskIsLoading && task && (
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="icon" onClick={handleToggleEditMode} disabled={isSubmitting || isEditing && !isDirty}>
                  {isEditing ? <XCircle className="h-5 w-5" /> : <Edit className="h-5 w-5" />}
                  <span className="sr-only">{isEditing ? 'Cancel Edit' : 'Edit Task'}</span>
                </Button>
                 <Button variant="ghost" size="icon" onClick={handleDeleteTask} disabled={isSubmitting || isEditing} className="text-red-500 hover:text-red-700">
                  <Trash2 className="h-5 w-5" />
                  <span className="sr-only">Delete Task</span>
                </Button>
              </div>
            )}
          </div>
          {!isEditing && task?.description && <DialogDescription className="line-clamp-2">{task.description}</DialogDescription>}
        </DialogHeader>
        
        {taskIsLoading && (
          <div className="flex justify-center items-center h-40">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}
        {taskError && (
          <div className="text-red-500 p-4 border border-red-500 rounded-md">
            <p><strong>Error:</strong> {taskError.message || 'Could not load task details.'}</p>
          </div>
        )}
        {!taskIsLoading && !taskError && task && (
          isEditing ? renderEditMode() : renderViewMode()
        )}
        {!taskIsLoading && !taskError && !task && taskId && (
            <p className="text-muted-foreground text-center py-10">Task not found.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}
