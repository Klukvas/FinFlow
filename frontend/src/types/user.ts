export interface User {
  id: number;
  email: string;
  username: string;
  base_currency: string;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  base_currency?: string;
}

export interface UserUpdate {
  email?: string;
  username?: string;
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
