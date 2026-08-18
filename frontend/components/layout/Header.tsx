'use client';

import { useAuth } from '@/hooks/useAuth';

export const Header = () => {
  const { user } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">
          {user?.tenant_name || 'Dashboard'}
        </h2>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {user?.first_name || user?.username || 'User'}
          </span>
          <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
            {user?.role || 'Role'}
          </span>
        </div>
      </div>
    </header>
  );
};