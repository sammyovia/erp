'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { candidatesApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const candidateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  role_applied_for: z.string().min(1, 'Role is required'),
});

type CandidateForm = z.infer<typeof candidateSchema>;

export default function NewCandidatePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<CandidateForm>({
    resolver: zodResolver(candidateSchema),
  });

  const onSubmit = async (data: CandidateForm) => {
    setLoading(true);
    try {
      await candidatesApi.create(data);
      toast.success('Candidate created successfully!');
      router.push('/candidates');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to create candidate');
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/candidates" className="text-gray-500 hover:text-gray-700">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Add New Candidate</h1>
          <p className="text-gray-600 mt-1">Create a new candidate profile</p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            label="Full Name"
            placeholder="Enter candidate's full name"
            fullWidth
            {...register('name')}
            error={errors.name?.message}
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="Enter candidate's email"
            fullWidth
            {...register('email')}
            error={errors.email?.message}
          />

          <Input
            label="Role Applied For"
            placeholder="e.g. Senior Developer"
            fullWidth
            {...register('role_applied_for')}
            error={errors.role_applied_for?.message}
          />

          <div className="flex gap-4 pt-4">
            <Button type="submit" loading={loading}>
              Create Candidate
            </Button>
            <Link href="/candidates">
              <Button variant="outline" type="button">
                Cancel
              </Button>
            </Link>
          </div>
        </form>
      </Card>
    </div>
  );
}