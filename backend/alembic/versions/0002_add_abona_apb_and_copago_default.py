"""Add abona_apb and copago_default

Revision ID: 0002_add_abona_apb_and_copago_default
Revises: 0001_initial_schema
Create Date: 2025-02-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_abona_apb_and_copago_default"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # 1. Columna abona_apb en ordenes_medicas
    try:
        op.add_column(
            "ordenes_medicas",
            sa.Column("abona_apb", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    except Exception:
        pass

    # 2. Columna copago_default en obras_sociales
    try:
        op.add_column(
            "obras_sociales",
            sa.Column("copago_default", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        )
    except Exception:
        pass

    # 3. Valores ENUM adicionales para PostgreSQL
    if dialect_name == "postgresql":
        op.execute(sa.text("ALTER TYPE estado_solicitud_enum ADD VALUE IF NOT EXISTS 'INFORMACION';"))
        op.execute(sa.text("ALTER TYPE tipo_llamada_enum ADD VALUE IF NOT EXISTS 'CONSULTA_PACIENTE';"))
        op.execute(sa.text("ALTER TYPE tipo_llamada_enum ADD VALUE IF NOT EXISTS 'SEGUIMIENTO_SUCURSAL';"))
        op.execute(sa.text("ALTER TYPE tipo_llamada_enum ADD VALUE IF NOT EXISTS 'OTRO';"))


def downgrade() -> None:
    try:
        op.drop_column("obras_sociales", "copago_default")
    except Exception:
        pass
    try:
        op.drop_column("ordenes_medicas", "abona_apb")
    except Exception:
        pass
