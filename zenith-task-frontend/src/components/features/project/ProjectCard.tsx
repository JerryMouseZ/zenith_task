'use client';

import Link from 'next/link';
import { Project } from '@/types/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Archive, Edit, Palette } from 'lucide-react'; // Icons

interface ProjectCardProps {
  project: Project;
  // onEdit: (project: Project) => void; // For later editing
  // onArchive: (project: Project) => void; // For later archiving
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle className="hover:text-primary">
            <Link href={`/projects/${project.id}`}>{project.name}</Link>
          </CardTitle>
          {project.color_hex && (
            <span className="w-6 h-6 rounded-full inline-block" style={{ backgroundColor: project.color_hex }} title={project.color_hex}></span>
          )}
        </div>
        {project.description && (
          <CardDescription className="mt-1 line-clamp-2">{project.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-grow">
        {/* Placeholder for more project details, e.g., task count, progress */}
        <p className="text-sm text-muted-foreground">
          View: {project.view_preference || 'Default'}
        </p>
        <p className="text-sm text-muted-foreground">
          Created: {new Date(project.created_at).toLocaleDateString()}
        </p>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
        {/* <Button variant="outline" size="sm" onClick={() => onEdit(project)}>
          <Edit className="h-4 w-4 mr-1" /> Edit
        </Button>
        <Button variant="outline" size="sm" onClick={() => onArchive(project)} title={project.is_archived ? "Unarchive" : "Archive"}>
          <Archive className="h-4 w-4 mr-1" /> {project.is_archived ? "Unarchive" : "Archive"}
        </Button> */}
        <Button variant="ghost" size="sm" asChild>
          <Link href={`/projects/${project.id}/settings`} title="Project Settings">
            <Edit className="h-4 w-4" />
          </Link>
        </Button>
         <Button variant="ghost" size="sm" asChild>
          <Link href={`/projects/${project.id}`} title="View Project">
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
