import uuid
from decimal import Decimal
from typing import Dict, List, Optional
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

