import axios from 'axios';
import { getToken, getTenantId } from './auth';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth headers
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    const tenantId = getTenantId();
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('tenant_id');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action');
    }
    
    if (error.response?.status === 404) {
      toast.error('Resource not found');
    }
    
    if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.');
    }
    
    return Promise.reject(error);
  }
);

// Auth API - Matches your backend exactly
export const authApi = {
  register: (data: any) => api.post('/auth/register/', data),
  login: (data: any) => api.post('/auth/login/', data),
  logout: () => {
    const refresh = localStorage.getItem('refresh_token');
    return api.post('/auth/logout/', { refresh });
  },
  refresh: (refresh: string) => api.post('/auth/token/refresh/', { refresh }),
  verify: (token: string) => api.post('/auth/token/verify/', { token }),
  profile: () => api.get('/auth/profile/'),
  changePassword: (data: any) => api.post('/auth/change-password/', data),
};

// Candidates API - Matches your backend exactly
export const candidatesApi = {
  list: (params?: any) => api.get('/candidates/', { params }),
  create: (data: any) => api.post('/candidates/', data),
  get: (id: string) => api.get(`/candidates/${id}/`),
  update: (id: string, data: any) => api.patch(`/candidates/${id}/`, data),
  delete: (id: string) => api.delete(`/candidates/${id}/`),
  addDocument: (id: string, data: any) => api.post(`/candidates/${id}/add_document/`, data),
  expiringDocuments: () => api.get('/candidates/expiring_documents/'),
};

// Documents API - Matches your backend exactly
export const documentsApi = {
  list: (params?: any) => api.get('/documents/', { params }),
  create: (data: any) => api.post('/documents/', data),
  get: (id: string) => api.get(`/documents/${id}/`),
  update: (id: string, data: any) => api.patch(`/documents/${id}/`, data),
  delete: (id: string) => api.delete(`/documents/${id}/`),
  versions: (id: string) => api.get(`/documents/${id}/versions/`),
  expiringSoon: () => api.get('/documents/expiring_soon/'),
};

// AI API - Matches your backend exactly
export const aiApi = {
  analyzeCV: (file: File, candidateId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (candidateId) {
      formData.append('candidate_id', candidateId);
    }
    return api.post('/ai/cv-analyze/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  listExtractions: (params?: any) => api.get('/ai/extractions/', { params }),
  confirmExtraction: (id: string, data: any) => 
    api.post(`/ai/extractions/${id}/confirm/`, data),
};

// Audit API - Matches your backend exactly
export const auditApi = {
  list: (params?: any) => api.get('/audit/logs/', { params }),
  stats: () => api.get('/audit/stats/'),
  get: (id: string) => api.get(`/audit/logs/${id}/`),
  byRecord: (recordType: string, recordId: string) =>
    api.get('/audit/logs/by_record/', { params: { record_type: recordType, record_id: recordId } }),
  byActor: (actorId: string) =>
    api.get('/audit/logs/by_actor/', { params: { actor_id: actorId } }),
  recent: (days: number = 7) => api.get('/audit/logs/recent/', { params: { days } }),
  summary: () => api.get('/audit/logs/summary/'),
};

// Tenants API - Matches your backend exactly
export const tenantsApi = {
  list: () => api.get('/tenants/'),
  get: (id: string) => api.get(`/tenants/${id}/`),
  create: (data: any) => api.post('/tenants/', data),
  update: (id: string, data: any) => api.patch(`/tenants/${id}/`, data),
  delete: (id: string) => api.delete(`/tenants/${id}/`),
  users: (id: string) => api.get(`/tenants/${id}/users/`),
  addUser: (id: string, data: any) => api.post(`/tenants/${id}/add_user/`, data),
  removeUser: (id: string, data: any) => api.post(`/tenants/${id}/remove_user/`, data),
  updateUserRole: (id: string, data: any) => api.put(`/tenants/${id}/update_user_role/`, data),
  switch: (tenantId: string) => api.post('/tenants/switch/', { tenant_id: tenantId }),
  myTenants: () => api.get('/tenants/my_tenants/'), // Note: This is at /tenants/{id}/my_tenants/ in your backend
};

export default api;