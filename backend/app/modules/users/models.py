import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship


from backend.app.shared.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Tabla intermedia de asociacion Role <-> Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)



class Sucursal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo para la gestion de sedes/sucursales."""
    __tablename__ = "sucursales"

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    users: Mapped[List["User"]] = relationship("User", back_populates="sucursal")


class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo de permisos atomicos del sistema."""
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    module: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relaciones
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo de roles de usuario (RBAC)."""
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hierarchy_level: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False, comment="Nivel jerárquico: 100=Admin, 50=Auditor, 10=Usuario"
    )

    # Relaciones
    permissions: Mapped[List[Permission]] = relationship(
        Permission, secondary=role_permissions, back_populates="roles", lazy="selectin"
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Modelo principal de usuarios del sistema."""
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Claves foraneas
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    sucursal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sucursales.id", ondelete="SET NULL"), nullable=True
    )


    # Relaciones
    role: Mapped[Role] = relationship("Role", back_populates="users", lazy="selectin")
    sucursal: Mapped[Optional[Sucursal]] = relationship(
        "Sucursal", back_populates="users", lazy="selectin"
    )

    @property
    def full_name(self) -> str:
        """Devuelve el nombre y apellido completo concatenado."""
        return f"{self.first_name} {self.last_name}".strip()

