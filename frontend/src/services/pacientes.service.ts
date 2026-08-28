import api from './api';
import {
  Paciente,
  PacienteCreate,
  PacientePaginatedResponse,
  PacienteSearchResult,
} from '../types/pacientes';

export const pacientesService = {
  async list(params: {
    skip?: number;
    limit?: number;
    search?: string;
    obra_social?: string;
    only_active?: boolean;
  }): Promise<PacientePaginatedResponse> {
    const response = await api.get<PacientePaginatedResponse>('/pacientes', { params });
    return response.data;
  },

  async search(query: string, limit = 10): Promise<PacienteSearchResult[]> {
    const response = await api.get<PacienteSearchResult[]>('/pacientes/search', {
      params: { q: query, limit },
    });
    return response.data;
  },

  async getById(id: string): Promise<Paciente> {
    const response = await api.get<Paciente>(`/pacientes/${id}`);
    return response.data;
  },

  async getByDocumento(documento: string): Promise<Paciente> {
    const response = await api.get<Paciente>(`/pacientes/documento/${documento}`);
    return response.data;
  },

  async create(dto: PacienteCreate): Promise<Paciente> {
    const response = await api.post<Paciente>('/pacientes', dto);
    return response.data;
  },

  async update(id: string, dto: Partial<PacienteCreate>): Promise<Paciente> {
    const response = await api.put<Paciente>(`/pacientes/${id}`, dto);
    return response.data;
  },
};
