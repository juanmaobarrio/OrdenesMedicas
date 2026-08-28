import uuid
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.exceptions import ForbiddenActionException, InvalidCredentialsException
from backend.app.core.security import decode_token
from backend.app.modules.users.models import User
from backend.app.modules.users.repository import UserRepository

# Manejo de token Bearer en cabecera HTTP
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extrae y valida el usuario activo a traves del token Bearer JWT."""
    if not credentials:
        raise InvalidCredentialsException("Cabecera de autorizacion no proporcionada")

    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise InvalidCredentialsException("Token de acceso invalido o expirado")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise InvalidCredentialsException("Token no contiene identificador valido")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise InvalidCredentialsException("Identificador de usuario invalido")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise InvalidCredentialsException("Usuario no encontrado")

    if not user.is_active:
        raise ForbiddenActionException("El usuario se encuentra inactivo")

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """Dependencia para restringir endpoints a ciertos codigos de rol (ej: ['ADMIN', 'AUDITOR'])."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        if not current_user.role or current_user.role.code not in allowed_roles:
            raise ForbiddenActionException(
                f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def require_permission(permission_code: str) -> Callable:
    """Dependencia para verificar si el usuario cuenta con un permiso especifico."""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        user_permissions = (
            [p.code for p in current_user.role.permissions] if current_user.role else []
        )
        if permission_code not in user_permissions:
            raise ForbiddenActionException(
                f"Permiso requerido no otorgado: '{permission_code}'"
            )
        return current_user

    return permission_checker
