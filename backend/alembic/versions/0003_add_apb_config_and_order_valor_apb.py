"""Add apb config and order valor_apb

Revision ID: 0003_add_apb_config_and_order_valor_apb
Revises: 0002_add_abona_apb_and_copago_default
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_apb_config_and_order_valor_apb"
down_revision: Union[str, None] = "0002_add_abona_apb_and_copago_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Columna valor_apb en ordenes_medicas
    try:
        op.add_column(
            "ordenes_medicas",
            sa.Column("valor_apb", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        )
    except Exception:
        pass

    # 2. Columna porcentaje_cobertura_apb en obras_sociales
    try:
        op.add_column(
            "obras_sociales",
            sa.Column("porcentaje_cobertura_apb", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.00")),
        )
    except Exception:
        pass

    # 3. Tabla configuracion_sistema
    try:
        op.create_table(
            "configuracion_sistema",
            sa.Column("clave", sa.String(100), primary_key=True),
            sa.Column("valor", sa.String(255), nullable=False),
            sa.Column("descripcion", sa.String(255), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.execute(
            sa.text(
                "INSERT INTO configuracion_sistema (clave, valor, descripcion) "
                "VALUES ('VALOR_APB', '0.00', 'Valor vigente de referencia del Acto Profesional Bioquímico (APB)')"
            )
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_table("configuracion_sistema")
    except Exception:
        pass
    try:
        op.drop_column("obras_sociales", "porcentaje_cobertura_apb")
    except Exception:
        pass
    try:
        op.drop_column("ordenes_medicas", "valor_apb")
    except Exception:
        pass
