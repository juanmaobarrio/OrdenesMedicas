import api from './api';
import {
  ConfiguracionAPB,
  ConfiguracionMailAutomatizacion,
  EstadoOrdenConfig,
  EstadoOrdenConfigCreate,
  EstadoOrdenConfigUpdate,
  IndicacionEstudio,
  IndicacionEstudioCreate,
  IndicacionEstudioUpdate,
  MotivoCancelacion,
  MotivoCancelacionCreate,
  MotivoCancelacionUpdate,
  PlantillaEmail,
  PlantillaEmailCreate,
  PlantillaEmailUpdate,
  SystemFeaturesConfig,
  SystemFeaturesConfigUpdate,
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

  // Acto Profesional Bioquímico (APB) General
  async getValorApb(): Promise<ConfiguracionAPB> {
    const response = await api.get<ConfiguracionAPB>('/config/apb');
    return response.data;
  },

  async updateValorApb(valor_apb: number): Promise<ConfiguracionAPB> {
    const response = await api.put<ConfiguracionAPB>('/config/apb', { valor_apb });
    return response.data;
  },

  // Indicaciones de Estudios
  async listIndicaciones(onlyActive = false): Promise<IndicacionEstudio[]> {
    const response = await api.get<IndicacionEstudio[]>('/config/indicaciones', {
      params: { only_active: onlyActive },
    });
    return response.data;
  },

  async createIndicacion(dto: IndicacionEstudioCreate): Promise<IndicacionEstudio> {
    const response = await api.post<IndicacionEstudio>('/config/indicaciones', dto);
    return response.data;
  },

  async updateIndicacion(id: string, dto: IndicacionEstudioUpdate): Promise<IndicacionEstudio> {
    const response = await api.put<IndicacionEstudio>(`/config/indicaciones/${id}`, dto);
    return response.data;
  },

  async deleteIndicacion(id: string): Promise<void> {
    await api.delete(`/config/indicaciones/${id}`);
  },

  // Configuración de Automatización de Emails
  async getMailAutomatizacion(): Promise<ConfiguracionMailAutomatizacion> {
    const response = await api.get<ConfiguracionMailAutomatizacion>('/config/mail-automatizacion');
    return response.data;
  },

  async updateMailAutomatizacion(dto: { envio_automatico: boolean; minutos_gracia: number }): Promise<ConfiguracionMailAutomatizacion> {
    const response = await api.put<ConfiguracionMailAutomatizacion>('/config/mail-automatizacion', dto);
    return response.data;
  },

  // Plantillas de Correo
  async listPlantillasEmail(onlyActive = false): Promise<PlantillaEmail[]> {
    const response = await api.get<PlantillaEmail[]>('/config/plantillas-email', {
      params: { only_active: onlyActive },
    });
    return response.data;
  },

  async createPlantillaEmail(dto: PlantillaEmailCreate): Promise<PlantillaEmail> {
    const response = await api.post<PlantillaEmail>('/config/plantillas-email', dto);
    return response.data;
  },

  async updatePlantillaEmail(id: string, dto: PlantillaEmailUpdate): Promise<PlantillaEmail> {
    const response = await api.put<PlantillaEmail>(`/config/plantillas-email/${id}`, dto);
    return response.data;
  },

  async deletePlantillaEmail(id: string): Promise<void> {
    await api.delete(`/config/plantillas-email/${id}`);
  },

  async getCodigoBasePlantilla(): Promise<string> {
    const response = await api.get<{ codigo_html: string }>('/config/plantillas-email-codigo-base');
    return response.data.codigo_html;
  },

  // Feature Flags / Funcionalidades
  async getFeatures(): Promise<SystemFeaturesConfig> {
    const response = await api.get<SystemFeaturesConfig>('/config/features');
    return response.data;
  },

  async updateFeatures(dto: SystemFeaturesConfigUpdate): Promise<SystemFeaturesConfig> {
    const response = await api.put<SystemFeaturesConfig>('/config/features', dto);
    return response.data;
  },
};
