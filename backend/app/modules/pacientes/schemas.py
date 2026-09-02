import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ==========================================
# OBRA SOCIAL / MUTUAL SCHEMAS
# ==========================================
class ObraSocialBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50, description="Codigo unico interno de la mutual")
    sigla: str = Field(..., min_length=2, max_length=50, description="Sigla o acronimo (ej: OSDE, SM)")
    nombre: str = Field(..., min_length=2, max_length=150, description="Nombre o razon social completa")
    codigo_externo: Optional[str] = Field(None, max_length=50)
    dias_vencimiento: int = Field(default=30, ge=1, le=365, description="Dias de validez de la orden")
    copago_default: Decimal = Field(default=Decimal("0.00"), ge=0, description="Valor de copago por defecto")
    porcentaje_cobertura_apb: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100, description="Porcentaje de APB cubierto por la mutual (0 a 100%)"
    )
    activa: bool = Field(default=True, description="Estado de operacion")


class ObraSocialCreate(ObraSocialBase):
    pass


class ObraSocialUpdate(BaseModel):
    sigla: Optional[str] = Field(None, min_length=2, max_length=50)
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    codigo_externo: Optional[str] = None
    dias_vencimiento: Optional[int] = Field(None, ge=1, le=365)
    copago_default: Optional[Decimal] = Field(None, ge=0)
    porcentaje_cobertura_apb: Optional[Decimal] = Field(None, ge=0, le=100)
    activa: Optional[bool] = None


class ObraSocialRead(ObraSocialBase):
    id: uuid.UUID
    display_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PACIENTE SCHEMAS
# ==========================================
class PacienteBase(BaseModel):

    documento: str = Field(
        ..., min_length=4, max_length=30, description="DNI o documento de identidad unico"
    )
    nombres: str = Field(..., min_length=2, max_length=100, description="Nombres del paciente")
    apellidos: str = Field(..., min_length=2, max_length=100, description="Apellidos del paciente")
    fecha_nacimiento: Optional[date] = Field(
        None, description="Fecha de nacimiento (YYYY-MM-DD)"
    )
    obra_social: Optional[str] = Field(
        None, max_length=100, description="Obra social o entidad prepaga"
    )
    nro_afiliado: Optional[str] = Field(
        None, max_length=50, description="Numero de credencial o afiliado"
    )
    telefono: Optional[str] = Field(None, max_length=30, description="Telefono de contacto")
    email: Optional[EmailStr] = Field(None, description="Correo electronico")
    is_active: bool = Field(default=True, description="Estado activo del registro")

    @field_validator("email", "fecha_nacimiento", "obra_social", "nro_afiliado", "telefono", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or (isinstance(v, str) and not v.strip()):
            return None
        return v


class PacienteCreate(PacienteBase):
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento obligatoria (YYYY-MM-DD)")


class PacienteUpdate(BaseModel):
    documento: Optional[str] = Field(None, min_length=3, max_length=30)
    nombres: Optional[str] = Field(None, min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    fecha_nacimiento: Optional[Any] = None
    obra_social: Optional[str] = Field(None, max_length=100)
    nro_afiliado: Optional[str] = Field(None, max_length=50)
    telefono: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("email", "fecha_nacimiento", "obra_social", "nro_afiliado", "telefono", "documento", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or (isinstance(v, str) and not v.strip()):
            return None
        return v


class PacienteRead(PacienteBase):
    id: uuid.UUID
    nombre_completo: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PacienteSearchResult(BaseModel):
    id: uuid.UUID
    documento: str
    nombre_completo: str
    obra_social: Optional[str] = None
    nro_afiliado: Optional[str] = None
    telefono: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

