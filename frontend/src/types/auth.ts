export interface LoginCredentials {
  identifier: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserSession {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role_code: string;
  role_name: string;
  hierarchy_level?: number;
  permissions: string[];
  sucursal_id: string | null;
  sucursal_nombre: string | null;
  is_superuser: boolean;
}
