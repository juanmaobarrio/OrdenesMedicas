import asyncio
import sys
from loguru import logger
from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.modules.users.models import User
from backend.app.core.seed import seed_initial_data


async def update_admin_password(new_password: str):
    # Asegurar que el seed corrió primero
    await seed_initial_data()
    
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == "admin")
        user = (await db.execute(stmt)).scalar_one_or_none()
        if user:
            user.hashed_password = get_password_hash(new_password)
            await db.commit()
            logger.info(f"¡Contraseña del usuario 'admin' actualizada exitosamente a '{new_password}'!")
            print(f"OK: Contraseña de admin establecida a: {new_password}")
        else:
            logger.error("No se encontró el usuario 'admin' en la base de datos.")


if __name__ == "__main__":
    password = sys.argv[1] if len(sys.argv) > 1 else "6367Angelic"
    asyncio.run(update_admin_password(password))
