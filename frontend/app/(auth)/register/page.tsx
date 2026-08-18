'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { setAuthData, isAuthenticated, redirectTo } from '@/lib/auth';

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  tenant_name: z.string().min(1, 'Tenant name is required'),
  tenant_slug: z.string().optional(),
  role: z.enum(['admin', 'recruiter', 'viewer']),
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { 
      role: 'admin',
    },
  });

  const tenantName = watch('tenant_name');

  useEffect(() => {
    if (isAuthenticated()) {
      redirectTo('/dashboard');
    }
  }, []);

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  };

  const onSubmit = async (data: RegisterForm) => {
    setLoading(true);
    try {
      if (!data.tenant_slug) {
        data.tenant_slug = generateSlug(data.tenant_name);
      }
      
      const response = await authApi.register(data);
      console.log('Register response:', response.data);
      
      // Store auth data
      setAuthData(response.data);
      
      // Check if we have the required data
      const token = localStorage.getItem('access_token');
      const tenantId = localStorage.getItem('tenant_id');
      
      if (token && tenantId) {
        toast.success('Registration successful!');
        window.location.href = '/dashboard';
      } else if (response.data.user?.tenant_id) {
        localStorage.setItem('tenant_id', response.data.user.tenant_id);
        toast.success('Registration successful!');
        window.location.href = '/dashboard';
      } else {
        toast.error('Registration succeeded but missing tenant information');
        setLoading(false);
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      toast.error(error.response?.data?.error || 'Registration failed');
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
          <p className="mt-2 text-sm text-gray-600">Create your account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                placeholder="Choose a username"
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
                Email
              </label>
              <input
                type="email"
                placeholder="Enter your email"
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition ${
                  errors.email ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                {...register('email')}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                placeholder="Create a password"
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition ${
                  errors.password ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                {...register('password')}
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Organization / Tenant Name
              </label>
              <input
                type="text"
                placeholder="Enter your organization name"
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition ${
                  errors.tenant_name ? 'border-red-500 bg-red-50' : 'border-gray-300'
                }`}
                {...register('tenant_name')}
              />
              {errors.tenant_name && (
                <p className="mt-1 text-sm text-red-600">{errors.tenant_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tenant Slug (URL identifier)
              </label>
              <input
                type="text"
                placeholder="Auto-generated from tenant name"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                {...register('tenant_slug')}
              />
              {tenantName && (
                <p className="mt-1 text-xs text-gray-500">
                  Suggested: <span className="text-blue-600 font-mono">{generateSlug(tenantName)}</span>
                </p>
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
                  Creating account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-600 hover:text-blue-500 font-medium">
                Sign in
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