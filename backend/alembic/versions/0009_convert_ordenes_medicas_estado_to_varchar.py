"""Convert ordenes_medicas estado to varchar for dynamic states

Revision ID: 0009_convert_ordenes_medicas_estado_to_varchar
Revises: 0008_sync_estados_orden_config_seq
Create Date: 2026-10-16 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0009_convert_ordenes_medicas_estado_to_varchar"
down_revision: Union[str, None] = "0008_sync_estados_orden_config_seq"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convierte ordenes_medicas.estado de tipo ENUM a VARCHAR(100)
    # Esta operación es 100% segura y preserva todos los registros existentes sin pérdida de datos.
    # Permite soportar estados creados dinámicamente en estados_orden_config sin colisiones de Enum.
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'ordenes_medicas' 
                          AND column_name = 'estado' 
                          AND data_type = 'USER-DEFINED'
                    ) THEN
                        ALTER TABLE ordenes_medicas ALTER COLUMN estado DROP DEFAULT;
                        ALTER TABLE ordenes_medicas ALTER COLUMN estado TYPE VARCHAR(100) USING estado::VARCHAR(100);
                        ALTER TABLE ordenes_medicas ALTER COLUMN estado SET DEFAULT 'Ingreso';
                    END IF;
                END $$;
                """
            )
        )
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'auditoria_logs' AND column_name = 'estado_anterior'
                    ) THEN
                        ALTER TABLE auditoria_logs ALTER COLUMN estado_anterior TYPE VARCHAR(100);
                        ALTER TABLE auditoria_logs ALTER COLUMN estado_nuevo TYPE VARCHAR(100);
                    END IF;
                END $$;
                """
            )
        )
        # Normalizar códigos en mayúsculas a sus nombres descriptivos legibles
        op.execute(
            sa.text(
                """
                UPDATE ordenes_medicas
                SET estado = CASE estado
                    WHEN 'INGRESO' THEN 'Ingreso'
                    WHEN 'EN_AUDITORIA' THEN 'en Auditoria'
                    WHEN 'SOLICITUDES_AUDITORIA' THEN 'Solicitudes de auditoria'
                    WHEN 'ACTUALIZADA' THEN 'Actualizada'
                    WHEN 'AUDITORIA_FINALIZADA' THEN 'Auditoria Finalizada'
                    WHEN 'DAR_DE_BAJA' THEN 'Dar de baja'
                    WHEN 'CANCELADA' THEN 'Cancelada'
                    WHEN 'CERRADA' THEN 'Cerrada'
                    ELSE estado
                END
                WHERE estado IN ('INGRESO', 'EN_AUDITORIA', 'SOLICITUDES_AUDITORIA', 'ACTUALIZADA', 'AUDITORIA_FINALIZADA', 'DAR_DE_BAJA', 'CANCELADA', 'CERRADA');

                UPDATE auditoria_logs
                SET estado_anterior = CASE estado_anterior
                    WHEN 'INGRESO' THEN 'Ingreso'
                    WHEN 'EN_AUDITORIA' THEN 'en Auditoria'
                    WHEN 'SOLICITUDES_AUDITORIA' THEN 'Solicitudes de auditoria'
                    WHEN 'ACTUALIZADA' THEN 'Actualizada'
                    WHEN 'AUDITORIA_FINALIZADA' THEN 'Auditoria Finalizada'
                    WHEN 'DAR_DE_BAJA' THEN 'Dar de baja'
                    WHEN 'CANCELADA' THEN 'Cancelada'
                    WHEN 'CERRADA' THEN 'Cerrada'
                    ELSE estado_anterior
                END
                WHERE estado_anterior IN ('INGRESO', 'EN_AUDITORIA', 'SOLICITUDES_AUDITORIA', 'ACTUALIZADA', 'AUDITORIA_FINALIZADA', 'DAR_DE_BAJA', 'CANCELADA', 'CERRADA');

                UPDATE auditoria_logs
                SET estado_nuevo = CASE estado_nuevo
                    WHEN 'INGRESO' THEN 'Ingreso'
                    WHEN 'EN_AUDITORIA' THEN 'en Auditoria'
                    WHEN 'SOLICITUDES_AUDITORIA' THEN 'Solicitudes de auditoria'
                    WHEN 'ACTUALIZADA' THEN 'Actualizada'
                    WHEN 'AUDITORIA_FINALIZADA' THEN 'Auditoria Finalizada'
                    WHEN 'DAR_DE_BAJA' THEN 'Dar de baja'
                    WHEN 'CANCELADA' THEN 'Cancelada'
                    WHEN 'CERRADA' THEN 'Cerrada'
                    ELSE estado_nuevo
                END
                WHERE estado_nuevo IN ('INGRESO', 'EN_AUDITORIA', 'SOLICITUDES_AUDITORIA', 'ACTUALIZADA', 'AUDITORIA_FINALIZADA', 'DAR_DE_BAJA', 'CANCELADA', 'CERRADA');

                -- Normalizar cualquier otro estado personalizado que tenga código en la tabla estados_orden_config
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'estados_orden_config') THEN
                    UPDATE ordenes_medicas om
                    SET estado = eoc.nombre
                    FROM estados_orden_config eoc
                    WHERE om.estado = eoc.codigo;

                    UPDATE auditoria_logs al
                    SET estado_anterior = eoc.nombre
                    FROM estados_orden_config eoc
                    WHERE al.estado_anterior = eoc.codigo;

                    UPDATE auditoria_logs al
                    SET estado_nuevo = eoc.nombre
                    FROM estados_orden_config eoc
                    WHERE al.estado_nuevo = eoc.codigo;
                END IF;
                """
            )
        )


def downgrade() -> None:
    pass
