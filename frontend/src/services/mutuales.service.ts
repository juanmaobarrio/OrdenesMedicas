import api from './api';
import { ObraSocial, ObraSocialCreate, ObraSocialUpdate } from '../types/mutuales';

export const mutualesService = {
  async list(onlyActive = true): Promise<ObraSocial[]> {
    const response = await api.get<ObraSocial[]>('/mutuales', {
      params: { only_active: onlyActive },
    });
    return response.data;
  },

  async getById(id: string): Promise<ObraSocial> {
    const response = await api.get<ObraSocial>(`/mutuales/${id}`);
    return response.data;
  },

  async create(dto: ObraSocialCreate): Promise<ObraSocial> {
    const response = await api.post<ObraSocial>('/mutuales', dto);
    return response.data;
  },

  async update(id: string, dto: ObraSocialUpdate): Promise<ObraSocial> {
    const response = await api.put<ObraSocial>(`/mutuales/${id}`, dto);
    return response.data;
  },

  async toggleActive(id: string): Promise<ObraSocial> {
    const response = await api.patch<ObraSocial>(`/mutuales/${id}/toggle-active`);
    return response.data;
  },

  async getValorApb(): Promise<{ valor_apb: number; descripcion?: string; updated_at?: string }> {
    const response = await api.get('/config/apb');
    return response.data;
  },

  async updateValorApb(valor_apb: number): Promise<{ valor_apb: number; descripcion?: string; updated_at?: string }> {
    const response = await api.put('/config/apb', { valor_apb });
    return response.data;
  },
};
