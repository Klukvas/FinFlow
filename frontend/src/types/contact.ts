export interface ContactCreate {
  name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  address?: string | null;
  notes?: string | null;
}

export interface ContactUpdate {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  address?: string | null;
  notes?: string | null;
}

export interface ContactResponse {
  id: number;
  user_id: number;
  name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  address?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactSummary {
  id: number;
  name: string;
  company?: string | null;
  debts_count: number;
  total_debt_amount: number;
}
