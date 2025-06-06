'use client'; // Make it a client component to use hooks

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useUserStore } from '@/store/userStore'; // Import user store

export default function Navbar() {
  const router = useRouter();
  const { user, logout, isAuthenticated } = useUserStore((state) => ({
    user: state.user,
    logout: state.logout,
    isAuthenticated: state.isAuthenticated,
  }));

  const handleLogout = async () => {
    await logout();
    router.push('/login'); // Redirect to login page after logout
  };

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/dashboard" className="text-xl font-bold text-gray-800 dark:text-white">
          ZenithTask
        </Link>
        <div>
          {isAuthenticated ? (
            <div className="flex items-center space-x-4">
              <span className="text-gray-700 dark:text-gray-300">
                {user?.full_name || user?.email || 'User'}
              </span>
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          ) : (
            <Button variant="outline" onClick={() => router.push('/login')}>
              Login
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
}
