"""Initial database schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sucursales
    op.create_table(
        "sucursales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sucursales_codigo", "sucursales", ["codigo"], unique=True)
    op.create_index("ix_sucursales_id", "sucursales", ["id"], unique=False)

    # 2. Permissions
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_module", "permissions", ["module"], unique=False)
    op.create_index("ix_permissions_id", "permissions", ["id"], unique=False)

    # 3. Roles
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)
    op.create_index("ix_roles_id", "roles", ["id"], unique=False)

    # 4. Role Permissions (Association)
    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    # 5. Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sucursal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sucursales.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    # 6. Pacientes
    op.create_table(
        "pacientes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("documento", sa.String(30), nullable=False),
        sa.Column("nombres", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("obra_social", sa.String(100), nullable=True),
        sa.Column("nro_afiliado", sa.String(50), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pacientes_documento", "pacientes", ["documento"], unique=True)
    op.create_index("ix_pacientes_obra_social", "pacientes", ["obra_social"], unique=False)
    op.create_index("ix_pacientes_id", "pacientes", ["id"], unique=False)

    # 6.1 Obras Sociales / Mutuales
    op.create_table(
        "obras_sociales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("sigla", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("codigo_externo", sa.String(50), nullable=True),
        sa.Column("dias_vencimiento", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_obras_sociales_codigo", "obras_sociales", ["codigo"], unique=True)
    op.create_index("ix_obras_sociales_sigla", "obras_sociales", ["sigla"], unique=False)
    op.create_index("ix_obras_sociales_id", "obras_sociales", ["id"], unique=False)

    # 6.2 Motivos de Cancelación
    op.create_table(
        "motivos_cancelacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_motivos_cancelacion_codigo", "motivos_cancelacion", ["codigo"], unique=True)
    op.create_index("ix_motivos_cancelacion_id", "motivos_cancelacion", ["id"], unique=False)

    # 6.3 Configuración de Estados de Órdenes
    tipo_estado_orden_enum = postgresql.ENUM(
        "PROCESO", "FINALIZACION",
        name="tipo_estado_orden_enum",
        create_type=False
    )
    tipo_estado_orden_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "estados_orden_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column("tipo", tipo_estado_orden_enum, nullable=False, server_default="PROCESO"),
        sa.Column("requiere_motivo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("color_badge", sa.String(30), nullable=False, server_default="info"),
        sa.Column("icono", sa.String(50), nullable=True),
        sa.Column("es_sistema", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("orden_secuencia", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_estados_orden_config_codigo", "estados_orden_config", ["codigo"], unique=True)

    # 7. Ordenes Medicas
    estado_orden_enum = postgresql.ENUM(
        "Ingreso", "en Auditoria", "Solicitudes de auditoria", "Actualizada",
        "Auditoria Finalizada", "Dar de baja", "Cancelada", "Cerrada",
        name="estado_orden_enum",
        create_type=False
    )
    estado_orden_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ordenes_medicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("nro_orden", sa.String(50), nullable=False),
        sa.Column("paciente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sucursal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assigned_auditor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("estado", estado_orden_enum, nullable=False, server_default="Ingreso"),
        sa.Column("fecha_prescripcion", sa.Date(), nullable=False),
        sa.Column("cantidad_ordenes_fisicas", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("mutual", sa.String(100), nullable=False),
        sa.Column("valor_copago", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_estudios_no_autorizados", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("numeros_auditoria", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("debe_orden_medica", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("contacto_nombre", sa.String(150), nullable=True),
        sa.Column("contacto_horario", sa.String(100), nullable=True),
        sa.Column("contacto_telefono", sa.String(50), nullable=True),
        sa.Column("contacto_celular", sa.String(50), nullable=True),
        sa.Column("contacto_email", sa.String(255), nullable=True),
        sa.Column("observaciones_ingreso", sa.Text(), nullable=True),
        sa.Column("observacion_resultado_auditoria", sa.Text(), nullable=True),
        sa.Column("motivo_cancelacion", sa.Text(), nullable=True),
        sa.Column("llamada_solicitud_completada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("llamada_solicitud_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("llamada_solicitud_observacion", sa.Text(), nullable=True),
        sa.Column("llamada_finalizada_completada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("llamada_finalizada_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("llamada_finalizada_observacion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ordenes_medicas_nro_orden", "ordenes_medicas", ["nro_orden"], unique=True)
    op.create_index("ix_ordenes_medicas_paciente_id", "ordenes_medicas", ["paciente_id"], unique=False)
    op.create_index("ix_ordenes_medicas_sucursal_id", "ordenes_medicas", ["sucursal_id"], unique=False)
    op.create_index("ix_ordenes_medicas_assigned_auditor_id", "ordenes_medicas", ["assigned_auditor_id"], unique=False)
    op.create_index("ix_ordenes_medicas_estado", "ordenes_medicas", ["estado"], unique=False)
    op.create_index("ix_ordenes_medicas_mutual", "ordenes_medicas", ["mutual"], unique=False)
    op.create_index("ix_ordenes_medicas_id", "ordenes_medicas", ["id"], unique=False)

    # 8. Ordenes Adjuntos
    op.create_table(
        "ordenes_adjuntos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("orden_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subido_por_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nombre_archivo_original", sa.String(255), nullable=False),
        sa.Column("nombre_archivo_almacenado", sa.String(255), nullable=False),
        sa.Column("ruta_almacenamiento", sa.String(500), nullable=False),
        sa.Column("tipo_mime", sa.String(100), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ordenes_adjuntos_orden_id", "ordenes_adjuntos", ["orden_id"], unique=False)
    op.create_index("ix_ordenes_adjuntos_id", "ordenes_adjuntos", ["id"], unique=False)

    # 9. Auditoria Solicitudes
    estado_solicitud_enum = postgresql.ENUM(
        "PENDIENTE", "RESPONDIDA", "CERRADA",
        name="estado_solicitud_enum",
        create_type=False
    )
    estado_solicitud_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "auditoria_solicitudes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("orden_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("auditor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("motivo_solicitud", sa.String(150), nullable=False),
        sa.Column("mensaje_auditor", sa.Text(), nullable=False),
        sa.Column("respuesta_operador", sa.Text(), nullable=True),
        sa.Column("respondido_por_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fecha_respuesta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", estado_solicitud_enum, nullable=False, server_default="PENDIENTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auditoria_solicitudes_orden_id", "auditoria_solicitudes", ["orden_id"], unique=False)
    op.create_index("ix_auditoria_solicitudes_id", "auditoria_solicitudes", ["id"], unique=False)

    # 10. Auditoria Logs
    op.create_table(
        "auditoria_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("orden_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("accion", sa.String(80), nullable=False),
        sa.Column("estado_anterior", sa.String(50), nullable=True),
        sa.Column("estado_nuevo", sa.String(50), nullable=True),
        sa.Column("detalles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auditoria_logs_orden_id", "auditoria_logs", ["orden_id"], unique=False)
    op.create_index("ix_auditoria_logs_created_at", "auditoria_logs", ["created_at"], unique=False)
    op.create_index("ix_auditoria_logs_id", "auditoria_logs", ["id"], unique=False)

    # 11. Ordenes Llamadas Pacientes
    tipo_llamada_enum = postgresql.ENUM(
        "SOLICITUD_AUDITORIA", "AUDITORIA_FINALIZADA",
        name="tipo_llamada_enum",
        create_type=False
    )
    tipo_llamada_enum.create(op.get_bind(), checkfirst=True)

    resultado_llamada_enum = postgresql.ENUM(
        "EXITOSA", "NO_CONTESTA", "NUMERO_ERRONEO", "REINTENTAR",
        name="resultado_llamada_enum",
        create_type=False
    )
    resultado_llamada_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ordenes_llamadas_pacientes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("orden_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ordenes_medicas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo_llamada", tipo_llamada_enum, nullable=False),
        sa.Column("resultado", resultado_llamada_enum, nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ordenes_llamadas_pacientes_orden_id", "ordenes_llamadas_pacientes", ["orden_id"], unique=False)
    op.create_index("ix_ordenes_llamadas_pacientes_id", "ordenes_llamadas_pacientes", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("ordenes_llamadas_pacientes")
    op.drop_table("auditoria_logs")
    op.drop_table("auditoria_solicitudes")
    op.drop_table("ordenes_adjuntos")
    op.drop_table("ordenes_medicas")
    op.drop_table("estados_orden_config")
    op.drop_table("motivos_cancelacion")
    op.drop_table("obras_sociales")
    op.drop_table("pacientes")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
    op.drop_table("sucursales")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS resultado_llamada_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS tipo_llamada_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS tipo_estado_orden_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS estado_solicitud_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS estado_orden_enum CASCADE;")
