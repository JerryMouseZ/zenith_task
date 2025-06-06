'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { setAuthToken } from '@/lib/apiClient'; // To set token
import { Token } from '@/types/api';
import { useUserStore } from '@/store/userStore';

// Define the schema for the login form
const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
});

type LoginFormInputs = z.infer<typeof loginSchema>;

export default function LoginForm() {
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setToken: storeSetToken, checkAuth } = useUserStore((state) => ({ setToken: state.setToken, checkAuth: state.checkAuth }));

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit: SubmitHandler<LoginFormInputs> = async (data) => {
    setIsLoading(true);
    setApiError(null);

    if (data.email === 'devmock@example.com') {
      // Mock login flow
      storeSetToken('mock-auth-token');
      await checkAuth(); // Setup user state
      router.push('/dashboard');
      setIsLoading(false); // Ensure loading state is reset
      return; // Skip API call
    }

    // FastAPI's OAuth2PasswordRequestForm expects 'username' and 'password' as form fields.
    // We will use a direct fetch call for this specific endpoint to send form data.
    const formData = new URLSearchParams();
    formData.append('username', data.email); // API expects 'username' for email
    formData.append('password', data.password);

    try {
      const response = await fetch('/api/auth/token', { // Assuming Next.js proxy or direct backend URL
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed. Please check your credentials.' }));
        throw new Error(errorData.detail || 'Login failed. Please check your credentials.');
      }

      const tokenData: Token = await response.json();
      storeSetToken(tokenData.access_token);
      await checkAuth();

      // TODO: Update user state in global store (e.g., Zustand) if needed

      router.push('/dashboard'); // Redirect to dashboard on successful login
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('An unexpected error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Login</CardTitle>
        <CardDescription>Enter your email below to login to your account.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="m@example.com"
              {...register('email')}
              className={errors.email ? 'border-red-500' : ''}
            />
            {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              {...register('password')}
              className={errors.password ? 'border-red-500' : ''}
            />
            {errors.password && <p className="text-sm text-red-600">{errors.password.message}</p>}
          </div>
          {apiError && <p className="text-sm text-red-600">{apiError}</p>}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="text-sm">
        {/* Link to Signup page will be added later */}
        {/* Don't have an account? <Link href="/signup" className="underline">Sign up</Link> */}
      </CardFooter>
    </Card>
  );
}
