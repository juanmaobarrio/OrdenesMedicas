import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import case, cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.ordenes.models import EstadoOrden, OrdenMedica
from backend.app.modules.pacientes.models import Paciente
from backend.app.modules.users.models import Sucursal


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_counts_by_estado(
        self, sucursal_id: Optional[uuid.UUID] = None
    ) -> Dict[str, int]:
        """Obtiene el conteo agrupado por cada estado del ciclo de vida."""
        stmt = select(OrdenMedica.estado, func.count(OrdenMedica.id)).group_by(OrdenMedica.estado)
        if sucursal_id:
            stmt = stmt.where(OrdenMedica.sucursal_id == sucursal_id)

        result = await self.db.execute(stmt)
        counts = {estado.value: 0 for estado in EstadoOrden}
        for estado, count in result.all():
            val = estado.value if hasattr(estado, "value") else str(estado)
            counts[val] = count
        return counts

    async def get_pending_calls_counts(
        self, sucursal_id: Optional[uuid.UUID] = None
    ) -> Dict[str, int]:
        """Calcula las llamadas pendientes divididas por motivo."""
        stmt_solicitud = (
            select(func.count(OrdenMedica.id))
            .where(OrdenMedica.estado == EstadoOrden.SOLICITUDES_AUDITORIA)
            .where(OrdenMedica.llamada_solicitud_completada.is_(False))
        )
        stmt_finalizada = (
            select(func.count(OrdenMedica.id))
            .where(OrdenMedica.estado == EstadoOrden.AUDITORIA_FINALIZADA)
            .where(OrdenMedica.llamada_finalizada_completada.is_(False))
        )

        if sucursal_id:
            stmt_solicitud = stmt_solicitud.where(OrdenMedica.sucursal_id == sucursal_id)
            stmt_finalizada = stmt_finalizada.where(OrdenMedica.sucursal_id == sucursal_id)

        sol_count = (await self.db.execute(stmt_solicitud)).scalar_one()
        fin_count = (await self.db.execute(stmt_finalizada)).scalar_one()

        return {
            "solicitud": sol_count,
            "finalizada": fin_count,
            "total": sol_count + fin_count,
        }

    async def get_total_copago(
        self, sucursal_id: Optional[uuid.UUID] = None
    ) -> Decimal:
        """Suma el total de copago recaudado."""
        stmt = select(func.coalesce(func.sum(OrdenMedica.valor_copago), 0))
        if sucursal_id:
            stmt = stmt.where(OrdenMedica.sucursal_id == sucursal_id)
        return Decimal(str((await self.db.execute(stmt)).scalar_one()))

    async def get_distribution_by_sucursal(self) -> Sequence[Tuple[str, Optional[uuid.UUID], int, int, int]]:
        """Agrupa ordenes abiertas vs cerradas por cada sucursal."""
        abiertas_expr = case(
            (OrdenMedica.estado.in_([EstadoOrden.CANCELADA, EstadoOrden.DAR_DE_BAJA, EstadoOrden.CERRADA]), 0),
            else_=1,
        )
        cerradas_expr = case(
            (OrdenMedica.estado.in_([EstadoOrden.CANCELADA, EstadoOrden.DAR_DE_BAJA, EstadoOrden.CERRADA]), 1),
            else_=0,
        )

        stmt = (
            select(
                Sucursal.nombre,
                Sucursal.id,
                func.sum(abiertas_expr).label("abiertas"),
                func.sum(cerradas_expr).label("cerradas"),
                func.count(OrdenMedica.id).label("total"),
            )
            .join(OrdenMedica, OrdenMedica.sucursal_id == Sucursal.id, isouter=True)
            .group_by(Sucursal.id, Sucursal.nombre)
            .order_by(Sucursal.nombre.asc())
        )
        result = await self.db.execute(stmt)
        return result.all()

    async def get_top_mutuales(
        self, limit: int = 5, sucursal_id: Optional[uuid.UUID] = None
    ) -> Sequence[Tuple[str, int, Decimal]]:
        """Top de mutuales / obras sociales con mayor volumen de ordenes."""
        stmt = (
            select(
                OrdenMedica.mutual,
                func.count(OrdenMedica.id).label("cant"),
                func.coalesce(func.sum(OrdenMedica.valor_copago), 0).label("copago_sum"),
            )
            .group_by(OrdenMedica.mutual)
            .order_by(func.count(OrdenMedica.id).desc())
            .limit(limit)
        )
        if sucursal_id:
            stmt = stmt.where(OrdenMedica.sucursal_id == sucursal_id)

        result = await self.db.execute(stmt)
        return result.all()

    async def get_tendencias_temporales(
        self, days: int = 14, sucursal_id: Optional[uuid.UUID] = None
    ) -> Sequence[Tuple[date, int, int]]:
        """Calcula el flujo de ordenes ingresadas vs finalizadas en los ultimos N dias."""
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()

        date_col = cast(OrdenMedica.created_at, Date)
        finalizada_expr = case(
            (OrdenMedica.estado.in_([EstadoOrden.CERRADA, EstadoOrden.AUDITORIA_FINALIZADA]), 1),
            else_=0,
        )

        stmt = (
            select(
                date_col.label("fecha"),
                func.count(OrdenMedica.id).label("ingresadas"),
                func.sum(finalizada_expr).label("finalizadas"),
            )
            .where(date_col >= since_date)
            .group_by(date_col)
            .order_by(date_col.asc())
        )
        if sucursal_id:
            stmt = stmt.where(OrdenMedica.sucursal_id == sucursal_id)

        result = await self.db.execute(stmt)
        return result.all()

    async def get_orders_for_export(
        self,
        sucursal_id: Optional[uuid.UUID] = None,
        estado: Optional[str] = None,
        mutual: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Sequence[OrdenMedica]:
        """Obtiene el conjunto de datos completo para exportacion a CSV/Excel."""
        stmt = (
            select(OrdenMedica)
            .options(
                selectinload(OrdenMedica.paciente),
                selectinload(OrdenMedica.sucursal),
                selectinload(OrdenMedica.created_by_user),
                selectinload(OrdenMedica.assigned_auditor),
            )
            .order_by(OrdenMedica.created_at.desc())
        )

        filters = []
        if sucursal_id:
            filters.append(OrdenMedica.sucursal_id == sucursal_id)
        if estado:
            filters.append(OrdenMedica.estado == estado)
        if mutual:
            filters.append(OrdenMedica.mutual.ilike(f"%{mutual.strip()}%"))
        if fecha_desde:
            filters.append(OrdenMedica.fecha_prescripcion >= fecha_desde)
        if fecha_hasta:
            filters.append(OrdenMedica.fecha_prescripcion <= fecha_hasta)

        if filters:
            stmt = stmt.where(*filters)

        result = await self.db.execute(stmt)
        return result.scalars().all()

