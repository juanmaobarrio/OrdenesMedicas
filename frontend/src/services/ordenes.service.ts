import api from './api';
import {
  AdjuntoOrden,
  AuditoriaSolicitud,
  EnviarEmailResolucionPayload,
  EstadoOrden,
  EstudioDetalleItem,
  OrdenLlamadaPendienteItem,
  OrdenMedicaCreate,
  OrdenMedicaDetail,
  OrdenMedicaListItem,
  PreviewEmailResolucion,
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
    observacion_resultado?: string | null,
    valor_copago?: number | null,
    valor_estudios_no_autorizados?: number | null,
    valor_apb?: number | null,
    estudios_autorizados?: string[] | null,
    estudios_no_autorizados?: string[] | null
  ): Promise<OrdenMedicaDetail> {
    const response = await api.post<OrdenMedicaDetail>(`/ordenes/${id}/estado`, {
      nuevo_estado,
      motivo,
      motivo_cancelacion_id,
      observacion_resultado,
      valor_copago,
      valor_estudios_no_autorizados,
      valor_apb,
      estudios_autorizados,
      estudios_no_autorizados,
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

  // Indicaciones Clínicas de la Orden
  async actualizarIndicaciones(
    ordenId: string,
    indicacionesIds: string[],
    indicacionesTexto?: string | null
  ): Promise<OrdenMedicaDetail> {
    const response = await api.put<OrdenMedicaDetail>(`/ordenes/${ordenId}/indicaciones`, {
      indicaciones_ids: indicacionesIds,
      indicaciones_texto: indicacionesTexto,
    });
    return response.data;
  },

  // Previsualización y Envío de Email de Resolución
  async previewEmail(ordenId: string): Promise<PreviewEmailResolucion> {
    const response = await api.get<PreviewEmailResolucion>(`/ordenes/${ordenId}/preview-email`);
    return response.data;
  },

  async enviarEmail(ordenId: string, payload: EnviarEmailResolucionPayload): Promise<OrdenMedicaDetail> {
    const response = await api.post<OrdenMedicaDetail>(`/ordenes/${ordenId}/enviar-email`, payload);
    return response.data;
  },

  async cancelarEnvioAutomatico(ordenId: string): Promise<OrdenMedicaDetail> {
    const response = await api.post<OrdenMedicaDetail>(`/ordenes/${ordenId}/cancelar-envio-automatico`);
    return response.data;
  },

  // Actualizar estudios autorizados y no autorizados de auditoría
  async actualizarEstudiosAuditoria(
    ordenId: string,
    estudiosAutorizados: string[],
    estudiosNoAutorizados: string[]
  ): Promise<OrdenMedicaDetail> {
    const response = await api.put<OrdenMedicaDetail>(`/ordenes/${ordenId}/estudios-auditoria`, {
      estudios_autorizados: estudiosAutorizados,
      estudios_no_autorizados: estudiosNoAutorizados,
    });
    return response.data;
  },

  // Actualizar desglose detallado de estudios con precios y estado de autorización
  async actualizarEstudiosDetalle(
    ordenId: string,
    estudiosDetalle: EstudioDetalleItem[]
  ): Promise<OrdenMedicaDetail> {
    const response = await api.put<OrdenMedicaDetail>(`/ordenes/${ordenId}/estudios-detalle`, {
      estudios_detalle: estudiosDetalle,
    });
    return response.data;
  },
};
