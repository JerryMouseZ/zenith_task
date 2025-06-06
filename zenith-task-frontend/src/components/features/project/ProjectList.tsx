'use client';

import useSWR from 'swr';
import { Project } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import ProjectCard from './ProjectCard';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'; // For error display
import { Loader2 } from 'lucide-react'; // For loading state

// SWR fetcher function
const fetcher = (url: string) => apiClient.get<Project[]>(url);

export default function ProjectList() {
  const { data: projects, error, isLoading } = useSWR<Project[]>('/projects', fetcher);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-10">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="ml-2">Loading projects...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error Loading Projects</AlertTitle>
        <AlertDescription>{error.message || 'An unknown error occurred.'}</AlertDescription>
      </Alert>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <div className="text-center py-10">
        <p className="text-lg text-muted-foreground">No projects found.</p>
        <p className="text-sm text-muted-foreground">Get started by creating a new project.</p>
      </div>
    );
  }

  // Filter out archived projects for the main list, can add a toggle later
  const activeProjects = projects.filter(p => !p.is_archived);

  if (activeProjects.length === 0) {
     return (
      <div className="text-center py-10">
        <p className="text-lg text-muted-foreground">No active projects found.</p>
        <p className="text-sm text-muted-foreground">You can create a new project or view archived projects.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {activeProjects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
