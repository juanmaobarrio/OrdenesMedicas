import api from './api';
import { Permission, Role, RoleCreate, RoleUpdate, Sucursal, SucursalCreate, UserCreate, UserDetail } from '../types/users';


export const usersService = {
  // Sucursales
  async listSucursales(onlyActive = false): Promise<Sucursal[]> {
    const response = await api.get<Sucursal[]>('/sucursales', {
      params: { only_active: onlyActive },
    });
    return response.data;
  },

  async createSucursal(dto: SucursalCreate): Promise<Sucursal> {
    const response = await api.post<Sucursal>('/sucursales', dto);
    return response.data;
  },

  // Roles y Permisos
  async listRoles(): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles');
    return response.data;
  },

  async listPermissions(): Promise<Permission[]> {
    const response = await api.get<Permission[]>('/permissions');
    return response.data;
  },

  async createRole(dto: RoleCreate): Promise<Role> {
    const response = await api.post<Role>('/roles', dto);
    return response.data;
  },

  async updateRole(id: string, dto: RoleUpdate): Promise<Role> {
    const response = await api.put<Role>(`/roles/${id}`, dto);
    return response.data;
  },

  async deleteRole(id: string): Promise<void> {
    await api.delete(`/roles/${id}`);
  },

  // Users
  async listUsers(sucursalId?: string, roleId?: string, isActive?: boolean): Promise<UserDetail[]> {
    const response = await api.get<UserDetail[]>('/users', {
      params: { sucursal_id: sucursalId, role_id: roleId, is_active: isActive },
    });
    return response.data;
  },

  async createUser(dto: UserCreate): Promise<UserDetail> {
    const response = await api.post<UserDetail>('/users', dto);
    return response.data;
  },

  async getUser(id: string): Promise<UserDetail> {
    const response = await api.get<UserDetail>(`/users/${id}`);
    return response.data;
  },

  async updateUser(id: string, dto: Partial<UserCreate>): Promise<UserDetail> {
    const response = await api.put<UserDetail>(`/users/${id}`, dto);
    return response.data;
  },

  async toggleActiveUser(id: string): Promise<UserDetail> {
    const response = await api.patch<UserDetail>(`/users/${id}/toggle-active`);
    return response.data;
  },

  async resetPasswordByAdmin(id: string, new_password: string): Promise<void> {
    await api.post(`/users/${id}/reset-password`, { new_password });
  },
};
