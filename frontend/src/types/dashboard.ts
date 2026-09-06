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


export interface ReporteConfigurableRequest {
  preset?: string | null;
  dimension_primaria: string;
  dimension_secundaria?: string | null;
  agrupacion_tiempo?: string;
  fecha_desde?: string | null;
  fecha_hasta?: string | null;
  mutuales?: string[] | null;
  sucursal_id?: string | null;
  estado?: string | null;
  solo_con_reintegro?: boolean;
}

export interface ReporteFilaItem {
  clave_primaria: string;
  etiqueta_primaria: string;
  clave_secundaria?: string | null;
  etiqueta_secundaria?: string | null;
  total_ordenes: number;
  ordenes_aprobadas: number;
  ordenes_canceladas: number;
  ordenes_en_proceso: number;
  total_estudios_evaluados: number;
  total_estudios_autorizados: number;
  total_estudios_rechazados: number;
  porcentaje_rechazo_estudios: number;
  total_copago: number;
  total_no_autorizados: number;
  total_apb: number;
  total_facturado_auditoria: number;
  total_abonado_atencion: number;
  total_reintegros_a_favor: number;
  cant_pacientes_reintegro: number;
}

export interface ReporteConfigurableResponse {
  titulo_reporte: string;
  subtitulo: string;
  periodo_desde?: string | null;
  periodo_hasta?: string | null;
  fecha_generacion: string;
  generado_por: string;
  resumen_global: Record<string, any>;
  filas: ReporteFilaItem[];
  grafico_labels: string[];
  grafico_datasets: Record<string, any>[];
}
