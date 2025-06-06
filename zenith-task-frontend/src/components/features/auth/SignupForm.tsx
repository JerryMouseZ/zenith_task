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
import { registerUser, setAuthToken } from '@/lib/apiClient'; // Using registerUser and setAuthToken
import { UserCreate, User, Token } from '@/types/api';
import { useUserStore } from '@/store/userStore';

// Define the schema for the signup form
const signupSchema = z.object({
  fullName: z.string().min(2, { message: 'Full name must be at least 2 characters' }).optional().or(z.literal('')),
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'], // path to field that gets the error
});

type SignupFormInputs = z.infer<typeof signupSchema>;

export default function SignupForm() {
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setToken: storeSetToken, checkAuth } = useUserStore((state) => ({ setToken: state.setToken, checkAuth: state.checkAuth }));

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormInputs>({
    resolver: zodResolver(signupSchema),
  });

  const onSubmit: SubmitHandler<SignupFormInputs> = async (data) => {
    setIsLoading(true);
    setApiError(null);

    const userData: UserCreate = {
      email: data.email,
      password: data.password,
      full_name: data.fullName || null,
      // avatar_url and preferences can be added later if needed
    };

    try {
      // Step 1: Register the user
      const registeredUser: User = await registerUser(userData);
      console.log('User registered:', registeredUser);

      // Auto-login removed. Set success message and redirect to login.
      setApiError("Registration successful! Please log in to continue."); // Using apiError to display this message
      setIsLoading(false); // Stop loading before redirect
      router.push('/auth/login');
      // No return needed here as it's the end of the try block for the success path.
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('An unexpected error occurred during signup.');
      }
      setIsLoading(false); // Ensure loading is stopped on error
    }
    // The finally block for setIsLoading(false) from original code is removed
    // as it's now handled in both success and error paths of the try-catch.
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Create an account</CardTitle>
        <CardDescription>Enter your details below to create your account.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name (Optional)</Label>
            <Input
              id="fullName"
              type="text"
              placeholder="John Doe"
              {...register('fullName')}
              className={errors.fullName ? 'border-red-500' : ''}
            />
            {errors.fullName && <p className="text-sm text-red-600">{errors.fullName.message}</p>}
          </div>
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
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              {...register('confirmPassword')}
              className={errors.confirmPassword ? 'border-red-500' : ''}
            />
            {errors.confirmPassword && <p className="text-sm text-red-600">{errors.confirmPassword.message}</p>}
          </div>
          {apiError && <p className="text-sm text-red-600">{apiError}</p>}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Creating account...' : 'Create account'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
