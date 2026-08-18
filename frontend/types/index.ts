export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  user_count?: number;
  created_at: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
}

export interface Candidate {
  id: string;
  tenant: string;
  tenant_name?: string;
  name: string;
  email: string;
  role_applied_for: string;
  document_count: number;
  documents?: Document[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  candidate: string;
  candidate_name?: string;
  document_type: string;
  document_type_display: string;
  issue_date: string;
  expiry_date: string;
  status: 'pending' | 'verified' | 'failed' | 'expired';
  status_display: string;
  file_url?: string;
  version: number;
  is_current: boolean;
  days_until_expiry?: number;
  created_at: string;
  updated_at: string;
}

export interface AIExtraction {
  id: string;
  tenant: string;
  tenant_name?: string;
  candidate: string | null;
  candidate_name?: string;
  candidate_email?: string;
  extracted_data: {
    full_name: string;
    email: string;
    skills: string[];
    years_experience: number;
    certifications: string[];
    role?: string;
  };
  model_used: string;
  status: 'pending_confirmation' | 'confirmed' | 'rejected';
  status_display: string;
  confidence_score: number | null;
  confirmed_at: string | null;
  confirmed_by: string | null;
  confirmed_by_username?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  tenant: string;
  tenant_name?: string;
  actor_id: number;
  action: string;
  action_display: string;
  record_type: string;
  record_id: string;
  data: any;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
  tenant: {
    id: string;
    name: string;
    slug: string;
    role: string;
  };
}

export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}