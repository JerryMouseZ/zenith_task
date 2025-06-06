'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useUserStore } from '@/store/userStore';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, token } = useUserStore((state) => ({
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    token: state.token, // Access token directly to see if it's checked
  }));

  useEffect(() => {
    // Don't redirect while initial auth check is loading
    if (isLoading) {
      return;
    }

    // If not authenticated and not on a public path (though this guard is for protected routes)
    // redirect to login.
    if (!isAuthenticated) {
      // Store the intended path to redirect after login
      // Avoid redirect loops if already on login page (though this guard shouldn't be on /login)
      if (pathname !== '/login') {
        // router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
        router.replace('/login'); // Simpler redirect for now
      }
    }
  }, [isAuthenticated, isLoading, router, pathname]);

  // If loading, you can show a loader, or nothing if layout handles it
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading...</p> {/* Replace with a proper spinner/loader component */}
      </div>
    );
  }

  // If authenticated, render the children (the protected page content)
  if (isAuthenticated) {
    return <>{children}</>;
  }

  // If not authenticated and not loading, user will be redirected by useEffect.
  // Return null or a loader while redirect is happening to prevent brief flash of content.
  return (
    <div className="flex items-center justify-center h-screen">
      <p>Redirecting to login...</p>
    </div>
  );
}
