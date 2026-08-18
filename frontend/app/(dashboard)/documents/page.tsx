'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { formatDate, getStatusColor } from '@/lib/utils';
import { Search, FileText, Clock } from 'lucide-react';

export default function DocumentsPage() {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  const { data, isLoading } = useQuery({
    queryKey: ['documents', search, filter],
    queryFn: () => documentsApi.list({ 
      search, 
      status: filter !== 'all' ? filter : undefined 
    }),
  });

  const documents = data?.data?.results || [];

  const statusOptions = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'verified', label: 'Verified' },
    { value: 'failed', label: 'Failed' },
    { value: 'expired', label: 'Expired' },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <p className="text-gray-600 mt-1">Manage compliance documents for candidates</p>
      </div>

      <Card>
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Input
              placeholder="Search documents..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="flex gap-2">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setFilter(option.value)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  filter === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-8">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto text-gray-300 mb-3" />
            <p>No documents found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc: any) => (
              <div key={doc.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-medium text-gray-900">{doc.document_type_display}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(doc.status)}`}>
                    {doc.status_display}
                  </span>
                </div>
                <p className="text-sm text-gray-600">Candidate: {doc.candidate_name}</p>
                <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                  <span>Issued: {formatDate(doc.issue_date)}</span>
                  <span>Expires: {formatDate(doc.expiry_date)}</span>
                </div>
                {doc.days_until_expiry !== null && doc.days_until_expiry !== undefined && (
                  <div className="mt-2 flex items-center gap-1 text-sm">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span className={doc.days_until_expiry < 30 ? 'text-red-600 font-medium' : 'text-gray-500'}>
                      {doc.days_until_expiry} days until expiry
                    </span>
                  </div>
                )}
                <div className="mt-3 text-xs text-gray-400">
                  v{doc.version} • {doc.is_current ? 'Current' : 'Archived'}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}