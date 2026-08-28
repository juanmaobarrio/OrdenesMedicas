import uuid
from typing import Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import EntityAlreadyExistsException, EntityNotFoundException
from backend.app.modules.pacientes.models import ObraSocial, Paciente
from backend.app.modules.pacientes.repository import ObraSocialRepository, PacienteRepository
from backend.app.modules.pacientes.schemas import (
    ObraSocialCreate,
    ObraSocialUpdate,
    PacienteCreate,
    PacienteUpdate,
)


class ObraSocialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ObraSocialRepository(db)

    async def list_mutuales(self, only_active: bool = True) -> Sequence[ObraSocial]:
        return await self.repo.list_all(only_active=only_active)

    async def get_by_id(self, mutual_id: uuid.UUID) -> ObraSocial:
        mutual = await self.repo.get_by_id(mutual_id)
        if not mutual:
            raise EntityNotFoundException("Obra Social", mutual_id)
        return mutual

    async def create_mutual(self, dto: ObraSocialCreate) -> ObraSocial:
        existing = await self.repo.get_by_codigo(dto.codigo)
        if existing:
            raise EntityAlreadyExistsException("Obra Social", "codigo", dto.codigo)

        mutual = ObraSocial(
            codigo=dto.codigo.strip().upper(),
            sigla=dto.sigla.strip().upper(),
            nombre=dto.nombre.strip(),
            codigo_externo=dto.codigo_externo.strip() if dto.codigo_externo else None,
            dias_vencimiento=dto.dias_vencimiento,
            activa=dto.activa,
        )
        return await self.repo.create(mutual)

    async def update_mutual(self, mutual_id: uuid.UUID, dto: ObraSocialUpdate) -> ObraSocial:
        mutual = await self.get_by_id(mutual_id)
        update_data = {}
        if dto.sigla is not None:
            update_data["sigla"] = dto.sigla.strip().upper()
        if dto.nombre is not None:
            update_data["nombre"] = dto.nombre.strip()
        if dto.codigo_externo is not None:
            update_data["codigo_externo"] = dto.codigo_externo.strip() if dto.codigo_externo else None
        if dto.dias_vencimiento is not None:
            update_data["dias_vencimiento"] = dto.dias_vencimiento
        if dto.activa is not None:
            update_data["activa"] = dto.activa

        return await self.repo.update(mutual, update_data)

    async def toggle_active(self, mutual_id: uuid.UUID) -> ObraSocial:
        mutual = await self.get_by_id(mutual_id)
        return await self.repo.update(mutual, {"activa": not mutual.activa})



class PacienteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PacienteRepository(db)

    async def get_by_id(self, paciente_id: uuid.UUID) -> Paciente:
        paciente = await self.repo.get_by_id(paciente_id)
        if not paciente:
            raise EntityNotFoundException("Paciente", paciente_id)
        return paciente

    async def get_by_documento(self, documento: str) -> Paciente:
        paciente = await self.repo.get_by_documento(documento)
        if not paciente:
            raise EntityNotFoundException("Paciente con documento", documento)
        return paciente

    async def search_pacientes(self, query: str, limit: int = 10) -> Sequence[Paciente]:
        if not query or len(query.strip()) < 2:
            return []
        return await self.repo.search(query.strip(), limit=limit)

    async def list_pacientes(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        obra_social: Optional[str] = None,
        only_active: bool = True,
    ) -> Tuple[Sequence[Paciente], int]:
        return await self.repo.list_paginated(
            skip=skip,
            limit=limit,
            search=search,
            obra_social=obra_social,
            only_active=only_active,
        )

    async def create_paciente(self, dto: PacienteCreate) -> Paciente:
        doc_clean = dto.documento.strip()
        existing = await self.repo.get_by_documento(doc_clean)
        if existing:
            raise EntityAlreadyExistsException("Paciente", "documento", doc_clean)

        paciente = Paciente(
            documento=doc_clean,
            nombres=dto.nombres.strip().title(),
            apellidos=dto.apellidos.strip().upper(),
            fecha_nacimiento=dto.fecha_nacimiento,
            obra_social=dto.obra_social.strip().upper() if dto.obra_social else None,
            nro_afiliado=dto.nro_afiliado.strip() if dto.nro_afiliado else None,
            telefono=dto.telefono.strip() if dto.telefono else None,
            email=dto.email.strip().lower() if dto.email else None,
            is_active=dto.is_active,
        )
        return await self.repo.create(paciente)

    async def update_paciente(self, paciente_id: uuid.UUID, dto: PacienteUpdate) -> Paciente:
        paciente = await self.get_by_id(paciente_id)

        if dto.documento and dto.documento.strip() != paciente.documento:
            doc_clean = dto.documento.strip()
            existing = await self.repo.get_by_documento(doc_clean)
            if existing and existing.id != paciente_id:
                raise EntityAlreadyExistsException("Paciente", "documento", doc_clean)
            paciente.documento = doc_clean

        if dto.nombres is not None:
            paciente.nombres = dto.nombres.strip().title()

        if dto.apellidos is not None:
            paciente.apellidos = dto.apellidos.strip().upper()

        if dto.fecha_nacimiento is not None:
            paciente.fecha_nacimiento = dto.fecha_nacimiento

        if dto.obra_social is not None:
            paciente.obra_social = dto.obra_social.strip().upper() if dto.obra_social else None

        if dto.nro_afiliado is not None:
            paciente.nro_afiliado = dto.nro_afiliado.strip() if dto.nro_afiliado else None

        if dto.telefono is not None:
            paciente.telefono = dto.telefono.strip() if dto.telefono else None

        if dto.email is not None:
            paciente.email = dto.email.strip().lower() if dto.email else None

        if dto.is_active is not None:
            paciente.is_active = dto.is_active

        await self.db.flush()
        return paciente

