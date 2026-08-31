import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.modules.auth.dependencies import get_current_user, require_permission
from backend.app.modules.pacientes.schemas import (
    ObraSocialCreate,
    ObraSocialRead,
    ObraSocialUpdate,
    PacienteCreate,
    PacienteRead,
    PacienteSearchResult,
    PacienteUpdate,
)
from backend.app.modules.pacientes.service import ObraSocialService, PacienteService
from backend.app.modules.users.models import User

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])
mutuales_router = APIRouter(prefix="/mutuales", tags=["Obras Sociales / Mutuales"])



class PacientePaginatedResponse(BaseModel):
    items: List[PacienteRead]
    total: int
    skip: int
    limit: int


@router.get(
    "",
    response_model=PacientePaginatedResponse,
    summary="Listar pacientes con paginacion y filtros",
)
async def list_pacientes(
    skip: int = Query(0, ge=0, description="Numero de registros a saltar"),
    limit: int = Query(50, ge=1, le=200, description="Limite de registros por pagina"),
    search: Optional[str] = Query(None, description="Buscar por DNI, apellido o nombre"),
    obra_social: Optional[str] = Query(None, description="Filtrar por obra social"),
    only_active: bool = Query(True, description="Filtrar solo registros activos"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PacienteService(db)
    items, total = await service.list_pacientes(
        skip=skip,
        limit=limit,
        search=search,
        obra_social=obra_social,
        only_active=only_active,
    )
    return PacientePaginatedResponse(
        items=list(items),
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/search",
    response_model=List[PacienteSearchResult],
    summary="Busqueda rapida de pacientes para autocompletado",
)
async def search_pacientes(
    q: str = Query(..., min_length=2, description="Texto a buscar (DNI o Nombre)"),
    limit: int = Query(10, ge=1, le=50, description="Cantidad maxima de resultados"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PacienteService(db)
    return await service.search_pacientes(query=q, limit=limit)


@router.post(
    "",
    response_model=PacienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo paciente",
)
async def create_paciente(
    dto: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("pacientes:manage")),
):
    service = PacienteService(db)
    return await service.create_paciente(dto)


@router.get(
    "/{paciente_id}",
    response_model=PacienteRead,
    summary="Obtener detalle de paciente por ID",
)
async def get_paciente(
    paciente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PacienteService(db)
    return await service.get_by_id(paciente_id)


@router.get(
    "/documento/{documento}",
    response_model=PacienteRead,
    summary="Buscar paciente por numero de documento",
)
async def get_paciente_by_documento(
    documento: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PacienteService(db)
    return await service.get_by_documento(documento)


@router.put(
    "/{paciente_id}",
    response_model=PacienteRead,
    summary="Actualizar datos del paciente",
)
async def update_paciente(
    paciente_id: uuid.UUID,
    dto: PacienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("pacientes:manage")),
):
    service = PacienteService(db)
    return await service.update_paciente(paciente_id, dto)


# ==========================================
# ENDPOINTS DE OBRAS SOCIALES / MUTUALES
# ==========================================
@mutuales_router.get(
    "",
    response_model=List[ObraSocialRead],
    summary="Listar obras sociales y mutuales",
)
async def list_mutuales(
    only_active: bool = Query(True, description="Filtrar solo mutuales activas"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ObraSocialService(db)
    return await service.list_mutuales(only_active=only_active)


@mutuales_router.post(
    "",
    response_model=ObraSocialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva mutual u obra social",
)
async def create_mutual(
    dto: ObraSocialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("mutuales:manage")),
):
    service = ObraSocialService(db)
    return await service.create_mutual(dto)


@mutuales_router.get(
    "/{mutual_id}",
    response_model=ObraSocialRead,
    summary="Obtener detalle de mutual por ID",
)
async def get_mutual(
    mutual_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ObraSocialService(db)
    return await service.get_by_id(mutual_id)


@mutuales_router.put(
    "/{mutual_id}",
    response_model=ObraSocialRead,
    summary="Actualizar datos de obra social o mutual",
)
async def update_mutual(
    mutual_id: uuid.UUID,
    dto: ObraSocialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("mutuales:manage")),
):
    service = ObraSocialService(db)
    return await service.update_mutual(mutual_id, dto)


@mutuales_router.patch(
    "/{mutual_id}/toggle-active",
    response_model=ObraSocialRead,
    summary="Activar o desactivar obra social",
)
async def toggle_active_mutual(
    mutual_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("mutuales:manage")),
):
    service = ObraSocialService(db)
    return await service.toggle_active(mutual_id)


