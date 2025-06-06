import ProjectList from '@/components/features/project/ProjectList';
import ProjectForm from '@/components/features/project/ProjectForm';
// Potentially a button to toggle ProjectForm visibility
// import { Button } from '@/components/ui/button';
// import { useState } from 'react'; (if client component for toggle)

export default function ProjectsPage() {
  // const [showCreateForm, setShowCreateForm] = useState(false); // If making form toggleable

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-white">My Projects</h1>
        {/* Add a button to toggle form visibility or navigate to a create page */}
        {/* <Button onClick={() => setShowCreateForm(!showCreateForm)}>
            {showCreateForm ? 'Cancel' : 'Create New Project'}
        </Button> */}
        {/* For now, always show the form above the list */}
        <div className="mb-8">
          <ProjectForm />
        </div>
        <ProjectList />
      </section>
    </div>
  );
}
