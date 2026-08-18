'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { candidatesApi, auditApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Users, FileText, History, Bot, Plus, FileUp } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    candidates: 0,
    documents: 0,
    auditLogs: 0,
    aiExtractions: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch candidates count
        try {
          const candidatesRes = await candidatesApi.list({ page_size: 1 });
          setStats(prev => ({ ...prev, candidates: candidatesRes.data?.count || 0 }));
        } catch (err) {
          console.log('Candidates endpoint not available yet');
        }

        // Fetch audit logs count
        try {
          const auditRes = await auditApi.list({ page_size: 1 });
          setStats(prev => ({ ...prev, auditLogs: auditRes.data?.count || 0 }));
        } catch (err) {
          console.log('Audit endpoint not available yet');
        }
      } catch (err) {
        console.log('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statCards = [
    { 
      title: 'Candidates', 
      value: stats.candidates, 
      icon: Users, 
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      href: '/candidates'
    },
    { 
      title: 'Documents', 
      value: stats.documents, 
      icon: FileText, 
      color: 'bg-green-500',
      textColor: 'text-green-600',
      bgColor: 'bg-green-50',
      href: '/documents'
    },
    { 
      title: 'Audit Logs', 
      value: stats.auditLogs, 
      icon: History, 
      color: 'bg-purple-500',
      textColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      href: '/audit'
    },
    { 
      title: 'AI Extractions', 
      value: stats.aiExtractions, 
      icon: Bot, 
      color: 'bg-orange-500',
      textColor: 'text-orange-600',
      bgColor: 'bg-orange-50',
      href: '/ai'
    },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Welcome back, {user?.first_name || user?.username}!
        </p>
        <p className="text-sm text-gray-500">Tenant: {user?.tenant_name}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map(({ title, value, icon: Icon, color, textColor, bgColor, href }) => (
          <Link key={title} href={href}>
            <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 cursor-pointer">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 font-medium">{title}</p>
                  <p className={`text-3xl font-bold mt-2 ${textColor}`}>
                    {loading ? '...' : value}
                  </p>
                </div>
                <div className={`${color} p-3 rounded-xl`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link href="/candidates/new" className="block p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
              <div className="flex items-center gap-3">
                <Plus className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-700">Add New Candidate</p>
                  <p className="text-sm text-blue-600">Create a new candidate profile</p>
                </div>
              </div>
            </Link>
            <Link href="/ai" className="block p-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors">
              <div className="flex items-center gap-3">
                <FileUp className="h-5 w-5 text-purple-600" />
                <div>
                  <p className="font-medium text-purple-700">AI CV Analysis</p>
                  <p className="text-sm text-purple-600">Upload CV and extract data</p>
                </div>
              </div>
            </Link>
            <Link href="/documents" className="block p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-700">Expiring Documents</p>
                  <p className="text-sm text-green-600">Check documents expiring soon</p>
                </div>
              </div>
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3 text-sm">
            <p className="text-gray-500">Recent audit logs will appear here</p>
            <Link href="/audit" className="text-blue-600 hover:text-blue-700 font-medium inline-block">
              View all audit logs →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}