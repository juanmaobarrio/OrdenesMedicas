import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


from backend.app.modules.pacientes.models import Paciente
from backend.app.modules.users.models import Sucursal, User
from backend.app.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EstadoOrden(str, enum.Enum):
    """Estados del ciclo de vida de una orden medica."""
    INGRESO = "Ingreso"
    EN_AUDITORIA = "en Auditoria"
    SOLICITUDES_AUDITORIA = "Solicitudes de auditoria"
    ACTUALIZADA = "Actualizada"
    AUDITORIA_FINALIZADA = "Auditoria Finalizada"
    DAR_DE_BAJA = "Dar de baja"
    CANCELADA = "Cancelada"
    CERRADA = "Cerrada"


class TipoEstadoOrden(str, enum.Enum):
    """Clasificacion de estado: en proceso activo vs finalizacion/terminal."""
    PROCESO = "PROCESO"
    FINALIZACION = "FINALIZACION"


class EstadoSolicitudAuditoria(str, enum.Enum):
    """Estados de una solicitud/observacion de auditoria."""
    PENDIENTE = "PENDIENTE"
    RESPONDIDA = "RESPONDIDA"
    CERRADA = "CERRADA"


class TipoLlamadaPaciente(str, enum.Enum):
    """Tipos de llamada/notificacion al paciente segun la etapa."""
    SOLICITUD_AUDITORIA = "SOLICITUD_AUDITORIA"
    AUDITORIA_FINALIZADA = "AUDITORIA_FINALIZADA"


class ResultadoLlamada(str, enum.Enum):
    """Resultado del intento de comunicacion con el paciente."""
    EXITOSA = "EXITOSA"
    NO_CONTESTA = "NO_CONTESTA"
    NUMERO_ERRONEO = "NUMERO_ERRONEO"
    REINTENTAR = "REINTENTAR"



class OrdenMedica(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo principal de la Orden Medica."""
    __tablename__ = "ordenes_medicas"

    # Codigo secuencial o identificador legible de la orden
    nro_orden: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="Identificador unico de la orden"
    )

    # Relaciones obligatorias
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sucursal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_auditor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )


    # Estado del ciclo de vida
    estado: Mapped[EstadoOrden] = mapped_column(
        SQLEnum(EstadoOrden, name="estado_orden_enum"),
        default=EstadoOrden.INGRESO,
        nullable=False,
        index=True,
    )

    # Datos especificos de la orden medica
    fecha_prescripcion: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Fecha de prescripcion medica"
    )
    cantidad_ordenes_fisicas: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="Cantidad de comprobantes / cupones fisicos"
    )
    mutual: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Mutual u Obra Social aplicada"
    )
    valor_copago: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="Copago a abonar por el paciente"
    )
    valor_estudios_no_autorizados: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="Valor total de los estudios no autorizados"
    )
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha limite de vencimiento de la prescripcion"
    )


    # Numeros de auditoria (Array / JSONB para permitir multiples registros)
    numeros_auditoria: Mapped[List[str]] = mapped_column(
        JSON_TYPE, default=list, nullable=False, comment="Lista de codigos / numeros de auditoria autorizados"
    )

    # Control de orden fisica adeudada (recibida por mail/digital)
    debe_orden_medica: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Indica si el paciente debe la orden fisica original"
    )


    # Datos de contacto para seguimiento
    contacto_nombre: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contacto_horario: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contacto_telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contacto_celular: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contacto_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Observaciones generales
    observaciones_ingreso: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observacion_resultado_auditoria: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Observacion o resolucion comunicada al paciente al finalizar auditoria"
    )
    motivo_cancelacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Control de llamadas y aviso a pacientes en hitos clave
    # Hito 1: Cuando pasa a 'Solicitudes de auditoria'
    llamada_solicitud_completada: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True, comment="Indica si ya se aviso al paciente sobre la solicitud"
    )
    llamada_solicitud_fecha: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    llamada_solicitud_observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hito 2: Cuando pasa a 'Auditoria Finalizada'
    llamada_finalizada_completada: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True, comment="Indica si ya se aviso al paciente sobre la auditoria finalizada"
    )
    llamada_finalizada_fecha: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    llamada_finalizada_observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones ORM
    paciente: Mapped[Paciente] = relationship("Paciente", lazy="selectin")
    sucursal: Mapped[Sucursal] = relationship("Sucursal", lazy="selectin")
    created_by_user: Mapped[User] = relationship(
        "User", foreign_keys=[created_by_user_id], lazy="selectin"
    )
    assigned_auditor: Mapped[Optional[User]] = relationship(
        "User", foreign_keys=[assigned_auditor_id], lazy="selectin"
    )
    adjuntos: Mapped[List["AdjuntoOrden"]] = relationship(
        "AdjuntoOrden", back_populates="orden", cascade="all, delete-orphan", lazy="selectin"
    )
    solicitudes: Mapped[List["AuditoriaSolicitud"]] = relationship(
        "AuditoriaSolicitud", back_populates="orden", cascade="all, delete-orphan", lazy="selectin", order_by="desc(AuditoriaSolicitud.created_at)"
    )
    audit_logs: Mapped[List["AuditoriaLog"]] = relationship(
        "AuditoriaLog", back_populates="orden", cascade="all, delete-orphan", lazy="selectin", order_by="desc(AuditoriaLog.created_at)"
    )
    llamadas_registro: Mapped[List["RegistroLlamadaPaciente"]] = relationship(
        "RegistroLlamadaPaciente", back_populates="orden", cascade="all, delete-orphan", lazy="selectin", order_by="desc(RegistroLlamadaPaciente.created_at)"
    )



class AdjuntoOrden(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Archivos adjuntos asociados a una orden (fotos, recetas escaneadas, PDFs)."""
    __tablename__ = "ordenes_adjuntos"

    orden_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subido_por_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    nombre_archivo_original: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_archivo_almacenado: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_almacenamiento: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo_mime: Mapped[str] = mapped_column(String(100), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relaciones ORM
    orden: Mapped[OrdenMedica] = relationship("OrdenMedica", back_populates="adjuntos")
    subido_por: Mapped[User] = relationship("User", lazy="selectin")


class MotivoCancelacion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Catalogo administrable de motivos unicos de cancelacion para estadisticas."""
    __tablename__ = "motivos_cancelacion"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EstadoOrdenConfig(Base, TimestampMixin):
    """Catalogo dinamico y configurable de estados con ID numerico para integraciones API."""
    __tablename__ = "estados_orden_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tipo: Mapped[TipoEstadoOrden] = mapped_column(
        SQLEnum(TipoEstadoOrden, name="tipo_estado_orden_enum"),
        default=TipoEstadoOrden.PROCESO,
        nullable=False,
    )
    requiere_motivo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    color_badge: Mapped[str] = mapped_column(String(30), default="info", nullable=False)
    icono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    es_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    orden_secuencia: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AuditoriaSolicitud(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Solicitudes u observaciones emitidas por un auditor medico a la sucursal."""
    __tablename__ = "auditoria_solicitudes"

    orden_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    auditor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    motivo_solicitud: Mapped[str] = mapped_column(
        String(150), nullable=False, comment="Ej: Firma ilegible, Falta diagnostico, etc."
    )
    mensaje_auditor: Mapped[str] = mapped_column(Text, nullable=False)

    # Respuesta de la sucursal
    respuesta_operador: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    respondido_por_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    fecha_respuesta: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    estado: Mapped[EstadoSolicitudAuditoria] = mapped_column(
        SQLEnum(EstadoSolicitudAuditoria, name="estado_solicitud_enum"),
        default=EstadoSolicitudAuditoria.PENDIENTE,
        nullable=False,
    )

    # Relaciones ORM
    orden: Mapped[OrdenMedica] = relationship("OrdenMedica", back_populates="solicitudes")
    auditor: Mapped[User] = relationship("User", foreign_keys=[auditor_id], lazy="selectin")
    respondido_por: Mapped[Optional[User]] = relationship(
        "User", foreign_keys=[respondido_por_id], lazy="selectin"
    )


class AuditoriaLog(Base, UUIDPrimaryKeyMixin):
    """Bitacora inmutable de cambios (Audit Trail) para trazabilidad legal."""
    __tablename__ = "auditoria_logs"

    orden_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    accion: Mapped[str] = mapped_column(
        String(80), nullable=False, comment="Ej: CREACION, CAMBIO_ESTADO, ADJUNTAR_DOCUMENTO"
    )
    estado_anterior: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estado_nuevo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    detalles: Mapped[Dict[str, Any]] = mapped_column(
        JSON_TYPE, default=dict, nullable=False, comment="Payload con snapshot del cambio"
    )

    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


    # Relaciones ORM
    orden: Mapped[OrdenMedica] = relationship("OrdenMedica", back_populates="audit_logs")
    user: Mapped[Optional[User]] = relationship("User", lazy="selectin")


class RegistroLlamadaPaciente(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registro historico de cada intento o concrecion de llamada al paciente."""
    __tablename__ = "ordenes_llamadas_pacientes"

    orden_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    tipo_llamada: Mapped[TipoLlamadaPaciente] = mapped_column(
        SQLEnum(TipoLlamadaPaciente, name="tipo_llamada_enum"),
        nullable=False,
        comment="Etapa en la que se realizo la llamada",
    )
    resultado: Mapped[ResultadoLlamada] = mapped_column(
        SQLEnum(ResultadoLlamada, name="resultado_llamada_enum"),
        nullable=False,
        comment="Resultado del contacto (EXITOSA, NO_CONTESTA, etc.)",
    )
    observaciones: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Detalle de lo conversado o motivo de falla"
    )

    # Relaciones ORM
    orden: Mapped[OrdenMedica] = relationship("OrdenMedica", back_populates="llamadas_registro")
    operador: Mapped[User] = relationship("User", lazy="selectin")


