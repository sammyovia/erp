import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User } from '@/types';
import { getUser, isAuthenticated, clearAuth, getToken, getTenantId } from '@/lib/auth';

export const useAuth = () => {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated()) {
      setUser(getUser());
    }
    setLoading(false);
  }, []);

  const logout = () => {
    clearAuth();
    setUser(null);
    router.push('/login');
  };

  return {
    user,
    loading,
    isAuthenticated: isAuthenticated(),
    logout,
    token: getToken(),
    tenantId: getTenantId(),
  };
};