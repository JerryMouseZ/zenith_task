'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/auth/login');
  }, [router]);

  // It's good practice to return some minimal UI, e.g., a loading message,
  // as the redirect might take a moment.
  return <p>Loading...</p>;
}
