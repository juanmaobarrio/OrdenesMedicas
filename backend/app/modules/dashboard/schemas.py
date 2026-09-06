import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class KpiMetricsResponse(BaseModel):
    """Metricas e indicadores clave de rendimiento (KPIs)."""
    total_ordenes: int = Field(..., description="Total historico de ordenes")
    ordenes_activas: int = Field(..., description="Ordenes en proceso (no cerradas ni canceladas)")
    ordenes_ingreso: int
    ordenes_en_auditoria: int
    ordenes_con_solicitudes: int
    ordenes_actualizadas: int
    ordenes_auditoria_finalizada: int
    ordenes_dadas_de_baja: int = 0
    ordenes_cerradas: int
    ordenes_canceladas: int
    tasa_aprobacion_porcentaje: float = Field(
        ..., description="Porcentaje de ordenes aprobadas respecto a finalizadas + canceladas"
    )
    llamadas_pendientes_total: int
    llamadas_pendientes_solicitud: int
    llamadas_pendientes_finalizada: int
    total_copago_recaudado: Decimal

    model_config = ConfigDict(from_attributes=True)


class DistribucionEstado(BaseModel):
    estado: str
    cantidad: int
    porcentaje: float


class DistribucionSucursal(BaseModel):
    sucursal_id: Optional[uuid.UUID] = None
    sucursal_nombre: str
    ordenes_abiertas: int
    ordenes_cerradas: int
    total_ordenes: int


class DistribucionMutual(BaseModel):
    mutual: str
    cantidad_ordenes: int
    total_copago: Decimal


class TendenciaTemporalItem(BaseModel):
    periodo: str
    ingresadas: int
    finalizadas: int


class DashboardChartsResponse(BaseModel):
    """Datos agregados listos para componentes de graficos (PrimeVue / Chart.js)."""
    estados: List[DistribucionEstado]
    sucursales: List[DistribucionSucursal]
    mutuales_top: List[DistribucionMutual]
    tendencias: List[TendenciaTemporalItem]


class ReporteFiltrosRequest(BaseModel):
    sucursal_id: Optional[uuid.UUID] = None
    estado: Optional[str] = None
    mutual: Optional[str] = None
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None



# ==========================================
# REPORTES Y ESTADÍSTICAS CONFIGURABLES
# ==========================================

class ReporteConfigurableRequest(BaseModel):
    """Parámetros para generar reportes dinámicos multidimensionales."""
    preset: Optional[str] = Field(None, description="Preset rápido: 'ordenes_tiempo', 'motivos_cancelacion', 'tasa_rechazo', 'financiero_reintegros'")
    dimension_primaria: str = Field(default="mutual", description="Eje principal: 'mutual', 'tiempo', 'motivo_cancelacion', 'sucursal', 'estado'")
    dimension_secundaria: Optional[str] = Field(None, description="Eje secundario de cruce opcional: 'mutual', 'estado', 'sucursal', 'tiempo'")
    agrupacion_tiempo: str = Field(default="mes", description="Unidad de tiempo: 'dia', 'semana', 'mes', 'anio'")
    fecha_desde: Optional[date] = Field(None, description="Fecha de prescripción o inicio desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha hasta")
    mutuales: Optional[List[str]] = Field(None, description="Filtrar por una o más mutuales específicas")
    sucursal_id: Optional[uuid.UUID] = Field(None, description="Filtrar por sucursal específica")
    estado: Optional[str] = Field(None, description="Filtrar por estado específico de orden")
    solo_con_reintegro: Optional[bool] = Field(False, description="Solo órdenes donde el paciente ya se atendió")


class ReporteFilaItem(BaseModel):
    """Fila o registro procesado para la tabla de datos y gráficos."""
    clave_primaria: str
    etiqueta_primaria: str
    clave_secundaria: Optional[str] = None
    etiqueta_secundaria: Optional[str] = None
    total_ordenes: int = 0
    ordenes_aprobadas: int = 0
    ordenes_canceladas: int = 0
    ordenes_en_proceso: int = 0
    total_estudios_evaluados: int = 0
    total_estudios_autorizados: int = 0
    total_estudios_rechazados: int = 0
    porcentaje_rechazo_estudios: float = 0.0
    total_copago: Decimal = Decimal("0.00")
    total_no_autorizados: Decimal = Decimal("0.00")
    total_apb: Decimal = Decimal("0.00")
    total_facturado_auditoria: Decimal = Decimal("0.00")
    total_abonado_atencion: Decimal = Decimal("0.00")
    total_reintegros_a_favor: Decimal = Decimal("0.00")
    cant_pacientes_reintegro: int = 0


class ReporteConfigurableResponse(BaseModel):
    """Resultado estructurado listo para renderizado de tablas, gráficos y PDF."""
    titulo_reporte: str
    subtitulo: str
    periodo_desde: Optional[str] = None
    periodo_hasta: Optional[str] = None
    fecha_generacion: str
    generado_por: str
    resumen_global: Dict[str, Any]
    filas: List[ReporteFilaItem]
    grafico_labels: List[str]
    grafico_datasets: List[Dict[str, Any]]
