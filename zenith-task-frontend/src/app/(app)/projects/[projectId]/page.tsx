'use client';

import { useParams } from 'next/navigation';
import useSWR from 'swr';
import { Project, Task } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import ProjectDetailView from '@/components/features/project/ProjectDetailView';
import KanbanBoard from '@/components/features/kanban/KanbanBoard';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'; // Added Card components
import { Loader2 } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

const projectFetcher = (url: string) => apiClient.get<Project>(url);
const tasksFetcher = (url: string) => apiClient.get<Task[]>(url); // Assuming Task[] is the expected response

export default function SpecificProjectPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const { data: project, error: projectError, isLoading: projectIsLoading, mutate: mutateProject } =
    useSWR<Project>(projectId ? `/projects/${projectId}` : null, projectFetcher);



  if (projectIsLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  if (projectError) {
    return (
      <Alert variant="destructive" className="max-w-lg mx-auto mt-10">
        <AlertTitle>Error Loading Project</AlertTitle>
        <AlertDescription>
          {projectError.message || 'Could not load project details.'}
          <div className="mt-4">
            <Button asChild variant="outline">
              <Link href="/projects">Back to Projects</Link>
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-10">
        <p className="text-lg text-muted-foreground">Project not found.</p>
         <div className="mt-4">
            <Button asChild variant="outline">
              <Link href="/projects">Back to Projects</Link>
            </Button>
          </div>
      </div>
    );
  }



  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
         <Button asChild variant="outline" size="sm">
           <Link href="/projects">← Back to All Projects</Link>
         </Button>
      </div>

      <ProjectDetailView project={project} />

      <Card>
        <CardHeader>
          <CardTitle>Project Tasks</CardTitle>
          <CardDescription>Manage tasks for &quot;{project.name}&quot; using the board below.</CardDescription>
        </CardHeader>
        <CardContent>
          {/* tasks SWR is now handled within KanbanBoard */}
          <KanbanBoard projectId={project.id} />
        </CardContent>
      </Card>
    </div>
  );
}
