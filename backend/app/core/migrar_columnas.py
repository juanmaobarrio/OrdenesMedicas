import asyncio
from loguru import logger
from sqlalchemy import text
from backend.app.core.database import engine, AsyncSessionLocal
from backend.app.modules.ordenes.models import OrdenMedica
from sqlalchemy import select

async def fix_and_inspect():
    print("=== 1. VERIFICANDO Y CREANDO COLUMNAS EN BASE DE DATOS ===")
    async with engine.begin() as conn:
        dialect = conn.dialect.name
        print(f">>> Motor de base de datos detectado: {dialect}")

        if dialect == "sqlite":
            # SQLite safe column addition
            columns_to_add = [
                ("ordenes_medicas", "nro_afiliado", "VARCHAR(50)"),
                ("ordenes_medicas", "valor_estudios_no_autorizados", "NUMERIC(12, 2) DEFAULT 0.00"),
                ("ordenes_medicas", "observacion_resultado_auditoria", "TEXT"),
                ("ordenes_medicas", "debe_orden_medica", "BOOLEAN DEFAULT 0"),
                ("ordenes_medicas", "abona_apb", "BOOLEAN DEFAULT 0"),
                ("ordenes_medicas", "valor_apb", "NUMERIC(12, 2) DEFAULT 0.00"),
                ("ordenes_medicas", "estudios_autorizados", "JSON DEFAULT '[]'"),
                ("ordenes_medicas", "estudios_no_autorizados", "JSON DEFAULT '[]'"),
                ("ordenes_medicas", "estudios_detalle", "JSON DEFAULT '[]'"),
                ("obras_sociales", "copago_default", "NUMERIC(12, 2) DEFAULT 0.00"),
                ("obras_sociales", "porcentaje_cobertura_apb", "NUMERIC(5, 2) DEFAULT 0.00"),
                ("ordenes_medicas", "indicaciones_ids", "JSON DEFAULT '[]'"),
                ("ordenes_medicas", "indicaciones_texto", "TEXT"),
                ("ordenes_medicas", "mail_enviado", "BOOLEAN DEFAULT 0"),
                ("ordenes_medicas", "mail_enviado_fecha", "TIMESTAMP"),
                ("ordenes_medicas", "mail_enviado_por_id", "VARCHAR(36)"),
                ("ordenes_medicas", "mail_destinatario", "VARCHAR(255)"),
                ("ordenes_medicas", "mail_asunto", "VARCHAR(255)"),
                ("ordenes_medicas", "mail_cuerpo_html", "TEXT"),
                ("ordenes_medicas", "mail_message_id", "VARCHAR(150)"),
                ("ordenes_medicas", "mail_programado_para", "TIMESTAMP"),
                ("ordenes_medicas", "mail_auto_cancelado", "BOOLEAN DEFAULT 0"),
            ]
            for table, col, col_type in columns_to_add:
                try:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                    print(f"  + Columna agregada en SQLite: {table}.{col}")
                except Exception as e:
                    # Columna ya existe
                    pass

            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    clave VARCHAR(100) PRIMARY KEY,
                    valor VARCHAR(255) NOT NULL,
                    descripcion VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            row = (await conn.execute(text("SELECT clave FROM configuracion_sistema WHERE clave = 'VALOR_APB';"))).fetchone()
            if not row:
                await conn.execute(text("INSERT INTO configuracion_sistema (clave, valor, descripcion) VALUES ('VALOR_APB', '0.00', 'Valor vigente de referencia del Acto Profesional Bioquímico (APB)');"))
        else:
            # PostgreSQL
            postgres_statements = [
                "ALTER TABLE roles ADD COLUMN IF NOT EXISTS hierarchy_level INTEGER DEFAULT 10;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS nro_afiliado VARCHAR(50);",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS observacion_resultado_auditoria TEXT;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS debe_orden_medica BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS abona_apb BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS valor_apb NUMERIC(12, 2) DEFAULT 0.00;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS estudios_autorizados JSONB DEFAULT '[]';",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS estudios_no_autorizados JSONB DEFAULT '[]';",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS estudios_detalle JSONB DEFAULT '[]';",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS indicaciones_ids JSONB DEFAULT '[]';",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS indicaciones_texto TEXT;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_enviado BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_enviado_fecha TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_enviado_por_id UUID REFERENCES users(id) ON DELETE SET NULL;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_destinatario VARCHAR(255);",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_asunto VARCHAR(255);",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_cuerpo_html TEXT;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_message_id VARCHAR(150);",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_programado_para TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_auto_cancelado BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE obras_sociales ADD COLUMN IF NOT EXISTS copago_default NUMERIC(12, 2) DEFAULT 0.00;",
                "ALTER TABLE obras_sociales ADD COLUMN IF NOT EXISTS porcentaje_cobertura_apb NUMERIC(5, 2) DEFAULT 0.00;",
                """
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    clave VARCHAR(100) PRIMARY KEY,
                    valor VARCHAR(255) NOT NULL,
                    descripcion VARCHAR(255),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                INSERT INTO configuracion_sistema (clave, valor, descripcion)
                VALUES ('VALOR_APB', '0.00', 'Valor vigente de referencia del Acto Profesional Bioquímico (APB)')
                ON CONFLICT (clave) DO NOTHING;
                """,
                """
                INSERT INTO configuracion_sistema (clave, valor, descripcion)
                VALUES ('ENVIO_MAIL_AUTOMATICO', 'false', 'Indica si el envio de correos por auditoria finalizada es automatico (true) o manual (false)')
                ON CONFLICT (clave) DO NOTHING;
                """,
                """
                INSERT INTO configuracion_sistema (clave, valor, descripcion)
                VALUES ('MINUTOS_GRACIA_ENVIO_MAIL', '120', 'Minutos de espera programada antes del envio automatico del mail (permite cancelacion manual)')
                ON CONFLICT (clave) DO NOTHING;
                """,
            ]
            for stmt in postgres_statements:
                try:
                    await conn.execute(text(stmt))
                    print(f"  + Ejecutado en PostgreSQL: {stmt}")
                except Exception as e:
                    print(f"  - Aviso en PostgreSQL '{stmt}': {e}")
            # Agregar valores a los tipos Enum en Postgres si no existen
            for val in ["INFORMACION"]:
                try:
                    await conn.execute(text(f"ALTER TYPE estado_solicitud_enum ADD VALUE IF NOT EXISTS '{val}';"))
                except Exception:
                    pass
            for val in ["CONSULTA_PACIENTE", "SEGUIMIENTO_SUCURSAL", "OTRO"]:
                try:
                    await conn.execute(text(f"ALTER TYPE tipo_llamada_enum ADD VALUE IF NOT EXISTS '{val}';"))
                except Exception:
                    pass

    print(">>> Columnas creadas/verificadas correctamente.")

    print("\n=== 2. CONSULTANDO ÓRDENES EN BASE DE DATOS ===")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(OrdenMedica))
        ordenes = res.scalars().all()
        print(f">>> Total de órdenes encontradas en BD: {len(ordenes)}")
        for o in ordenes:
            print(f"- ID: {o.id} | Nro: {o.nro_orden} | Estado: {o.estado} | Paciente ID: {o.paciente_id} | Sucursal ID: {o.sucursal_id} | Mutual: {o.mutual} | Nro Afiliado: {o.nro_afiliado}")

if __name__ == "__main__":
    asyncio.run(fix_and_inspect())
