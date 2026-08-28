export interface KpiMetrics {
  total_ordenes: number;
  ordenes_activas: number;
  ordenes_ingreso: number;
  ordenes_en_auditoria: number;
  ordenes_con_solicitudes: number;
  ordenes_actualizadas: number;
  ordenes_auditoria_finalizada: number;
  ordenes_dadas_de_baja?: number;
  ordenes_cerradas: number;
  ordenes_canceladas: number;
  tasa_aprobacion_porcentaje: number;
  llamadas_pendientes_total: number;
  llamadas_pendientes_solicitud: number;
  llamadas_pendientes_finalizada: number;
  total_copago_recaudado: number;
}

export interface DistribucionEstado {
  estado: string;
  cantidad: number;
  porcentaje: number;
}

export interface DistribucionSucursal {
  sucursal_id?: string | null;
  sucursal_nombre: string;
  ordenes_abiertas: number;
  ordenes_cerradas: number;
  total_ordenes: number;
}

export interface DistribucionMutual {
  mutual: string;
  cantidad_ordenes: number;
  total_copago: number;
}

export interface TendenciaTemporalItem {
  periodo: string;
  ingresadas: number;
  finalizadas: number;
}

export interface DashboardCharts {
  estados: DistribucionEstado[];
  sucursales: DistribucionSucursal[];
  mutuales_top: DistribucionMutual[];
  tendencias: TendenciaTemporalItem[];
}
