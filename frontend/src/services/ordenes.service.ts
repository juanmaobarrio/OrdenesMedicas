import api from './api';
import {
  AdjuntoOrden,
  AuditoriaSolicitud,
  EstadoOrden,
  OrdenLlamadaPendienteItem,
  OrdenMedicaCreate,
  OrdenMedicaDetail,
  OrdenMedicaListItem,
  RegistroLlamada,
  ResultadoLlamada,
  TipoLlamada,
} from '../types/ordenes';

export interface ListOrdenesParams {
  skip?: number;
  limit?: number;
  estado?: EstadoOrden;
  sucursal_id?: string;
  paciente_id?: string;
  auditor_id?: string;
  mutual?: string;
  search?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface ListOrdenesResponse {
  items: OrdenMedicaListItem[];
  total: number;
  skip: number;
  limit: number;
}

export const ordenesService = {
  async list(params: ListOrdenesParams): Promise<ListOrdenesResponse> {
    const response = await api.get<ListOrdenesResponse>('/ordenes', { params });
    return response.data;
  },

  async getById(id: string): Promise<OrdenMedicaDetail> {
    const response = await api.get<OrdenMedicaDetail>(`/ordenes/${id}`);
    return response.data;
  },

  async create(dto: OrdenMedicaCreate): Promise<OrdenMedicaDetail> {
    const response = await api.post<OrdenMedicaDetail>('/ordenes', dto);
    return response.data;
  },

  async update(id: string, dto: Partial<OrdenMedicaCreate>): Promise<OrdenMedicaDetail> {
    const response = await api.put<OrdenMedicaDetail>(`/ordenes/${id}`, dto);
    return response.data;
  },

  async cambiarEstado(
    id: string,
    nuevo_estado: EstadoOrden,
    motivo?: string,
    motivo_cancelacion_id?: string | null,
    observacion_resultado?: string | null
  ): Promise<OrdenMedicaDetail> {
    const response = await api.post<OrdenMedicaDetail>(`/ordenes/${id}/estado`, {
      nuevo_estado,
      motivo,
      motivo_cancelacion_id,
      observacion_resultado,
    });
    return response.data;
  },

  async asignarAuditor(id: string, auditor_id?: string | null): Promise<OrdenMedicaDetail> {
    const response = await api.post<OrdenMedicaDetail>(`/ordenes/${id}/asignar-auditor`, {
      auditor_id,
    });
    return response.data;
  },

  // Solicitudes de auditoria
  async crearSolicitud(
    ordenId: string,
    motivo_solicitud: string,
    mensaje_auditor: string,
    es_informativa: boolean = false
  ): Promise<AuditoriaSolicitud> {
    const response = await api.post<AuditoriaSolicitud>(`/ordenes/${ordenId}/solicitudes`, {
      motivo_solicitud,
      mensaje_auditor,
      es_informativa,
    });
    return response.data;
  },

  async responderSolicitud(
    solicitudId: string,
    respuesta_operador: string
  ): Promise<AuditoriaSolicitud> {
    const response = await api.post<AuditoriaSolicitud>(
      `/ordenes/solicitudes/${solicitudId}/responder`,
      { respuesta_operador }
    );
    return response.data;
  },

  // Llamadas pendientes
  async listLlamadasPendientes(sucursalId?: string): Promise<OrdenLlamadaPendienteItem[]> {
    const response = await api.get<OrdenLlamadaPendienteItem[]>('/ordenes/llamadas-pendientes', {
      params: { sucursal_id: sucursalId },
    });
    return response.data;
  },

  async registrarLlamada(
    ordenId: string,
    data: {
      tipo_llamada: TipoLlamada;
      resultado: ResultadoLlamada;
      observaciones?: string;
      completar_aviso_pendiente?: boolean;
    }
  ): Promise<RegistroLlamada> {
    const response = await api.post<RegistroLlamada>(
      `/ordenes/${ordenId}/registrar-llamada`,
      data
    );
    return response.data;
  },

  // Adjuntos
  async subirAdjunto(ordenId: string, file: File): Promise<AdjuntoOrden> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<AdjuntoOrden>(`/ordenes/${ordenId}/adjuntos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async eliminarAdjunto(adjuntoId: string): Promise<void> {
    await api.delete(`/ordenes/adjuntos/${adjuntoId}`);
  },

  getDescargarAdjuntoUrl(adjuntoId: string): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    return `${baseUrl}/ordenes/adjuntos/${adjuntoId}/descargar`;
  },

  async getAdjuntoBlob(adjuntoId: string): Promise<Blob> {
    const response = await api.get(`/ordenes/adjuntos/${adjuntoId}/descargar`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

