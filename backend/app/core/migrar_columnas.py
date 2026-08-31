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
                ("obras_sociales", "copago_default", "NUMERIC(12, 2) DEFAULT 0.00"),
            ]
            for table, col, col_type in columns_to_add:
                try:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                    print(f"  + Columna agregada en SQLite: {table}.{col}")
                except Exception as e:
                    # Columna ya existe
                    pass
        else:
            # PostgreSQL
            await conn.execute(text("""
                ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS nro_afiliado VARCHAR(50);
                ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00;
                ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS observacion_resultado_auditoria TEXT;
                ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS debe_orden_medica BOOLEAN DEFAULT FALSE;
                ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS abona_apb BOOLEAN DEFAULT FALSE;
                ALTER TABLE obras_sociales ADD COLUMN IF NOT EXISTS copago_default NUMERIC(12, 2) DEFAULT 0.00;
            """))
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
