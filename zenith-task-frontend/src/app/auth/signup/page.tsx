import SignupForm from '@/components/features/auth/SignupForm';
import Link from 'next/link';

export default function SignupPage() {
  return (
    <div className="w-full max-w-md space-y-6">
      <SignupForm />
      <p className="text-center text-sm text-gray-600 dark:text-gray-400">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Login
        </Link>
      </p>
    </div>
  );
}
