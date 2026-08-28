import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.modules.auth.dependencies import get_current_user, require_roles
from backend.app.modules.users.models import User
from backend.app.modules.users.schemas import (
    PermissionRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    SucursalCreate,
    SucursalRead,
    UserCreate,
    UserPasswordUpdate,
    UserRead,
    UserReadSummary,
    UserResetPasswordAdmin,
    UserUpdate,
)
from backend.app.modules.users.service import RoleService, SucursalService, UserService

router = APIRouter(prefix="", tags=["Usuarios, Roles y Sucursales"])


# ==========================================
# ENDPOINTS DE SUCURSALES
# ==========================================
@router.get(
    "/sucursales",
    response_model=List[SucursalRead],
    summary="Listar todas las sucursales",
)
async def list_sucursales(
    only_active: bool = Query(False, description="Filtrar solo sucursales activas"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SucursalService(db)
    return await service.list_sucursales(only_active=only_active)


@router.post(
    "/sucursales",
    response_model=SucursalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva sucursal (Solo Administrador)",
)
async def create_sucursal(
    dto: SucursalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = SucursalService(db)
    return await service.create_sucursal(dto)


# ==========================================
# ENDPOINTS DE ROLES
# ==========================================
@router.get(
    "/roles",
    response_model=List[RoleRead],
    summary="Listar roles del sistema",
)
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RoleService(db)
    return await service.list_roles()


@router.post(
    "/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol personalizado (Solo Administrador)",
)
async def create_role(
    dto: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = RoleService(db)
    return await service.create_role(dto)


@router.get(
    "/permissions",
    response_model=List[PermissionRead],
    summary="Listar catalogo de permisos del sistema (Solo Administrador)",
)
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = RoleService(db)
    return await service.list_permissions()


@router.put(
    "/roles/{role_id}",
    response_model=RoleRead,
    summary="Actualizar rol y permisos asignados (Solo Administrador)",
)
async def update_role(
    role_id: uuid.UUID,
    dto: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = RoleService(db)
    return await service.update_role(role_id, dto)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar rol personalizado (Solo Administrador)",
)
async def delete_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = RoleService(db)
    await service.delete_role(role_id)


# ==========================================
# ENDPOINTS DE USUARIOS
# ==========================================
@router.get(
    "/users",
    response_model=List[UserRead],
    summary="Listar usuarios del sistema",
)
async def list_users(
    sucursal_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID de sucursal"),
    role_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID de rol"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return await service.list_users(sucursal_id=sucursal_id, role_id=role_id, is_active=is_active)


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario con jerarquía de rol",
)
async def create_user(
    dto: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return await service.create_user(dto, current_user=current_user)


@router.get(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Obtener detalle de usuario por ID",
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return await service.get_user_by_id(user_id)


@router.put(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Actualizar datos de usuario (Solo Administrador)",
)
async def update_user(
    user_id: uuid.UUID,
    dto: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = UserService(db)
    return await service.update_user(user_id, dto)


@router.patch(
    "/users/{user_id}/toggle-active",
    response_model=UserRead,
    summary="Activar o desactivar usuario (Solo Administrador)",
)
async def toggle_active_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = UserService(db)
    return await service.toggle_active(user_id)


@router.post(
    "/users/{user_id}/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña de usuario (Solo Administrador)",
)
async def reset_password_by_admin(
    user_id: uuid.UUID,
    dto: UserResetPasswordAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    service = UserService(db)
    await service.reset_password_by_admin(user_id, dto.new_password)
    return {"message": "Contraseña restablecida exitosamente por el Administrador"}


@router.post(
    "/users/{user_id}/change-password",
    status_code=status.HTTP_200_OK,
    summary="Cambiar contrasena de usuario",
)
async def change_password(
    user_id: uuid.UUID,
    dto: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    await service.change_password(user_id, dto)
    return {"message": "Contrasena actualizada correctamente"}

