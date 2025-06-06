'use client';

import { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import useSWR, { mutate } from 'swr';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch'; // For is_archived
import { apiClient } from '@/lib/apiClient';
import { Project, ProjectUpdate } from '@/types/api';
import { Loader2, Edit, Save, XCircle } from 'lucide-react';
import { useUserStore } from '@/store/userStore'; // To check if user can edit

// Schema for project update
const projectUpdateSchema = z.object({
  name: z.string().min(3, { message: 'Project name must be at least 3 characters' }),
  description: z.string().optional(),
  color_hex: z.string().regex(/^#([0-9A-Fa-f]{3}){1,2}$/, { message: 'Invalid hex color' }).optional().or(z.literal('')),
  view_preference: z.enum(['list', 'kanban']).optional(),
  is_archived: z.boolean().optional(),
});

type ProjectUpdateFormInputs = z.infer<typeof projectUpdateSchema>;

interface ProjectDetailViewProps {
  project: Project; // Initial project data passed as prop
}

export default function ProjectDetailView({ project: initialProject }: ProjectDetailViewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const currentUser = useUserStore((state) => state.user);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch, // Watch for changes to enable save button
    formState: { errors, isDirty },
  } = useForm<ProjectUpdateFormInputs>({
    resolver: zodResolver(projectUpdateSchema),
    defaultValues: {
      name: initialProject.name,
      description: initialProject.description || '',
      color_hex: initialProject.color_hex || '',
      view_preference: initialProject.view_preference || 'kanban',
      is_archived: initialProject.is_archived,
    },
  });

  // Reset form when initialProject changes or when editing is cancelled
  useEffect(() => {
    if (initialProject) {
      reset({
        name: initialProject.name,
        description: initialProject.description || '',
        color_hex: initialProject.color_hex || '',
        view_preference: initialProject.view_preference || 'kanban',
        is_archived: initialProject.is_archived,
      });
    }
  }, [initialProject, reset]); // Removed isEditing from dependency array to prevent reset when toggling edit mode with dirty form

  // Check if the current user owns this project (basic check)
  // This should ideally be handled by backend policies (e.g. user can only fetch projects they own)
  // But as a client-side check for enabling UI:
  const canEdit = currentUser && currentUser.id === initialProject.user_id;

  const onSubmit: SubmitHandler<ProjectUpdateFormInputs> = async (data) => {
    if (!canEdit) {
      setApiError("You don't have permission to edit this project.");
      return;
    }
    setIsSubmitting(true);
    setApiError(null);

    const updateData: ProjectUpdate = {
      name: data.name,
      description: data.description || null,
      color_hex: data.color_hex || null,
      view_preference: data.view_preference,
      is_archived: data.is_archived,
    };

    try {
      const updatedProject = await apiClient.put<Project, ProjectUpdate>(`/projects/${initialProject.id}`, updateData);
      // Revalidate this specific project's SWR cache and the main list
      mutate(`/projects/${initialProject.id}`, updatedProject, false); // Update local SWR cache immediately
      mutate('/projects'); // Revalidate project list page's cache
      setIsEditing(false);
      // Optionally show success message
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('An unexpected error occurred while updating the project.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    reset({ // Reset to initial project values
        name: initialProject.name,
        description: initialProject.description || '',
        color_hex: initialProject.color_hex || '',
        view_preference: initialProject.view_preference || 'kanban',
        is_archived: initialProject.is_archived,
      });
  };


  if (!initialProject) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row justify-between items-center">
        <div>
          <CardTitle className="flex items-center">
            {isEditing ? 'Edit Project' : initialProject.name}
            {initialProject.color_hex && !isEditing && (
              <span className="w-4 h-4 rounded-full inline-block ml-2" style={{ backgroundColor: initialProject.color_hex }}></span>
            )}
          </CardTitle>
          {!isEditing && initialProject.description && <CardDescription>{initialProject.description}</CardDescription>}
        </div>
        {canEdit && (
          <Button variant="outline" size="sm" onClick={() => {
            if (isEditing) {
              handleCancelEdit();
            } else {
              setIsEditing(true);
            }
          }} disabled={isSubmitting}>
            {isEditing ? <XCircle className="h-4 w-4 mr-1" /> : <Edit className="h-4 w-4 mr-1" />}
            {isEditing ? 'Cancel' : 'Edit'}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {isEditing && canEdit ? ( // Show form only if editing and allowed
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="name">Project Name</Label>
              <Input id="name" {...register('name')} />
              {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
            </div>
            <div className="space-y-1">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" {...register('description')} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label htmlFor="color_hex">Color (e.g., #FF5733)</Label>
                <Input id="color_hex" {...register('color_hex')} />
                {errors.color_hex && <p className="text-sm text-red-500">{errors.color_hex.message}</p>}
              </div>
              <div className="space-y-1">
                <Label htmlFor="view_preference">Default View</Label>
                 <select
                    id="view_preference"
                    {...register('view_preference')}
                    defaultValue={initialProject.view_preference || 'kanban'}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="kanban">Kanban</option>
                    <option value="list">List</option>
                  </select>
              </div>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <Switch id="is_archived" {...register('is_archived')} defaultChecked={initialProject.is_archived} onCheckedChange={(checked) => setValue('is_archived', checked, { shouldDirty: true })} />
              <Label htmlFor="is_archived" className="cursor-pointer">Archive Project</Label>
            </div>
            {apiError && <p className="text-sm text-red-600">{apiError}</p>}
            <div className="flex justify-end space-x-2 pt-2">
              <Button type="button" variant="outline" onClick={handleCancelEdit} disabled={isSubmitting}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting || !isDirty}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
                Save Changes
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-2">
            <p><strong>Description:</strong> {initialProject.description || 'N/A'}</p>
            <p><strong>Default View:</strong> {initialProject.view_preference || 'kanban'}</p>
            <p><strong>Status:</strong> {initialProject.is_archived ? 'Archived' : 'Active'}</p>
            <p><strong>Created:</strong> {new Date(initialProject.created_at).toLocaleDateString()}</p>
            <p><strong>Last Updated:</strong> {new Date(initialProject.updated_at).toLocaleDateString()}</p>
            {!canEdit && currentUser && <p className="text-sm text-yellow-600 mt-4">You do not have permission to edit this project.</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
