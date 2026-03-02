export interface User {
  id: number;
  email: string;
  base_currency: string;
  default_workspace_id?: string | null;
  tutorial_version: number;
  role?: string;
}

export interface UserCreate {
  email: string;
  password: string;
  base_currency?: string;
}

export interface UserUpdate {
  email?: string;
  base_currency?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}
