import uuid
from datetime import date, datetime, timezone
from typing import Any, List, Optional, Sequence, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.ordenes.models import (
    AdjuntoOrden,
    AuditoriaLog,
    AuditoriaSolicitud,
    EstadoOrden,
    EstadoOrdenConfig,
    MotivoCancelacion,
    OrdenMedica,
    RegistroLlamadaPaciente,
)

from backend.app.modules.pacientes.models import Paciente


class OrdenMedicaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, orden_id: uuid.UUID) -> Optional[OrdenMedica]:
        stmt = (
            select(OrdenMedica)
            .options(
                selectinload(OrdenMedica.paciente),
                selectinload(OrdenMedica.sucursal),
                selectinload(OrdenMedica.created_by_user),
                selectinload(OrdenMedica.assigned_auditor),
                selectinload(OrdenMedica.adjuntos).selectinload(AdjuntoOrden.subido_por),
                selectinload(OrdenMedica.solicitudes).selectinload(AuditoriaSolicitud.auditor),
                selectinload(OrdenMedica.solicitudes).selectinload(AuditoriaSolicitud.respondido_por),
                    selectinload(OrdenMedica.llamadas_registro).selectinload(RegistroLlamadaPaciente.operador),
                    selectinload(OrdenMedica.audit_logs).selectinload(AuditoriaLog.user),
                )
                .execution_options(populate_existing=True)
                .where(OrdenMedica.id == orden_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nro_orden(self, nro_orden: str) -> Optional[OrdenMedica]:
        stmt = select(OrdenMedica).where(OrdenMedica.nro_orden == nro_orden.strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def generate_next_nro_orden(self) -> str:
        """Genera un numero correlativo unico para la orden (ej: ORD-2025-000001)."""
        year = datetime.now(timezone.utc).year
        prefix = f"ORD-{year}-"

        stmt = (
            select(func.count(OrdenMedica.id))
            .where(OrdenMedica.nro_orden.like(f"{prefix}%"))
        )
        count = (await self.db.execute(stmt)).scalar_one()
        return f"{prefix}{count + 1:06d}"

    async def list_paginated(
        self,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[Any] = None,
        sucursal_id: Optional[uuid.UUID] = None,
        paciente_id: Optional[uuid.UUID] = None,
        auditor_id: Optional[uuid.UUID] = None,
        mutual: Optional[str] = None,
        search: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Tuple[Sequence[OrdenMedica], int]:
        """Consulta paginada de ordenes con filtros multiples."""
        base_stmt = (
            select(OrdenMedica)
            .options(
                selectinload(OrdenMedica.paciente),
                selectinload(OrdenMedica.sucursal),
                selectinload(OrdenMedica.created_by_user),
                selectinload(OrdenMedica.assigned_auditor),
                selectinload(OrdenMedica.adjuntos),
                selectinload(OrdenMedica.solicitudes),
            )
        )
        count_stmt = select(func.count(OrdenMedica.id))

        filters = []
        if estado:
            estado_val = estado.value if hasattr(estado, "value") else str(estado)
            filters.append(OrdenMedica.estado == estado_val)
        if sucursal_id:
            filters.append(OrdenMedica.sucursal_id == sucursal_id)
        if paciente_id:
            filters.append(OrdenMedica.paciente_id == paciente_id)
        if auditor_id:
            filters.append(OrdenMedica.assigned_auditor_id == auditor_id)
        if mutual:
            filters.append(OrdenMedica.mutual.ilike(f"%{mutual.strip()}%"))
        if fecha_desde:
            filters.append(OrdenMedica.fecha_prescripcion >= fecha_desde)
        if fecha_hasta:
            filters.append(OrdenMedica.fecha_prescripcion <= fecha_hasta)

        if search:
            base_stmt = base_stmt.outerjoin(Paciente, OrdenMedica.paciente_id == Paciente.id)
            count_stmt = count_stmt.outerjoin(Paciente, OrdenMedica.paciente_id == Paciente.id)
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    OrdenMedica.nro_orden.ilike(pattern),
                    Paciente.documento.ilike(pattern),
                    Paciente.apellidos.ilike(pattern),
                    Paciente.nombres.ilike(pattern),
                )
            )

        if filters:
            base_stmt = base_stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total_count = (await self.db.execute(count_stmt)).scalar_one()

        query_stmt = (
            base_stmt.order_by(OrdenMedica.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query_stmt)
        items = result.scalars().unique().all()

        return items, total_count

    async def create(self, orden: OrdenMedica) -> OrdenMedica:
        self.db.add(orden)
        await self.db.flush()
        await self.db.refresh(orden)
        return orden

    async def create_adjunto(self, adjunto: AdjuntoOrden) -> AdjuntoOrden:
        self.db.add(adjunto)
        await self.db.flush()
        await self.db.refresh(adjunto)
        return adjunto

    async def get_adjunto_by_id(self, adjunto_id: uuid.UUID) -> Optional[AdjuntoOrden]:
        stmt = select(AdjuntoOrden).where(AdjuntoOrden.id == adjunto_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_adjunto(self, adjunto: AdjuntoOrden) -> None:
        await self.db.delete(adjunto)
        await self.db.flush()

    async def create_solicitud(self, solicitud: AuditoriaSolicitud) -> AuditoriaSolicitud:
        self.db.add(solicitud)
        await self.db.flush()
        await self.db.refresh(solicitud)
        return solicitud

    async def get_solicitud_by_id(self, solicitud_id: uuid.UUID) -> Optional[AuditoriaSolicitud]:
        stmt = (
            select(AuditoriaSolicitud)
            .options(
                selectinload(AuditoriaSolicitud.auditor),
                selectinload(AuditoriaSolicitud.respondido_por),
            )
            .where(AuditoriaSolicitud.id == solicitud_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_audit_log(self, log: AuditoriaLog) -> AuditoriaLog:
        self.db.add(log)
        await self.db.flush()
        return log

    async def create_registro_llamada(
        self, registro: RegistroLlamadaPaciente
    ) -> RegistroLlamadaPaciente:
        self.db.add(registro)
        await self.db.flush()
        await self.db.refresh(registro)
        return registro

    async def list_ordenes_con_llamadas_pendientes(
        self, sucursal_id: Optional[uuid.UUID] = None
    ) -> Sequence[OrdenMedica]:
        """Obtiene ordenes en estados clave donde el paciente aun no ha sido avisado."""
        cond_solicitud = (OrdenMedica.estado == EstadoOrden.SOLICITUDES_AUDITORIA) & (
            OrdenMedica.llamada_solicitud_completada.is_(False)
        )
        cond_finalizada = (OrdenMedica.estado == EstadoOrden.AUDITORIA_FINALIZADA) & (
            OrdenMedica.llamada_finalizada_completada.is_(False)
        )

        stmt = (
            select(OrdenMedica)
            .options(
                selectinload(OrdenMedica.paciente),
                selectinload(OrdenMedica.sucursal),
                selectinload(OrdenMedica.solicitudes),
                selectinload(OrdenMedica.llamadas_registro),
            )
            .where(cond_solicitud | cond_finalizada)
        )

        if sucursal_id:
            stmt = stmt.where(OrdenMedica.sucursal_id == sucursal_id)

        stmt = stmt.order_by(OrdenMedica.updated_at.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()


class MotivoCancelacionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, only_active: bool = True) -> Sequence[MotivoCancelacion]:
        stmt = select(MotivoCancelacion)
        if only_active:
            stmt = stmt.where(MotivoCancelacion.activo.is_(True))
        stmt = stmt.order_by(MotivoCancelacion.nombre.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, motivo_id: uuid.UUID) -> Optional[MotivoCancelacion]:
        stmt = select(MotivoCancelacion).where(MotivoCancelacion.id == motivo_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codigo(self, codigo: str) -> Optional[MotivoCancelacion]:
        stmt = select(MotivoCancelacion).where(MotivoCancelacion.codigo == codigo.strip().upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nombre(self, nombre: str) -> Optional[MotivoCancelacion]:
        stmt = select(MotivoCancelacion).where(func.lower(MotivoCancelacion.nombre) == nombre.strip().lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, motivo: MotivoCancelacion) -> MotivoCancelacion:
        self.db.add(motivo)
        await self.db.flush()
        await self.db.refresh(motivo)
        return motivo

    async def update(self, motivo: MotivoCancelacion, data: dict) -> MotivoCancelacion:
        for k, v in data.items():
            if hasattr(motivo, k):
                setattr(motivo, k, v)
        await self.db.flush()
        await self.db.refresh(motivo)
        return motivo

    async def delete(self, motivo: MotivoCancelacion) -> None:
        await self.db.delete(motivo)
        await self.db.flush()


class EstadoOrdenConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, only_active: bool = False) -> Sequence[EstadoOrdenConfig]:
        stmt = select(EstadoOrdenConfig)
        if only_active:
            stmt = stmt.where(EstadoOrdenConfig.activo.is_(True))
        stmt = stmt.order_by(EstadoOrdenConfig.orden_secuencia.asc(), EstadoOrdenConfig.id.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, estado_id: int) -> Optional[EstadoOrdenConfig]:
        stmt = select(EstadoOrdenConfig).where(EstadoOrdenConfig.id == estado_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codigo(self, codigo: str) -> Optional[EstadoOrdenConfig]:
        stmt = select(EstadoOrdenConfig).where(EstadoOrdenConfig.codigo == codigo.strip().upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nombre(self, nombre: str) -> Optional[EstadoOrdenConfig]:
        stmt = select(EstadoOrdenConfig).where(func.lower(EstadoOrdenConfig.nombre) == nombre.strip().lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, estado: EstadoOrdenConfig) -> EstadoOrdenConfig:
        self.db.add(estado)
        await self.db.flush()
        await self.db.refresh(estado)
        return estado

    async def update(self, estado: EstadoOrdenConfig, data: dict) -> EstadoOrdenConfig:
        for k, v in data.items():
            if hasattr(estado, k):
                setattr(estado, k, v)
        await self.db.flush()
        await self.db.refresh(estado)
        return estado

    async def delete(self, estado: EstadoOrdenConfig) -> None:
        await self.db.delete(estado)
        await self.db.flush()


