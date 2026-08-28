import uuid
from typing import Optional, Sequence, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.pacientes.models import ObraSocial, Paciente


class ObraSocialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, mutual_id: uuid.UUID) -> Optional[ObraSocial]:
        stmt = select(ObraSocial).where(ObraSocial.id == mutual_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codigo(self, codigo: str) -> Optional[ObraSocial]:
        stmt = select(ObraSocial).where(ObraSocial.codigo == codigo.strip().upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, only_active: bool = True) -> Sequence[ObraSocial]:
        stmt = select(ObraSocial)
        if only_active:
            stmt = stmt.where(ObraSocial.activa.is_(True))
        stmt = stmt.order_by(ObraSocial.sigla.asc(), ObraSocial.nombre.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, mutual: ObraSocial) -> ObraSocial:
        self.db.add(mutual)
        await self.db.flush()
        await self.db.refresh(mutual)
        return mutual

    async def update(self, mutual: ObraSocial, data: dict) -> ObraSocial:
        for key, value in data.items():
            if hasattr(mutual, key):
                setattr(mutual, key, value)
        await self.db.flush()
        await self.db.refresh(mutual)
        return mutual



class PacienteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, paciente_id: uuid.UUID) -> Optional[Paciente]:
        stmt = select(Paciente).where(Paciente.id == paciente_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_documento(self, documento: str) -> Optional[Paciente]:
        stmt = select(Paciente).where(Paciente.documento == documento.strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, query: str, limit: int = 10) -> Sequence[Paciente]:
        """Busqueda rapida para autocompletado por DNI o apellidos/nombres."""
        pattern = f"%{query.strip()}%"
        stmt = (
            select(Paciente)
            .where(
                or_(
                    Paciente.documento.ilike(pattern),
                    Paciente.apellidos.ilike(pattern),
                    Paciente.nombres.ilike(pattern),
                )
            )
            .where(Paciente.is_active.is_(True))
            .order_by(Paciente.apellidos.asc(), Paciente.nombres.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_paginated(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        obra_social: Optional[str] = None,
        only_active: bool = True,
    ) -> Tuple[Sequence[Paciente], int]:
        """Lista pacientes con soporte de filtros y paginacion."""
        base_stmt = select(Paciente)
        count_stmt = select(func.count(Paciente.id))

        filters = []
        if only_active:
            filters.append(Paciente.is_active.is_(True))

        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Paciente.documento.ilike(pattern),
                    Paciente.apellidos.ilike(pattern),
                    Paciente.nombres.ilike(pattern),
                )
            )

        if obra_social:
            filters.append(Paciente.obra_social.ilike(f"%{obra_social.strip()}%"))

        if filters:
            base_stmt = base_stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        # Conteo total
        total_count = (await self.db.execute(count_stmt)).scalar_one()

        # Obtencion de registros
        query_stmt = (
            base_stmt.order_by(Paciente.apellidos.asc(), Paciente.nombres.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query_stmt)
        items = result.scalars().all()

        return items, total_count

    async def create(self, paciente: Paciente) -> Paciente:
        self.db.add(paciente)
        await self.db.flush()
        await self.db.refresh(paciente)
        return paciente

