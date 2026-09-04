"""Add indicaciones estudios and email fields to ordenes medicas

Revision ID: 0004_add_indicaciones_and_email_fields
Revises: 0003_add_apb_config_and_order_valor_apb
Create Date: 2026-09-02 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_add_indicaciones_and_email_fields"
down_revision: Union[str, None] = "0003_add_apb_config_and_order_valor_apb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla de indicaciones de estudios
    try:
        op.create_table(
            "indicaciones_estudios",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("codigo", sa.String(50), nullable=False, unique=True),
            sa.Column("titulo", sa.String(150), nullable=False),
            sa.Column("instrucciones", sa.Text(), nullable=False),
            sa.Column("categoria", sa.String(80), nullable=True),
            sa.Column("color", sa.String(30), nullable=False, server_default="info"),
            sa.Column("orden_secuencia", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_indicaciones_estudios_codigo", "indicaciones_estudios", ["codigo"], unique=True)
    except Exception:
        pass

    # 2. Nuevas columnas en ordenes_medicas
    json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")
    cols_to_add = [
        ("indicaciones_ids", json_type, sa.text("'[]'")),
        ("indicaciones_texto", sa.Text(), None),
        ("mail_enviado", sa.Boolean(), sa.text("false")),
        ("mail_enviado_fecha", sa.DateTime(timezone=True), None),
        ("mail_enviado_por_id", sa.Uuid(), None),
        ("mail_destinatario", sa.String(255), None),
        ("mail_asunto", sa.String(255), None),
        ("mail_cuerpo_html", sa.Text(), None),
        ("mail_message_id", sa.String(150), None),
        ("mail_programado_para", sa.DateTime(timezone=True), None),
        ("mail_auto_cancelado", sa.Boolean(), sa.text("false")),
    ]

    for col_name, col_type, default_val in cols_to_add:
        try:
            op.add_column(
                "ordenes_medicas",
                sa.Column(col_name, col_type, nullable=True if default_val is None else False, server_default=default_val)
            )
        except Exception:
            pass

    # Claves de configuración por defecto para envío de correos
    try:
        op.execute(
            sa.text(
                "INSERT INTO configuracion_sistema (clave, valor, descripcion) "
                "VALUES ('ENVIO_MAIL_AUTOMATICO', 'false', 'Indica si el envio de correos por auditoria finalizada es automatico (true) o manual (false)') "
                "ON CONFLICT (clave) DO NOTHING;"
            )
        )
        op.execute(
            sa.text(
                "INSERT INTO configuracion_sistema (clave, valor, descripcion) "
                "VALUES ('MINUTOS_GRACIA_ENVIO_MAIL', '120', 'Minutos de espera programada antes del envio automatico del mail (permite cancelacion manual)') "
                "ON CONFLICT (clave) DO NOTHING;"
            )
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_table("indicaciones_estudios")
    except Exception:
        pass
