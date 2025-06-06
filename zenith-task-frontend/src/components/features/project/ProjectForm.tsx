'use client';

import { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import useSWR, { mutate } from 'swr'; // For revalidating project list after creation

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea'; // Added for description
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/apiClient';
import { ProjectCreate, Project } from '@/types/api';

// Schema for project creation
const projectSchema = z.object({
  name: z.string().min(3, { message: 'Project name must be at least 3 characters' }),
  description: z.string().optional(),
  color_hex: z.string().regex(/^#([0-9A-Fa-f]{3}){1,2}$/, { message: 'Invalid hex color (e.g., #RRGGBB or #RGB)' }).optional().or(z.literal('')),
  view_preference: z.enum(['list', 'kanban']).optional(),
});

type ProjectFormInputs = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  onProjectCreated?: (newProject: Project) => void; // Callback after successful creation
}

export default function ProjectForm({ onProjectCreated }: ProjectFormProps) {
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormInputs>({
    resolver: zodResolver(projectSchema),
  });

  const onSubmit: SubmitHandler<ProjectFormInputs> = async (data) => {
    setIsLoading(true);
    setApiError(null);

    const projectData: ProjectCreate = {
      name: data.name,
      description: data.description || null,
      color_hex: data.color_hex || null,
      view_preference: data.view_preference || 'kanban', // Default view
    };

    try {
      const newProject = await apiClient.post<Project, ProjectCreate>('/projects', projectData);
      mutate('/projects'); // Revalidate the SWR cache for the project list
      reset(); // Reset form fields
      if (onProjectCreated) {
        onProjectCreated(newProject);
      }
      // Optionally show a success message or redirect
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('An unexpected error occurred while creating the project.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Create New Project</CardTitle>
        <CardDescription>Fill in the details below to add a new project.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="name">Project Name</Label>
            <Input id="name" {...register('name')} />
            {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
          </div>

          <div className="space-y-1">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea id="description" {...register('description')} />
            {errors.description && <p className="text-sm text-red-500">{errors.description.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label htmlFor="color_hex">Color (Optional, e.g., #FF5733)</Label>
              <Input id="color_hex" type="text" placeholder="#RRGGBB" {...register('color_hex')} />
              {errors.color_hex && <p className="text-sm text-red-500">{errors.color_hex.message}</p>}
            </div>
            <div className="space-y-1">
              <Label htmlFor="view_preference">Default View (Optional)</Label>
              <select
                id="view_preference"
                {...register('view_preference')}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                defaultValue="kanban" // Ensure default value is set for the select
              >
                <option value="kanban">Kanban</option>
                <option value="list">List</option>
              </select>
              {errors.view_preference && <p className="text-sm text-red-500">{errors.view_preference.message}</p>}
            </div>
          </div>

          {apiError && <p className="text-sm text-red-600 mt-2">{apiError}</p>}

          <Button type="submit" className="w-full sm:w-auto" disabled={isLoading}>
            {isLoading ? 'Creating Project...' : 'Create Project'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
