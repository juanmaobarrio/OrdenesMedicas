import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import Boolean, Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


from backend.app.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Paciente(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo para la gestion de pacientes de la institucion medica."""
    __tablename__ = "pacientes"

    documento: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False, comment="DNI / Documento de identidad"
    )
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    obra_social: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="Obra social o cobertura medica"
    )
    nro_afiliado: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Numero de credencial / afiliado"
    )
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def nombre_completo(self) -> str:
        """Devuelve el apellido y nombre completo formateado."""
        return f"{self.apellidos}, {self.nombres}".strip()


class ObraSocial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo para el catálogo maestro de Obras Sociales / Mutuales."""
    __tablename__ = "obras_sociales"

    codigo: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="Codigo interno unico de la mutual"
    )
    sigla: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False, comment="Sigla o acronimo (ej: OSDE, SM, PAMI)"
    )
    nombre: Mapped[str] = mapped_column(
        String(150), nullable=False, comment="Razon social o nombre completo"
    )
    codigo_externo: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Codigo de integracion o facturacion externa"
    )
    dias_vencimiento: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False, comment="Dias de validez/vencimiento de la orden"
    )
    copago_default: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="Valor de copago predeterminado"
    )
    porcentaje_cobertura_apb: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False, comment="Porcentaje de cobertura de APB (0 a 100%)"
    )
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def display_name(self) -> str:
        return f"{self.sigla} - {self.nombre}"


