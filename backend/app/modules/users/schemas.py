import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==========================================
# SUCURSAL SCHEMAS
# ==========================================
class SucursalBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre de la sucursal")
    codigo: str = Field(..., min_length=2, max_length=20, description="Codigo unico de la sucursal")
    activa: bool = Field(default=True, description="Estado de operacion de la sucursal")


class SucursalCreate(SucursalBase):
    pass


class SucursalUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    codigo: Optional[str] = Field(None, min_length=2, max_length=20)
    activa: Optional[bool] = None


class SucursalRead(SucursalBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PERMISSION SCHEMAS
# ==========================================
class PermissionBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=80, description="Codigo unico de permiso")
    module: str = Field(..., min_length=2, max_length=50, description="Modulo al que pertenece")
    description: Optional[str] = Field(None, max_length=255)


class PermissionCreate(PermissionBase):
    pass


class PermissionRead(PermissionBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ROLE SCHEMAS
# ==========================================
class RoleBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50, description="Codigo del rol (ej: ADMIN, AUDITOR)")
    name: str = Field(..., min_length=2, max_length=100, description="Nombre legible del rol")
    description: Optional[str] = Field(None, max_length=255)
    hierarchy_level: int = Field(default=10, description="Nivel jerarquico (100=Admin, 50=Auditor, 10=Usuario)")


class RoleCreate(RoleBase):
    permission_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    hierarchy_level: Optional[int] = None
    permission_ids: Optional[List[uuid.UUID]] = None


class RoleRead(RoleBase):
    id: uuid.UUID
    is_system: bool
    permissions: List[PermissionRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# USER SCHEMAS
# ==========================================
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario unico")
    email: EmailStr = Field(..., description="Correo electronico")
    first_name: str = Field(..., min_length=2, max_length=100, description="Nombre")
    last_name: str = Field(..., min_length=2, max_length=100, description="Apellido")
    is_active: bool = Field(default=True, description="Estado del usuario")
    role_id: uuid.UUID = Field(..., description="ID del rol asignado")
    sucursal_id: Optional[uuid.UUID] = Field(None, description="ID de la sucursal asignada")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="Contrasena en texto plano")
    is_superuser: bool = Field(default=False)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None
    role_id: Optional[uuid.UUID] = None
    sucursal_id: Optional[uuid.UUID] = None


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)


class UserResetPasswordAdmin(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100, description="Nueva contrasena establecida por el Administrador")


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_superuser: bool
    last_login_at: Optional[datetime] = None
    role: Optional[RoleRead] = None
    sucursal: Optional[SucursalRead] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserReadSummary(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    email: str
    role_code: Optional[str] = None
    sucursal_nombre: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

