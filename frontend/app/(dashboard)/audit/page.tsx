'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { formatDate, getActionColor } from '@/lib/utils';
import { Search, Filter } from 'lucide-react';

export default function AuditPage() {
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('all');

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', search, actionFilter],
    queryFn: () => auditApi.list({ 
      search, 
      action: actionFilter !== 'all' ? actionFilter : undefined 
    }),
  });

  const logs = data?.data?.results || [];

  const actionOptions = [
    { value: 'all', label: 'All' },
    { value: 'CREATE', label: 'Create' },
    { value: 'UPDATE', label: 'Update' },
    { value: 'DELETE', label: 'Delete' },
    { value: 'READ', label: 'Read' },
    { value: 'VERIFY', label: 'Verify' },
    { value: 'LOGIN', label: 'Login' },
    { value: 'LOGOUT', label: 'Logout' },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600 mt-1">
          Immutable audit trail of all system activities
        </p>
      </div>

      <Card>
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Input
              placeholder="Search audit logs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {actionOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-8">Loading audit logs...</div>
        ) : logs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No audit logs found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Action</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Record Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Record ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Actor</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.map((log: any) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getActionColor(log.action)}`}>
                        {log.action_display || log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{log.record_type}</td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-500">{log.record_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">User #{log.actor_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(log.created_at)}</td>
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