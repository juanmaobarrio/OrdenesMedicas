import asyncio
from loguru import logger
from sqlalchemy import text
from backend.app.core.database import engine, AsyncSessionLocal
from backend.app.modules.ordenes.models import OrdenMedica
from sqlalchemy import select

async def fix_and_inspect():
    print("=== 1. VERIFICANDO Y CREANDO COLUMNAS EN POSTGRESQL ===")
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS nro_afiliado VARCHAR(50);
            ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00;
            ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS observacion_resultado_auditoria TEXT;
            ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS debe_orden_medica BOOLEAN DEFAULT FALSE;
        """))
    print(">>> Columnas creadas/verificadas correctamente en PostgreSQL.")

    print("\n=== 2. CONSULTANDO ÓRDENES EN BASE DE DATOS ===")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(OrdenMedica))
        ordenes = res.scalars().all()
        print(f">>> Total de órdenes encontradas en BD: {len(ordenes)}")
        for o in ordenes:
            print(f"- ID: {o.id} | Nro: {o.nro_orden} | Estado: {o.estado} | Paciente ID: {o.paciente_id} | Sucursal ID: {o.sucursal_id} | Mutual: {o.mutual} | Nro Afiliado: {o.nro_afiliado}")

if __name__ == "__main__":
    asyncio.run(fix_and_inspect())
