import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Solicitud de inicio de sesion (admite username o email indistintamente)."""
    identifier: str = Field(..., description="Nombre de usuario o correo electronico")
    password: str = Field(..., min_length=1, description="Contrasena de acceso")


class TokenResponse(BaseModel):
    """Respuesta exitosa de emision de tokens JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Solicitud para renovar token de acceso mediante refresh token."""
    refresh_token: str


class CurrentUserSession(BaseModel):
    """Informacion de sesion del usuario autenticado."""
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role_code: str
    role_name: str
    hierarchy_level: int = 10
    permissions: List[str]
    sucursal_id: Optional[uuid.UUID] = None
    sucursal_nombre: Optional[str] = None
    is_superuser: bool

