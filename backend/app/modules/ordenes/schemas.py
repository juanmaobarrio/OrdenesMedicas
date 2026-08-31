import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from backend.app.modules.ordenes.models import (
    EstadoOrden,
    EstadoSolicitudAuditoria,
    ResultadoLlamada,
    TipoEstadoOrden,
    TipoLlamadaPaciente,
)

from backend.app.modules.pacientes.schemas import PacienteRead
from backend.app.modules.users.schemas import SucursalRead, UserReadSummary


# ==========================================
# MOTIVOS DE CANCELACION SCHEMAS
# ==========================================
class MotivoCancelacionBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50, description="Codigo unico de referencia")
    nombre: str = Field(..., min_length=2, max_length=150, description="Nombre descriptivo del motivo")
    descripcion: Optional[str] = Field(None, max_length=255)
    activo: bool = Field(default=True)


class MotivoCancelacionCreate(MotivoCancelacionBase):
    pass


class MotivoCancelacionUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=255)
    activo: Optional[bool] = None


class MotivoCancelacionRead(MotivoCancelacionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ESTADOS DE ORDEN CONFIGURABLES SCHEMAS
# ==========================================
class EstadoOrdenConfigBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50, description="Codigo unico de estado (ej: INGRESO)")
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre legible del estado")
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo: TipoEstadoOrden = Field(default=TipoEstadoOrden.PROCESO, description="PROCESO o FINALIZACION")
    requiere_motivo: bool = Field(default=False)
    color_badge: str = Field(default="info", max_length=30)
    icono: Optional[str] = Field(None, max_length=50)
    es_sistema: bool = Field(default=False)
    activo: bool = Field(default=True)
    orden_secuencia: int = Field(default=0)


class EstadoOrdenConfigCreate(EstadoOrdenConfigBase):
    pass


class EstadoOrdenConfigUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo: Optional[TipoEstadoOrden] = None
    requiere_motivo: Optional[bool] = None
    color_badge: Optional[str] = Field(None, max_length=30)
    icono: Optional[str] = Field(None, max_length=50)
    activo: Optional[bool] = None
    orden_secuencia: Optional[int] = None


class EstadoOrdenConfigRead(EstadoOrdenConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ADJUNTO SCHEMAS
# ==========================================
class AdjuntoOrdenRead(BaseModel):
    id: uuid.UUID
    nombre_archivo_original: str
    nombre_archivo_almacenado: str
    tipo_mime: str
    tamano_bytes: int
    subido_por: Optional[UserReadSummary] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SOLICITUD AUDITORIA SCHEMAS
# ==========================================
class AuditoriaSolicitudCreate(BaseModel):
    motivo_solicitud: str = Field(..., min_length=3, max_length=150)
    mensaje_auditor: str = Field(..., min_length=5)
    es_informativa: bool = Field(
        default=False,
        description="Si es True, la observación es de carácter Informativo (color azul) y no genera llamada pendiente",
    )


class AuditoriaSolicitudResponder(BaseModel):
    respuesta_operador: str = Field(..., min_length=3)


class AuditoriaSolicitudRead(BaseModel):
    id: uuid.UUID
    orden_id: uuid.UUID
    motivo_solicitud: str
    mensaje_auditor: str
    respuesta_operador: Optional[str] = None
    fecha_respuesta: Optional[datetime] = None
    estado: EstadoSolicitudAuditoria
    auditor: Optional[UserReadSummary] = None
    respondido_por: Optional[UserReadSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# REGISTRO DE LLAMADAS A PACIENTES
# ==========================================
class RegistroLlamadaCreate(BaseModel):
    tipo_llamada: TipoLlamadaPaciente = Field(
        ..., description="Etapa correspondiente o tipo de llamada"
    )
    resultado: ResultadoLlamada = Field(
        ..., description="Resultado del contacto: EXITOSA, NO_CONTESTA, NUMERO_ERRONEO, REINTENTAR"
    )
    observaciones: Optional[str] = Field(
        None, description="Observaciones adicionales sobre la comunicacion"
    )
    completar_aviso_pendiente: bool = Field(
        default=True,
        description="Si es True y la llamada fue EXITOSA, da por cumplido cualquier aviso pendiente al paciente de esta orden",
    )


class RegistroLlamadaRead(BaseModel):
    id: uuid.UUID
    orden_id: uuid.UUID
    tipo_llamada: TipoLlamadaPaciente
    resultado: ResultadoLlamada
    observaciones: Optional[str] = None
    operador: Optional[UserReadSummary] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrdenLlamadaPendienteItem(BaseModel):
    """Esquema optimizado para la pantalla y bandeja de llamadas pendientes a pacientes."""
    id: uuid.UUID
    nro_orden: str
    estado: EstadoOrden
    tipo_llamada_requerida: TipoLlamadaPaciente
    motivo_aviso: str
    fecha_estado: datetime
    paciente_nombre: str
    paciente_documento: str
    paciente_telefono: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_horario: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_celular: Optional[str] = None
    contacto_email: Optional[str] = None
    sucursal_nombre: str
    mutual: str
    observaciones_ingreso: Optional[str] = None
    observacion_resultado_auditoria: Optional[str] = None
    debe_orden_medica: bool = False
    cant_intentos_previos: int = 0
    solicitudes_pendientes: List["AuditoriaSolicitudRead"] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# AUDIT LOG SCHEMAS
# ==========================================

class AuditoriaLogRead(BaseModel):
    id: uuid.UUID
    orden_id: uuid.UUID
    accion: str
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    detalles: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    created_at: datetime
    user: Optional[UserReadSummary] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ORDEN MEDICA SCHEMAS
# ==========================================
class OrdenMedicaBase(BaseModel):
    paciente_id: uuid.UUID = Field(..., description="ID del paciente")
    sucursal_id: uuid.UUID = Field(..., description="ID de la sucursal de emision")
    fecha_prescripcion: date = Field(..., description="Fecha de prescripcion medica")
    cantidad_ordenes_fisicas: int = Field(
        default=1, ge=1, le=100, description="Cantidad de ordenes/recetas fisicas"
    )
    mutual: str = Field(..., min_length=2, max_length=100, description="Mutual u Obra Social")
    nro_afiliado: Optional[str] = Field(
        None, max_length=50, description="Numero de credencial / afiliado"
    )
    valor_copago: Decimal = Field(
        default=Decimal("0.00"), ge=0, description="Valor del copago a abonar"
    )
    valor_estudios_no_autorizados: Decimal = Field(
        default=Decimal("0.00"), ge=0, description="Valor total de los estudios no autorizados"
    )
    abona_apb: bool = Field(
        default=False, description="Indica si el paciente abona Acto Profesional Bioquímico (APB)"
    )
    fecha_vencimiento: Optional[date] = Field(
        None, description="Fecha de vencimiento de la prescripcion"
    )
    numeros_auditoria: List[str] = Field(
        default_factory=list, description="Lista de numeros/codigos de autorizacion de auditoria"
    )
    debe_orden_medica: bool = Field(
        default=False, description="Indica si el paciente debe la orden medica fisica (recibida digital/mail)"
    )

    # Datos de contacto
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    contacto_horario: Optional[str] = Field(None, max_length=100)
    contacto_telefono: Optional[str] = Field(None, max_length=50)
    contacto_celular: Optional[str] = Field(None, max_length=50)
    contacto_email: Optional[EmailStr] = None
    observaciones_ingreso: Optional[str] = None


class OrdenMedicaCreate(OrdenMedicaBase):
    nro_afiliado: str = Field(..., min_length=1, max_length=50, description="Numero de credencial obligatorio")
    contacto_nombre: str = Field(..., min_length=2, max_length=150, description="Nombre de contacto obligatorio")
    contacto_horario: str = Field(..., min_length=1, max_length=100, description="Horario de contacto obligatorio")

    @model_validator(mode="after")
    def validate_contact_numbers(self):
        tel = (self.contacto_telefono or "").strip()
        cel = (self.contacto_celular or "").strip()
        if not tel and not cel:
            raise ValueError("Debe ingresar al menos un número de contacto (Teléfono fijo o Celular/WhatsApp)")
        return self


class OrdenMedicaUpdate(BaseModel):
    fecha_prescripcion: Optional[date] = None
    cantidad_ordenes_fisicas: Optional[int] = Field(None, ge=1, le=100)
    mutual: Optional[str] = Field(None, min_length=2, max_length=100)
    nro_afiliado: Optional[str] = Field(None, max_length=50)
    valor_copago: Optional[Decimal] = Field(None, ge=0)
    valor_estudios_no_autorizados: Optional[Decimal] = Field(None, ge=0)
    abona_apb: Optional[bool] = None
    fecha_vencimiento: Optional[date] = None

    numeros_auditoria: Optional[List[str]] = None
    contacto_nombre: Optional[str] = None
    contacto_horario: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_celular: Optional[str] = None
    contacto_email: Optional[EmailStr] = None
    observaciones_ingreso: Optional[str] = None
    debe_orden_medica: Optional[bool] = None


class OrdenMedicaCambioEstado(BaseModel):
    nuevo_estado: Optional[str] = Field(None, description="Nombre o codigo del nuevo estado")
    estado_id: Optional[int] = Field(None, description="ID numerico del estado (para integraciones API / n8n)")
    motivo: Optional[str] = Field(
        None, description="Observacion o motivo del cambio (requerido si se cancela o da de baja)"
    )
    motivo_cancelacion_id: Optional[uuid.UUID] = Field(
        None, description="ID del motivo de cancelacion seleccionado"
    )
    observacion_resultado: Optional[str] = Field(
        None, description="Observacion o resultado comunicado al paciente al finalizar auditoria"
    )


class OrdenMedicaAsignarAuditor(BaseModel):
    auditor_id: Optional[uuid.UUID] = Field(None, description="ID del auditor a asignar")


class OrdenMedicaListItem(BaseModel):
    id: uuid.UUID
    nro_orden: str
    estado: Any = "Ingreso"
    fecha_prescripcion: Any
    mutual: Optional[str] = "S/D"
    nro_afiliado: Optional[str] = None
    valor_copago: Decimal = Decimal("0.00")
    valor_estudios_no_autorizados: Decimal = Decimal("0.00")
    abona_apb: bool = False
    cantidad_ordenes_fisicas: int = 1

    numeros_auditoria: List[str] = Field(default_factory=list)
    debe_orden_medica: bool = False
    paciente: Optional[PacienteRead] = None
    sucursal: Optional[SucursalRead] = None
    created_by_user: Optional[UserReadSummary] = None
    assigned_auditor: Optional[UserReadSummary] = None
    cant_adjuntos: int = 0
    cant_solicitudes_pendientes: int = 0
    llamada_solicitud_completada: bool = False
    llamada_finalizada_completada: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrdenMedicaDetail(BaseModel):
    id: uuid.UUID
    nro_orden: str
    estado: Any = "Ingreso"
    fecha_prescripcion: Any
    cantidad_ordenes_fisicas: int = 1
    mutual: Optional[str] = "S/D"
    nro_afiliado: Optional[str] = None
    valor_copago: Decimal = Decimal("0.00")
    valor_estudios_no_autorizados: Decimal = Decimal("0.00")
    abona_apb: bool = False
    fecha_vencimiento: Optional[date] = None

    numeros_auditoria: List[str] = Field(default_factory=list)
    debe_orden_medica: bool = False
    contacto_nombre: Optional[str] = None
    contacto_horario: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_celular: Optional[str] = None
    contacto_email: Optional[str] = None
    observaciones_ingreso: Optional[str] = None
    observacion_resultado_auditoria: Optional[str] = None
    motivo_cancelacion: Optional[str] = None
    llamada_solicitud_completada: bool = False
    llamada_solicitud_fecha: Optional[datetime] = None
    llamada_solicitud_observacion: Optional[str] = None
    llamada_finalizada_completada: bool = False
    llamada_finalizada_fecha: Optional[datetime] = None
    llamada_finalizada_observacion: Optional[str] = None
    paciente: Optional[PacienteRead] = None
    sucursal: Optional[SucursalRead] = None
    created_by_user: Optional[UserReadSummary] = None
    assigned_auditor: Optional[UserReadSummary] = None
    adjuntos: List[AdjuntoOrdenRead] = []
    solicitudes: List[AuditoriaSolicitudRead] = []
    llamadas_registro: List[RegistroLlamadaRead] = []
    audit_logs: List[AuditoriaLogRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


    model_config = ConfigDict(from_attributes=True)

