from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.modules.auth.dependencies import get_current_user
from backend.app.modules.auth.schemas import (
    CurrentUserSession,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from backend.app.modules.auth.service import AuthService
from backend.app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesion")
async def login(
    dto: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Permite el inicio de sesion usando indistintamente nombre de usuario o correo electronico."""
    service = AuthService(db)
    user = await service.authenticate_user(dto)
    return await service.generate_auth_tokens(user)


@router.post("/refresh", response_model=TokenResponse, summary="Refrescar token de acceso")
async def refresh_token(
    dto: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Genera un nuevo par de tokens a partir de un refresh token valido."""
    service = AuthService(db)
    return await service.refresh_access_token(dto.refresh_token)


@router.get("/me", response_model=CurrentUserSession, summary="Obtener perfil del usuario actual")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Devuelve la informacion de sesion, rol, sucursal y permisos del usuario autenticado."""
    return AuthService.build_user_session(current_user)

