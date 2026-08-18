'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { setAuthData, isAuthenticated, redirectTo } from '@/lib/auth';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  // Check if already authenticated
  useEffect(() => {
    if (isAuthenticated()) {
      redirectTo('/dashboard');
    }
  }, []);

  const onSubmit = async (data: LoginForm) => {
    setLoading(true);
    try {
      const response = await authApi.login(data);
      console.log('Login response:', response.data);
      
      // Store auth data
      setAuthData(response.data);
      
      // Check if we have the required data
      const token = localStorage.getItem('access_token');
      const tenantId = localStorage.getItem('tenant_id');
      
      if (token && tenantId) {
        toast.success('Login successful!');
        // Use window.location for hard redirect
        window.location.href = '/dashboard';
      } else {
        // If tenant ID is missing, try to get it from the response
        if (response.data.user?.tenant_id) {
          localStorage.setItem('tenant_id', response.data.user.tenant_id);
          toast.success('Login successful!');
          window.location.href = '/dashboard';
        } else {
          toast.error('Missing tenant information. Please contact support.');
          setLoading(false);
        }
      }
    } catch (error: any) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.error || 'Login failed');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <span className="text-2xl font-bold text-white">E3</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">E3OS Platform</h2>
          <p className="mt-2 text-sm text-gray-600">Sign in to your account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                placeholder="Enter your username"
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition ${
                  errors.username ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                {...register('username')}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                placeholder="Enter your password"
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition ${
                  errors.password ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                {...register('password')}
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link href="/register" className="text-blue-600 hover:text-blue-500 font-medium">
                Register here
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            © {new Date().getFullYear()} E3OS Platform. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}