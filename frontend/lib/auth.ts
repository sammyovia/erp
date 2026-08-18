import { User, AuthResponse } from '@/types';

export const setAuthData = (data: any) => {
  if (typeof window === 'undefined') return;
  
  try {
    console.log('Setting auth data:', data);
    
    // Store tokens
    if (data.access) {
      localStorage.setItem('access_token', data.access);
    }
    if (data.refresh) {
      localStorage.setItem('refresh_token', data.refresh);
    }
    
    // Handle tenant ID - could be in different places
    let tenantId = null;
    if (data.tenant?.id) {
      tenantId = data.tenant.id;
    } else if (data.user?.tenant_id) {
      tenantId = data.user.tenant_id;
    } else if (data.tenant_id) {
      tenantId = data.tenant_id;
    }
    
    if (tenantId) {
      localStorage.setItem('tenant_id', tenantId);
      console.log('Tenant ID stored:', tenantId);
    } else {
      console.warn('No tenant ID found in response:', data);
    }
    
    // Store user data
    if (data.user) {
      localStorage.setItem('user', JSON.stringify(data.user));
      console.log('User stored:', data.user);
    }
    
    // Verify storage worked
    console.log('Token stored:', !!localStorage.getItem('access_token'));
    console.log('Tenant ID stored:', !!localStorage.getItem('tenant_id'));
    console.log('User stored:', !!localStorage.getItem('user'));
    
  } catch (error) {
    console.error('Failed to store auth data:', error);
  }
};

export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
};

export const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
};

export const getTenantId = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('tenant_id');
};

export const getUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

export const clearAuth = () => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('tenant_id');
  localStorage.removeItem('user');
};

export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  const token = getToken();
  const tenantId = getTenantId();
  return !!token && !!tenantId;
};

export const redirectTo = (path: string) => {
  if (typeof window !== 'undefined') {
    window.location.href = path;
  }
};