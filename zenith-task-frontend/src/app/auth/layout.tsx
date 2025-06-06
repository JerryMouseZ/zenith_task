import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'ZenithTask - Authentication',
  description: 'Login or Sign up to ZenithTask',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
          {children}
        </div>
      </body>
    </html>
  );
}
