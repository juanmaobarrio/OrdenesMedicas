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
# ESTUDIO DETALLE ITEM (CALCULADORA / AUDITORIA)
# ==========================================
class EstudioDetalleItem(BaseModel):
    codigo: Optional[str] = Field(None, max_length=50, description="Código de la práctica (ej: 660001)")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre descriptivo de la práctica o estudio")
    precio: Decimal = Field(default=Decimal("0.00"), ge=0, description="Precio particular si no está autorizado")
    autorizado: bool = Field(default=True, description="Indica si la práctica está autorizada (true) o no autorizada (false)")

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
    valor_apb: Decimal = Field(
        default=Decimal("0.00"), ge=0, description="Monto de APB a abonar por el paciente"
    )
    fecha_vencimiento: Optional[date] = Field(
        None, description="Fecha de vencimiento de la prescripcion"
    )
    numeros_auditoria: List[str] = Field(
        default_factory=list, description="Lista de numeros/codigos de autorizacion de auditoria"
    )
    estudios_autorizados: List[str] = Field(
        default_factory=list, description="Lista de estudios autorizados por la auditoría"
    )
    estudios_no_autorizados: List[str] = Field(
        default_factory=list, description="Lista de estudios no autorizados / rechazados"
    )
    estudios_detalle: Optional[List[EstudioDetalleItem]] = Field(
        default=None, description="Desglose detallado de estudios con código, nombre, precio y estado de autorización"
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
    sucursal_id: Optional[uuid.UUID] = Field(None, description="ID de la sucursal o sede de ingreso")
    mutual: Optional[str] = Field(None, min_length=2, max_length=100)
    nro_afiliado: Optional[str] = Field(None, max_length=50)
    valor_copago: Optional[Decimal] = Field(None, ge=0)
    valor_estudios_no_autorizados: Optional[Decimal] = Field(None, ge=0)
    abona_apb: Optional[bool] = None
    valor_apb: Optional[Decimal] = Field(None, ge=0)
    fecha_vencimiento: Optional[date] = None

    numeros_auditoria: Optional[List[str]] = None
    estudios_autorizados: Optional[List[str]] = None
    estudios_no_autorizados: Optional[List[str]] = None
    estudios_detalle: Optional[List[EstudioDetalleItem]] = None
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
    estudios_autorizados: Optional[List[str]] = Field(
        None, description="Lista de estudios autorizados"
    )
    estudios_no_autorizados: Optional[List[str]] = Field(
        None, description="Lista de estudios no autorizados"
    )
    estudios_detalle: Optional[List[EstudioDetalleItem]] = Field(
        None, description="Desglose detallado de estudios con código, nombre, precio y autorización"
    )
    valor_copago: Optional[Decimal] = Field(
        None, ge=0, description="Monto actualizado del copago al finalizar auditoria"
    )
    valor_estudios_no_autorizados: Optional[Decimal] = Field(
        None, ge=0, description="Monto de estudios no autorizados al finalizar auditoria"
    )
    valor_apb: Optional[Decimal] = Field(
        None, ge=0, description="Monto actualizado del APB al finalizar auditoria"
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
    valor_apb: Decimal = Decimal("0.00")
    cantidad_ordenes_fisicas: int = 1

    numeros_auditoria: List[str] = Field(default_factory=list)
    estudios_autorizados: List[str] = Field(default_factory=list)
    estudios_no_autorizados: List[str] = Field(default_factory=list)
    estudios_detalle: List[EstudioDetalleItem] = Field(default_factory=list)
    debe_orden_medica: bool = False
    indicaciones_ids: List[str] = Field(default_factory=list)
    mail_enviado: bool = False
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
    valor_apb: Decimal = Decimal("0.00")
    fecha_vencimiento: Optional[date] = None

    numeros_auditoria: List[str] = Field(default_factory=list)
    estudios_autorizados: List[str] = Field(default_factory=list)
    estudios_no_autorizados: List[str] = Field(default_factory=list)
    estudios_detalle: List[EstudioDetalleItem] = Field(default_factory=list)
    debe_orden_medica: bool = False
    contacto_nombre: Optional[str] = None
    contacto_horario: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_celular: Optional[str] = None
    contacto_email: Optional[str] = None
    observaciones_ingreso: Optional[str] = None
    observacion_resultado_auditoria: Optional[str] = None
    motivo_cancelacion: Optional[str] = None

    # Indicaciones clínicas y estado del correo
    indicaciones_ids: List[str] = Field(default_factory=list)
    indicaciones_texto: Optional[str] = None
    mail_enviado: bool = False
    mail_enviado_fecha: Optional[datetime] = None
    mail_enviado_por_id: Optional[uuid.UUID] = None
    mail_destinatario: Optional[str] = None
    mail_asunto: Optional[str] = None
    mail_cuerpo_html: Optional[str] = None
    mail_message_id: Optional[str] = None
    mail_programado_para: Optional[datetime] = None
    mail_auto_cancelado: bool = False

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


# ==========================================
# CONFIGURACION SISTEMA / APB
# ==========================================
class ConfiguracionAPBRead(BaseModel):
    valor_apb: Decimal = Field(..., description="Valor base vigente del Acto Profesional Bioquímico (APB)")
    descripcion: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConfiguracionAPBUpdate(BaseModel):
    valor_apb: Decimal = Field(..., ge=0, description="Nuevo valor de referencia del Acto Profesional Bioquímico (APB)")


# ==========================================
# FEATURE FLAGS / FUNCIONALIDADES DEL SISTEMA
# ==========================================
class SystemFeaturesConfig(BaseModel):
    modulo_mail: bool = Field(default=False, description="Activa el módulo y despacho de correos electrónicos de resolución médica")
    calculadora_estudios: bool = Field(default=False, description="Activa el botón y modal de calculadora interactiva de presupuestos")
    estudios_autorizacion: bool = Field(default=False, description="Activa los campos clínicos de prácticas autorizadas y no autorizadas")
    indicaciones_estudios: bool = Field(default=False, description="Activa la asignación y catálogo de indicaciones clínicas de preparación")
    asignar_auditor: bool = Field(default=False, description="Activa la asignación de auditor médico a la orden médica")

    model_config = ConfigDict(from_attributes=True)


class SystemFeaturesConfigUpdate(BaseModel):
    modulo_mail: Optional[bool] = None
    calculadora_estudios: Optional[bool] = None
    estudios_autorizacion: Optional[bool] = None
    indicaciones_estudios: Optional[bool] = None
    asignar_auditor: Optional[bool] = None


# ==========================================
# INDICACIONES DE ESTUDIOS SCHEMAS
# ==========================================
class IndicacionEstudioBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50, description="Código único (ej: AYUNO_8HS)")
    titulo: str = Field(..., min_length=2, max_length=150, description="Título visible en chip")
    instrucciones: str = Field(..., min_length=5, description="Texto detallado de preparación clínica")
    categoria: Optional[str] = Field(None, max_length=80, description="Categoría (Sangre, Orina, etc.)")
    color: str = Field(default="info", max_length=30, description="Color de chip (info, warn, success, contrast, danger)")
    orden_secuencia: int = Field(default=0, ge=0)
    activa: bool = Field(default=True)


class IndicacionEstudioCreate(IndicacionEstudioBase):
    pass


class IndicacionEstudioUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=2, max_length=50)
    titulo: Optional[str] = Field(None, min_length=2, max_length=150)
    instrucciones: Optional[str] = None
    categoria: Optional[str] = None
    color: Optional[str] = None
    orden_secuencia: Optional[int] = None
    activa: Optional[bool] = None


class IndicacionEstudioRead(IndicacionEstudioBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrdenActualizarIndicaciones(BaseModel):
    indicaciones_ids: List[str] = Field(..., description="Lista de códigos o IDs de indicaciones asignadas")
    indicaciones_texto: Optional[str] = Field(None, description="Texto consolidado y editable de indicaciones")


# ==========================================
# CONFIGURACIÓN Y DESPACHO DE EMAIL SCHEMAS
# ==========================================
class ConfiguracionMailAutomatizacionRead(BaseModel):
    envio_automatico: bool = Field(..., description="Si el envío automático de mails está activo")
    minutos_gracia: int = Field(..., description="Minutos de gracia programados antes del envío")
    zeptomail_configurado: bool = Field(..., description="Indica si existe token válido de ZeptoMail")
    remitente_email: str
    remitente_nombre: str


class ConfiguracionMailAutomatizacionUpdate(BaseModel):
    envio_automatico: bool = Field(..., description="Habilitar o pausar envío automático")
    minutos_gracia: int = Field(default=120, ge=1, le=1440, description="Minutos de gracia (1 a 1440)")


class PreviewEmailResolucionRead(BaseModel):
    destinatario_email: str
    destinatario_nombre: str
    asunto: str
    cuerpo_html: str
    tiene_email: bool
    ya_enviado: bool
    mail_enviado_fecha: Optional[datetime] = None
    plantilla_id: Optional[uuid.UUID] = None
    plantillas_disponibles: List["PlantillaEmailRead"] = []


class EnviarEmailResolucionRequest(BaseModel):
    destinatario_email: Optional[EmailStr] = None
    asunto: Optional[str] = None
    cuerpo_html: Optional[str] = None
    plantilla_id: Optional[uuid.UUID] = None
    observaciones_adicionales: Optional[str] = None



# ==========================================
# PLANTILLAS DE EMAIL SCHEMAS
# ==========================================
class PlantillaEmailBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=150)
    asunto: str = Field(..., min_length=2, max_length=255)
    cuerpo_html: str = Field(default="", description="Cuerpo HTML con soporte de placeholders")
    es_default: bool = Field(default=False)
    activa: bool = Field(default=True)


class PlantillaEmailCreate(PlantillaEmailBase):
    pass


class PlantillaEmailUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    asunto: Optional[str] = None
    cuerpo_html: Optional[str] = None
    es_default: Optional[bool] = None
    activa: Optional[bool] = None


class PlantillaEmailRead(PlantillaEmailBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrdenActualizarEstudiosAuditoria(BaseModel):
    estudios_autorizados: Optional[List[str]] = Field(default=None)
    estudios_no_autorizados: Optional[List[str]] = Field(default=None)
    estudios_detalle: Optional[List[EstudioDetalleItem]] = Field(default=None)


class OrdenActualizarEstudiosDetalle(BaseModel):
    estudios_detalle: List[EstudioDetalleItem] = Field(..., description="Listado detallado de estudios")
