export interface Sucursal {
  id: string;
  nombre: string;
  codigo: string;
  activa: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SucursalCreate {
  nombre: string;
  codigo: string;
  activa: boolean;
}

export interface Permission {
  id: string;
  code: string;
  module: string;
  description?: string;
}

export interface Role {
  id: string;
  code: string;
  name: string;
  description?: string;
  hierarchy_level?: number;
  is_system: boolean;
  permissions: Permission[];
}

export interface RoleCreate {
  code: string;
  name: string;
  description?: string;
  hierarchy_level?: number;
  permission_ids?: string[];
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  hierarchy_level?: number;
  permission_ids?: string[];
}

export interface UserSummary {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role_code?: string;
  sucursal_nombre?: string;
  is_active: boolean;
}

export interface UserDetail {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login_at?: string | null;
  role?: Role;
  sucursal?: Sucursal | null;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_superuser?: boolean;
  role_id: string;
  sucursal_id?: string | null;
}
