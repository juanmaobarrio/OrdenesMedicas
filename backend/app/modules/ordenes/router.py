import os
import shutil
import uuid
from datetime import date
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.modules.auth.dependencies import get_current_user, require_roles
from backend.app.modules.ordenes.models import EstadoOrden
from backend.app.modules.ordenes.schemas import (
    AdjuntoOrdenRead,
    AuditoriaSolicitudCreate,
    AuditoriaSolicitudRead,
    AuditoriaSolicitudResponder,
    EstadoOrdenConfigCreate,
    EstadoOrdenConfigRead,
    EstadoOrdenConfigUpdate,
    MotivoCancelacionCreate,
    MotivoCancelacionRead,
    MotivoCancelacionUpdate,
    OrdenLlamadaPendienteItem,
    OrdenMedicaAsignarAuditor,
    OrdenMedicaCambioEstado,
    OrdenMedicaCreate,
    OrdenMedicaDetail,
    OrdenMedicaListItem,
    OrdenMedicaUpdate,
    RegistroLlamadaCreate,
    RegistroLlamadaRead,
)

from backend.app.modules.ordenes.service import (
    EstadoOrdenConfigService,
    MotivoCancelacionService,
    OrdenMedicaService,
)
from backend.app.modules.users.models import User

router = APIRouter(prefix="/ordenes", tags=["Ordenes Medicas"])


class OrdenesPaginatedResponse(BaseModel):
    items: List[OrdenMedicaListItem]
    total: int
    skip: int
    limit: int


def _get_client_info(request: Request):
    ip = request.client.host if request.client else None
    agent = request.headers.get("user-agent")
    return ip, agent


# ==========================================
# BANDEJA DE LLAMADAS PENDIENTES A PACIENTES
# ==========================================
@router.get(
    "/llamadas-pendientes",
    response_model=List[OrdenLlamadaPendienteItem],
    summary="Bandeja de llamadas pendientes a pacientes (Solicitud y Finalizada)",
)
async def list_llamadas_pendientes(
    sucursal_id: Optional[uuid.UUID] = Query(None, description="Filtrar por sucursal"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devuelve las ordenes que requieren llamado telefonico al paciente.
    Una vez avisado exitosamente, desaparece de esta lista sin cambiar el estado de la orden."""
    filtro_sucursal = sucursal_id
    if not current_user.is_superuser and current_user.role and current_user.role.code == "USUARIO":
        filtro_sucursal = current_user.sucursal_id

    service = OrdenMedicaService(db)
    return await service.obtener_llamadas_pendientes(sucursal_id=filtro_sucursal)


# ==========================================
# GESTION PRINCIPAL DE ORDENES
# ==========================================

@router.get(
    "",
    response_model=OrdenesPaginatedResponse,
    summary="Listar ordenes medicas con filtros avanzados",
)
async def list_ordenes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    estado: Optional[EstadoOrden] = Query(None, description="Filtrar por estado del ciclo de vida"),
    sucursal_id: Optional[uuid.UUID] = Query(None, description="Filtrar por sucursal"),
    paciente_id: Optional[uuid.UUID] = Query(None, description="Filtrar por paciente"),
    auditor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por auditor asignado"),
    mutual: Optional[str] = Query(None, description="Filtrar por mutual / obra social"),
    search: Optional[str] = Query(None, description="Buscar por Nro Orden, DNI o Nombre de Paciente"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de prescripcion desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de prescripcion hasta"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Si el usuario es de rol USUARIO (operador), restringir a su sucursal si no es admin
    filtro_sucursal = sucursal_id
    if not current_user.is_superuser and current_user.role and current_user.role.code == "USUARIO":
        filtro_sucursal = current_user.sucursal_id

    service = OrdenMedicaService(db)
    items, total = await service.list_ordenes(
        skip=skip,
        limit=limit,
        estado=estado,
        sucursal_id=filtro_sucursal,
        paciente_id=paciente_id,
        auditor_id=auditor_id,
        mutual=mutual,
        search=search,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    list_items = []
    for o in items:
        cant_adj = len(o.adjuntos) if o.adjuntos else 0
        cant_sol_pend = (
            len([s for s in o.solicitudes if s.estado.value == "PENDIENTE"])
            if o.solicitudes
            else 0
        )
        item_dict = {
            "id": o.id,
            "nro_orden": o.nro_orden,
            "estado": o.estado,
            "fecha_prescripcion": o.fecha_prescripcion,
            "mutual": o.mutual,
            "valor_copago": o.valor_copago,
            "cantidad_ordenes_fisicas": o.cantidad_ordenes_fisicas,
            "numeros_auditoria": o.numeros_auditoria,
            "paciente": o.paciente,
            "sucursal": o.sucursal,
            "created_by_user": o.created_by_user,
            "assigned_auditor": o.assigned_auditor,
            "cant_adjuntos": cant_adj,
            "cant_solicitudes_pendientes": cant_sol_pend,
            "created_at": o.created_at,
            "updated_at": o.updated_at,
        }
        list_items.append(OrdenMedicaListItem.model_validate(item_dict))

    return OrdenesPaginatedResponse(items=list_items, total=total, skip=skip, limit=limit)


@router.post(
    "",
    response_model=OrdenMedicaDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva orden medica",
)
async def create_orden(
    dto: OrdenMedicaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.create_orden(
        dto=dto, current_user=current_user, client_ip=ip, user_agent=agent
    )


@router.get(
    "/{orden_id}",
    response_model=OrdenMedicaDetail,
    summary="Obtener detalle completo de una orden con trazabilidad y adjuntos",
)
async def get_orden(
    orden_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrdenMedicaService(db)
    return await service.get_by_id(orden_id)


@router.put(
    "/{orden_id}",
    response_model=OrdenMedicaDetail,
    summary="Actualizar campos de una orden medica",
)
async def update_orden(
    orden_id: uuid.UUID,
    dto: OrdenMedicaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.update_orden(
        orden_id=orden_id, dto=dto, current_user=current_user, client_ip=ip, user_agent=agent
    )


# ==========================================
# TRANSICIONES DE ESTADO Y ASIGNACION
# ==========================================
@router.post(
    "/{orden_id}/estado",
    response_model=OrdenMedicaDetail,
    summary="Cambiar estado del ciclo de vida de la orden",
)
async def cambiar_estado(
    orden_id: uuid.UUID,
    dto: OrdenMedicaCambioEstado,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.cambiar_estado(
        orden_id=orden_id, dto=dto, current_user=current_user, client_ip=ip, user_agent=agent
    )


@router.post(
    "/{orden_id}/asignar-auditor",
    response_model=OrdenMedicaDetail,
    summary="Asignar un auditor medico a la orden",
)
async def asignar_auditor(
    orden_id: uuid.UUID,
    dto: OrdenMedicaAsignarAuditor,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "AUDITOR"])),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.asignar_auditor(
        orden_id=orden_id, dto=dto, current_user=current_user, client_ip=ip, user_agent=agent
    )


# ==========================================
# SOLICITUDES DE AUDITORIA Y OBSERVACIONES
# ==========================================
@router.post(
    "/{orden_id}/solicitudes",
    response_model=AuditoriaSolicitudRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud u observacion medica (Auditor)",
)
async def agregar_solicitud_auditoria(
    orden_id: uuid.UUID,
    dto: AuditoriaSolicitudCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "AUDITOR"])),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.agregar_solicitud_auditoria(
        orden_id=orden_id, dto=dto, current_user=current_user, client_ip=ip, user_agent=agent
    )


@router.post(
    "/solicitudes/{solicitud_id}/responder",
    response_model=AuditoriaSolicitudRead,
    summary="Responder solicitud de auditoria desde sucursal",
)
async def responder_solicitud_auditoria(
    solicitud_id: uuid.UUID,
    dto: AuditoriaSolicitudResponder,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.responder_solicitud_auditoria(
        solicitud_id=solicitud_id,
        dto=dto,
        current_user=current_user,
        client_ip=ip,
        user_agent=agent,
    )


@router.post(
    "/{orden_id}/registrar-llamada",
    response_model=RegistroLlamadaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar llamada y aviso al paciente",
)
async def registrar_llamada(
    orden_id: uuid.UUID,
    dto: RegistroLlamadaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.registrar_llamada_paciente(
        orden_id=orden_id, dto=dto, current_user=current_user, client_ip=ip, user_agent=agent
    )


# ==========================================
# SUBIDA Y DESCARGA DE ADJUNTOS
# ==========================================

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


@router.post(
    "/{orden_id}/adjuntos",
    response_model=AdjuntoOrdenRead,
    status_code=status.HTTP_201_CREATED,
    summary="Subir archivo o foto adjunta a la orden medica",
)
async def subir_adjunto(
    orden_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validar extension
    _, ext = os.path.splitext(file.filename or "")
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise AppException(
            status_code=400,
            detail=f"Formato no permitido ({ext}). Extensiones aceptadas: PDF, PNG, JPG, JPEG",
        )

    # Crear directorio si no existe
    upload_folder = os.path.join(settings.UPLOAD_DIR, str(orden_id))
    os.makedirs(upload_folder, exist_ok=True)

    # Nombre unico en disco
    unique_filename = f"{uuid.uuid4()}{ext_lower}"
    file_path = os.path.join(upload_folder, unique_filename)

    # Guardar en disco
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise AppException(
            status_code=400,
            detail=f"El archivo supera el tamano maximo permitido de {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    ip, agent = _get_client_info(request)
    service = OrdenMedicaService(db)
    return await service.registrar_adjunto(
        orden_id=orden_id,
        nombre_original=file.filename or "archivo_sin_nombre",
        nombre_almacenado=unique_filename,
        ruta_almacenamiento=file_path,
        tipo_mime=file.content_type or "application/octet-stream",
        tamano_bytes=file_size,
        current_user=current_user,
        client_ip=ip,
        user_agent=agent,
    )


@router.get(
    "/adjuntos/{adjunto_id}/descargar",
    summary="Descargar o visualizar archivo adjunto",
)
async def descargar_adjunto(
    adjunto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = OrdenMedicaService(db).repo
    adjunto = await repo.get_adjunto_by_id(adjunto_id)
    if not adjunto:
        raise AppException(status_code=404, detail="Archivo adjunto no encontrado")

    if not os.path.exists(adjunto.ruta_almacenamiento):
        raise AppException(status_code=404, detail="El archivo fisico no existe en el almacenamiento")

    return FileResponse(
        path=adjunto.ruta_almacenamiento,
        filename=adjunto.nombre_archivo_original,
        media_type=adjunto.tipo_mime,
    )


# ==========================================
# CONFIGURACION DEL SISTEMA Y MOTIVOS DE CANCELACION
# ==========================================
config_router = APIRouter(prefix="/config", tags=["Configuración"])


@config_router.get(
    "/motivos-cancelacion",
    response_model=List[MotivoCancelacionRead],
    summary="Listar catálogo de motivos de cancelación",
)
async def list_motivos_cancelacion(
    only_active: bool = Query(False, description="Filtrar solo motivos activos"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MotivoCancelacionService(db)
    return await service.list_motivos(only_active=only_active)


@config_router.post(
    "/motivos-cancelacion",
    response_model=MotivoCancelacionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear motivo de cancelación (Admin)",
)
async def create_motivo_cancelacion(
    dto: MotivoCancelacionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = MotivoCancelacionService(db)
    return await service.create_motivo(dto)


@config_router.put(
    "/motivos-cancelacion/{motivo_id}",
    response_model=MotivoCancelacionRead,
    summary="Actualizar motivo de cancelación (Admin)",
)
async def update_motivo_cancelacion(
    motivo_id: uuid.UUID,
    dto: MotivoCancelacionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = MotivoCancelacionService(db)
    return await service.update_motivo(motivo_id, dto)


@config_router.patch(
    "/motivos-cancelacion/{motivo_id}/toggle-active",
    response_model=MotivoCancelacionRead,
    summary="Activar o desactivar motivo de cancelación (Admin)",
)
async def toggle_active_motivo_cancelacion(
    motivo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = MotivoCancelacionService(db)
    return await service.toggle_active(motivo_id)


@config_router.delete(
    "/motivos-cancelacion/{motivo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar motivo de cancelación (Admin)",
)
async def delete_motivo_cancelacion(
    motivo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = MotivoCancelacionService(db)
    await service.delete_motivo(motivo_id)


# ==========================================
# GESTION DE ESTADOS CONFIGURABLES (CON ID NUMERICO)
# ==========================================
@config_router.get(
    "/estados",
    response_model=List[EstadoOrdenConfigRead],
    summary="Listar catalogo de estados del sistema con ID numerico",
)
async def list_estados_orden(
    only_active: bool = Query(False, description="Filtrar solo estados activos"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EstadoOrdenConfigService(db)
    return await service.list_estados(only_active=only_active)


@config_router.post(
    "/estados",
    response_model=EstadoOrdenConfigRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo estado de orden (Admin)",
)
async def create_estado_orden(
    dto: EstadoOrdenConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = EstadoOrdenConfigService(db)
    return await service.create_estado(dto)


@config_router.put(
    "/estados/{estado_id}",
    response_model=EstadoOrdenConfigRead,
    summary="Actualizar estado de orden (Admin)",
)
async def update_estado_orden(
    estado_id: int,
    dto: EstadoOrdenConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = EstadoOrdenConfigService(db)
    return await service.update_estado(estado_id, dto)


@config_router.patch(
    "/estados/{estado_id}/toggle-active",
    response_model=EstadoOrdenConfigRead,
    summary="Activar o desactivar estado de orden (Admin)",
)
async def toggle_active_estado_orden(
    estado_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = EstadoOrdenConfigService(db)
    return await service.toggle_active(estado_id)


@config_router.delete(
    "/estados/{estado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar estado de orden (Admin)",
)
async def delete_estado_orden(
    estado_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = EstadoOrdenConfigService(db)
    await service.delete_estado(estado_id)

