import api from './api';
import {
  EstadoOrdenConfig,
  EstadoOrdenConfigCreate,
  EstadoOrdenConfigUpdate,
  MotivoCancelacion,
  MotivoCancelacionCreate,
  MotivoCancelacionUpdate,
} from '../types/ordenes';

export const configService = {
  // Motivos de Cancelación
  async listMotivosCancelacion(onlyActive = false): Promise<MotivoCancelacion[]> {
    const response = await api.get<MotivoCancelacion[]>('/config/motivos-cancelacion', {
      params: { only_active: onlyActive },
    });
    return response.data;
  },

  async createMotivoCancelacion(dto: MotivoCancelacionCreate): Promise<MotivoCancelacion> {
    const response = await api.post<MotivoCancelacion>('/config/motivos-cancelacion', dto);
    return response.data;
  },

  async updateMotivoCancelacion(id: string, dto: MotivoCancelacionUpdate): Promise<MotivoCancelacion> {
    const response = await api.put<MotivoCancelacion>(`/config/motivos-cancelacion/${id}`, dto);
    return response.data;
  },

  async toggleActiveMotivoCancelacion(id: string): Promise<MotivoCancelacion> {
    const response = await api.patch<MotivoCancelacion>(`/config/motivos-cancelacion/${id}/toggle-active`);
    return response.data;
  },

  async deleteMotivoCancelacion(id: string): Promise<void> {
    await api.delete(`/config/motivos-cancelacion/${id}`);
  },

  // Estados de Orden Configurables
  async listEstados(onlyActive = false): Promise<EstadoOrdenConfig[]> {
    const response = await api.get<EstadoOrdenConfig[]>('/config/estados', {
      params: { only_active: onlyActive },
    });
    return response.data;
  },

  async createEstado(dto: EstadoOrdenConfigCreate): Promise<EstadoOrdenConfig> {
    const response = await api.post<EstadoOrdenConfig>('/config/estados', dto);
    return response.data;
  },

  async updateEstado(id: number, dto: EstadoOrdenConfigUpdate): Promise<EstadoOrdenConfig> {
    const response = await api.put<EstadoOrdenConfig>(`/config/estados/${id}`, dto);
    return response.data;
  },

  async toggleActiveEstado(id: number): Promise<EstadoOrdenConfig> {
    const response = await api.patch<EstadoOrdenConfig>(`/config/estados/${id}/toggle-active`);
    return response.data;
  },

  async deleteEstado(id: number): Promise<void> {
    await api.delete(`/config/estados/${id}`);
  },
};
