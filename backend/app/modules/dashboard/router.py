import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.modules.auth.dependencies import get_current_user, require_permission, require_roles
from backend.app.modules.dashboard.schemas import (
    DashboardChartsResponse,
    KpiMetricsResponse,
)
from backend.app.modules.dashboard.service import DashboardService
from backend.app.modules.users.models import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard y Reportes"])


@router.get(
    "/kpis",
    response_model=KpiMetricsResponse,
    summary="Obtener indicadores clave de rendimiento (KPIs)",
)
async def get_dashboard_kpis(
    sucursal_id: Optional[uuid.UUID] = Query(None, description="Filtrar por sucursal"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard:view")),
):
    filtro_sucursal = sucursal_id
    if not current_user.is_superuser and current_user.role and current_user.role.code == "USUARIO":
        filtro_sucursal = current_user.sucursal_id

    service = DashboardService(db)
    return await service.get_kpis(sucursal_id=filtro_sucursal)


@router.get(
    "/charts",
    response_model=DashboardChartsResponse,
    summary="Obtener distribuciones y tendencias para graficos interactivos",
)
async def get_dashboard_charts(
    sucursal_id: Optional[uuid.UUID] = Query(None, description="Filtrar por sucursal"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard:view")),
):
    filtro_sucursal = sucursal_id
    if not current_user.is_superuser and current_user.role and current_user.role.code == "USUARIO":
        filtro_sucursal = current_user.sucursal_id

    service = DashboardService(db)
    return await service.get_charts_data(sucursal_id=filtro_sucursal)


@router.get(
    "/reportes/ordenes-csv",
    summary="Exportar reporte de ordenes medicas en formato CSV compatible con Excel",
)
async def export_ordenes_csv(
    sucursal_id: Optional[uuid.UUID] = Query(None, description="Filtrar por sucursal"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    mutual: Optional[str] = Query(None, description="Filtrar por mutual"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de prescripcion desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de prescripcion hasta"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard:view")),
):
    filtro_sucursal = sucursal_id
    if not current_user.is_superuser and current_user.role and current_user.role.code == "USUARIO":
        filtro_sucursal = current_user.sucursal_id

    service = DashboardService(db)
    csv_stream = await service.generate_csv_report(
        sucursal_id=filtro_sucursal,
        estado=estado,
        mutual=mutual,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    response = Response(
        content=csv_stream.getvalue(),
        media_type="text/csv; charset=utf-8",
    )
    response.headers["Content-Disposition"] = "attachment; filename=reporte_ordenes_medicas.csv"
    return response

