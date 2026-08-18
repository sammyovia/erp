'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidatesApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { formatDate } from '@/lib/utils';
import { Plus, Search, Eye, Edit, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function CandidatesPage() {
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['candidates', search],
    queryFn: () => candidatesApi.list({ search }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => candidatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      toast.success('Candidate deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to delete candidate');
    },
  });

  const candidates = data?.data?.results || [];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Candidates</h1>
          <p className="text-gray-600 mt-1">Manage your candidates and their compliance documents</p>
        </div>
        <Link href="/candidates/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Candidate
          </Button>
        </Link>
      </div>

      <Card>
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1">
            <Input
              placeholder="Search candidates by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full"
            />
          </div>
          <Button variant="outline">
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">Loading candidates...</div>
        ) : candidates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No candidates found. Click "Add Candidate" to create one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Role</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Documents</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Created</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {candidates.map((candidate: any) => (
                  <tr key={candidate.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{candidate.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{candidate.email}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{candidate.role_applied_for}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                        {candidate.document_count || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(candidate.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Link href={`/candidates/${candidate.id}`}>
                          <button className="p-1 text-blue-600 hover:bg-blue-50 rounded">
                            <Eye className="h-4 w-4" />
                          </button>
                        </Link>
                        <Link href={`/candidates/${candidate.id}/edit`}>
                          <button className="p-1 text-gray-600 hover:bg-gray-50 rounded">
                            <Edit className="h-4 w-4" />
                          </button>
                        </Link>
                        <button 
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          onClick={() => {
                            if (confirm('Delete this candidate?')) {
                              deleteMutation.mutate(candidate.id);
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}