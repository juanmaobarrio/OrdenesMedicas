import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.exceptions import InvalidCredentialsException
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from backend.app.modules.auth.schemas import CurrentUserSession, LoginRequest, TokenResponse
from backend.app.modules.users.models import User
from backend.app.modules.users.repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate_user(self, dto: LoginRequest) -> User:
        """Autentica a un usuario por username o email."""
        identifier = dto.identifier.strip()
        user = await self.user_repo.get_by_username_or_email(identifier)

        if not user or not verify_password(dto.password, user.hashed_password):
            raise InvalidCredentialsException("Usuario, correo o contrasena incorrectos")

        if not user.is_active:
            raise InvalidCredentialsException("La cuenta de usuario se encuentra inactiva")

        # Actualizar fecha de ultimo login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        return user

    async def generate_auth_tokens(self, user: User) -> TokenResponse:
        """Genera par de tokens (Access y Refresh)."""
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Emite un nuevo access token a partir de un refresh token valido."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise InvalidCredentialsException("Token de refresco invalido o expirado")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidCredentialsException("Token no contiene sujeto valido")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise InvalidCredentialsException("Identificador de usuario invalido")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidCredentialsException("Usuario no encontrado o inactivo")

        return await self.generate_auth_tokens(user)

    @staticmethod
    def build_user_session(user: User) -> CurrentUserSession:
        """Construye la representacion resumida de sesion del usuario."""
        permissions = [p.code for p in user.role.permissions] if user.role else []
        return CurrentUserSession(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role_code=user.role.code if user.role else "",
            role_name=user.role.name if user.role else "",
            permissions=permissions,
            sucursal_id=user.sucursal.id if user.sucursal else None,
            sucursal_nombre=user.sucursal.nombre if user.sucursal else None,
            is_superuser=user.is_superuser,
        )

