import api from './api';
import { DashboardCharts, KpiMetrics } from '../types/dashboard';

export const dashboardService = {
  async getKpis(sucursalId?: string): Promise<KpiMetrics> {
    const response = await api.get<KpiMetrics>('/dashboard/kpis', {
      params: { sucursal_id: sucursalId },
    });
    return response.data;
  },

  async getCharts(sucursalId?: string): Promise<DashboardCharts> {
    const response = await api.get<DashboardCharts>('/dashboard/charts', {
      params: { sucursal_id: sucursalId },
    });
    return response.data;
  },

  async downloadCsv(params: {
    sucursal_id?: string;
    estado?: string;
    mutual?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<Blob> {
    const response = await api.get('/dashboard/reportes/ordenes-csv', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};
