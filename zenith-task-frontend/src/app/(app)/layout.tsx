import type { Metadata } from 'next';
import Navbar from '@/components/layout/Navbar';
import Sidebar from '@/components/layout/Sidebar';
import AuthGuard from '@/components/layout/AuthGuard'; // Import AuthGuard

export const metadata: Metadata = {
  title: 'ZenithTask',
  description: 'Your intelligent task management assistant.',
};

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // AuthGuard wraps the protected content.
    // The AuthGuard itself will show a loading state or redirect.
    // The actual layout (Sidebar, Navbar) will be shown by AuthGuard when authenticated.
    <AuthGuard>
      <div className="flex h-screen bg-gray-100 dark:bg-gray-950">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-950 p-6">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
