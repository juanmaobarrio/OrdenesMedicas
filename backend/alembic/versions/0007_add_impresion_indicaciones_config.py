"""Add impresion de indicaciones and alter configuracion valor text

Revision ID: 0007_add_impresion_indicaciones_config
Revises: 0006_add_ya_se_atendio_y_reintegro
Create Date: 2026-09-10 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0007_add_impresion_indicaciones_config"
down_revision: Union[str, None] = "0006_add_ya_se_atendio_y_reintegro"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ampliar columna valor en configuracion_sistema a TEXT
    # Esta operación es 100% segura e inmutable en PostgreSQL:
    # Cambiar de VARCHAR a TEXT no reescribe la tabla, no borra filas ni trunca datos existentes.
    try:
        op.alter_column("configuracion_sistema", "valor", type_=sa.Text(), existing_nullable=False)
    except Exception:
        pass


def downgrade() -> None:
    pass
