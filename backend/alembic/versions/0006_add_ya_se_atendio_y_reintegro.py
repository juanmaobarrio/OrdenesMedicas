"""Add ya_se_atendio and monto_abonado_atencion to ordenes_medicas

Revision ID: 0006_add_ya_se_atendio_y_reintegro
Revises: 0005_add_estudios_detalle
Create Date: 2026-09-04 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0006_add_ya_se_atendio_y_reintegro"
down_revision: Union[str, None] = "0005_add_estudios_detalle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.add_column(
            "ordenes_medicas",
            sa.Column("ya_se_atendio", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    except Exception:
        pass

    try:
        op.add_column(
            "ordenes_medicas",
            sa.Column("monto_abonado_atencion", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_column("ordenes_medicas", "monto_abonado_atencion")
    except Exception:
        pass

    try:
        op.drop_column("ordenes_medicas", "ya_se_atendio")
    except Exception:
        pass
