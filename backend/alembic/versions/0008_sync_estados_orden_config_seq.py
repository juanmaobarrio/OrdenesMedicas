"""Fix sequence estados_orden_config_id_seq

Revision ID: 0008_sync_estados_orden_config_seq
Revises: 0007_add_impresion_indicaciones_config
Create Date: 2026-10-16 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0008_sync_estados_orden_config_seq"
down_revision: Union[str, None] = "0007_add_impresion_indicaciones_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sincroniza la secuencia id de estados_orden_config en PostgreSQL con el max(id) existente
    # Esto evita el error de clave duplicada (UniqueViolationError: duplicate key value violates
    # unique constraint "estados_orden_config_pkey") generado cuando se sembraron registros
    # iniciales con IDs manuales (1..8) sin avanzar el contador interno de la secuencia.
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        try:
            op.execute(
                sa.text(
                    """
                    SELECT setval(
                        pg_get_serial_sequence('estados_orden_config', 'id'),
                        COALESCE((SELECT MAX(id) FROM estados_orden_config), 1),
                        true
                    );
                    """
                )
            )
        except Exception:
            pass


def downgrade() -> None:
    pass
