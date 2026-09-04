"""Add estudios detalle to ordenes medicas

Revision ID: 0005_add_estudios_detalle
Revises: 0004_add_indicaciones_and_email_fields
Create Date: 2026-09-04 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_add_estudios_detalle"
down_revision: Union[str, None] = "0004_add_indicaciones_and_email_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")
    # 1. Columna estudios_detalle en ordenes_medicas
    try:
        op.add_column(
            "ordenes_medicas",
            sa.Column("estudios_detalle", json_type, nullable=False, server_default=sa.text("'[]'")),
        )
    except Exception:
        pass

    # 2. Tabla plantillas_email
    try:
        op.create_table(
            "plantillas_email",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("codigo", sa.String(50), nullable=False, unique=True),
            sa.Column("nombre", sa.String(150), nullable=False),
            sa.Column("asunto", sa.String(255), nullable=False),
            sa.Column("cuerpo_html", sa.Text(), nullable=False),
            sa.Column("es_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_plantillas_email_codigo", "plantillas_email", ["codigo"], unique=True)
    except Exception:
        pass

    # 3. Plantilla por defecto con HTML
    try:
        from backend.app.core.templates_email import obtener_plantilla_base_html
        import uuid
        html_code = obtener_plantilla_base_html().replace("'", "''")
        uid = str(uuid.uuid4())
        op.execute(
            sa.text(
                f"""
                INSERT INTO plantillas_email (id, codigo, nombre, asunto, cuerpo_html, es_default, activa)
                VALUES ('{uid}', 'DEFAULT', 'Plantilla Estándar de Resolución Médica', 'Resolución de Auditoría Médica - Orden N° {{{{nro_orden}}}}', '{html_code}', true, true)
                ON CONFLICT (codigo) DO NOTHING;
                """
            )
        )
    except Exception:
        pass

    # 4. Feature Flags iniciales (inactivas por defecto)
    try:
        features = [
            ("FEATURE_MODULO_MAIL", "false", "Activa el módulo y despacho de correos electrónicos de resolución médica"),
            ("FEATURE_CALCULADORA_ESTUDIOS", "false", "Activa el botón y modal de calculadora interactiva de presupuestos"),
            ("FEATURE_ESTUDIOS_AUTORIZACION", "false", "Activa los campos clínicos de prácticas autorizadas y no autorizadas"),
            ("FEATURE_INDICACIONES_ESTUDIOS", "false", "Activa la asignación y catálogo de indicaciones clínicas de preparación"),
            ("FEATURE_ASIGNAR_AUDITOR", "false", "Activa la asignación de auditor médico a la orden médica"),
        ]
        for f_key, f_val, f_desc in features:
            op.execute(
                sa.text(
                    f"INSERT INTO configuracion_sistema (clave, valor, descripcion) "
                    f"VALUES ('{f_key}', '{f_val}', '{f_desc}') "
                    f"ON CONFLICT (clave) DO NOTHING;"
                )
            )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_table("plantillas_email")
    except Exception:
        pass
    try:
        op.drop_column("ordenes_medicas", "estudios_detalle")
    except Exception:
        pass
