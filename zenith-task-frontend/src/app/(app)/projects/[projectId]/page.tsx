'use client';

import { useParams } from 'next/navigation';
import useSWR from 'swr';
import { Project, Task } from '@/types/api';
import { apiClient } from '@/lib/apiClient';
import ProjectDetailView from '@/components/features/project/ProjectDetailView';
// Placeholder for Task List / Kanban for this project
// import ProjectTaskList from '@/components/features/task/ProjectTaskList';
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

  // TODO: Add SWR for tasks, e.g., /tasks?project_id=${projectId}
  const { data: tasks, error: tasksError, isLoading: tasksIsLoading } =
    useSWR<Task[]>(projectId ? `/tasks/?project_id=${projectId}` : null, tasksFetcher); // Corrected query param format

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

  // Basic task list display (can be replaced with Kanban or more detailed list later)
  const renderTasks = () => {
    if (tasksIsLoading) return <p className="text-muted-foreground"><Loader2 className="inline-block h-4 w-4 animate-spin mr-1" /> Loading tasks...</p>;
    if (tasksError) return <p className="text-red-500">Error loading tasks: {tasksError.message}</p>; // Display task-specific error
    if (!tasks || tasks.length === 0) return <p className="text-muted-foreground">No tasks in this project yet.</p>;

    return (
      <div className="space-y-2 mt-4">
        <ul className="list-disc pl-5">
          {tasks.map(task => (
            <li key={task.id} className="text-sm">
              {task.title} - <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700">{task.status}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
         <Button asChild variant="outline" size="sm">
           <Link href="/projects">← Back to All Projects</Link>
         </Button>
      </div>

      <ProjectDetailView project={project} /> {/* Pass the fetched project here */}

      {/* Placeholder for where project tasks will be displayed, e.g., a Kanban board or task list */}
      <Card>
        <CardHeader>
          <CardTitle>Project Tasks</CardTitle>
          <CardDescription>Tasks associated with the project &quot;{project.name}&quot;.</CardDescription>
        </CardHeader>
        <CardContent>
          {renderTasks()}
          {/* Later, this could be: <ProjectTaskList projectId={project.id} /> */}
          {/* Or a Kanban board: <KanbanBoard projectId={project.id} /> */}
        </CardContent>
      </Card>
    </div>
  );
}
