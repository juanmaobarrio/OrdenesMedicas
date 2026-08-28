import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.app.core.config import settings
from backend.app.core.exceptions import AppException
from backend.app.core.logging import setup_logging
from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.dashboard.router import router as dashboard_router
from backend.app.modules.ordenes.router import config_router, router as ordenes_router
from backend.app.modules.pacientes.router import mutuales_router, router as pacientes_router
from backend.app.modules.users.router import router as users_router






def sync_sqlite_columns(connection):
    from sqlalchemy import text
    try:
        res = connection.execute(text("PRAGMA table_info(ordenes_medicas)")).fetchall()
        cols = [r[1] for r in res]
        if cols and "observacion_resultado_auditoria" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN observacion_resultado_auditoria TEXT"))
        if cols and "valor_estudios_no_autorizados" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00"))
        if cols and "debe_orden_medica" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN debe_orden_medica BOOLEAN DEFAULT 0"))

        res_roles = connection.execute(text("PRAGMA table_info(roles)")).fetchall()
        cols_roles = [r[1] for r in res_roles]
        if cols_roles and "hierarchy_level" not in cols_roles:
            connection.execute(text("ALTER TABLE roles ADD COLUMN hierarchy_level INTEGER DEFAULT 10"))
    except Exception as err:
        logger.warning(f"Error comprobando columnas SQLite: {err}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicacion (Startup y Shutdown)."""
    logger.info(f"Iniciando {settings.PROJECT_NAME} en modo {settings.ENVIRONMENT}...")
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        from backend.app.core.database import engine
        from backend.app.shared.base_model import Base
        import backend.app.modules.users.models  # noqa
        import backend.app.modules.pacientes.models  # noqa
        import backend.app.modules.ordenes.models  # noqa
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(sync_sqlite_columns)
        from backend.app.core.seed import seed_initial_data
        await seed_initial_data()
    except Exception as e:
        logger.warning(f"Inicializacion de base de datos: {e}")
    yield
    logger.info(f"Apagando {settings.PROJECT_NAME}...")



def create_application() -> FastAPI:
    """Fabrica de creacion y configuracion de la aplicacion FastAPI."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configuracion de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )



    # Manejo global de excepciones personalizadas
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    # Manejo global de excepciones no controladas
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Error no controlado: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor. Por favor contacte al administrador."},
        )

    # Endpoint de verificacion de salud (Health check)
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
        }

    # Registro de routers por modulo
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(users_router, prefix=settings.API_V1_STR)
    app.include_router(pacientes_router, prefix=settings.API_V1_STR)
    app.include_router(mutuales_router, prefix=settings.API_V1_STR)
    app.include_router(ordenes_router, prefix=settings.API_V1_STR)
    app.include_router(config_router, prefix=settings.API_V1_STR)
    app.include_router(dashboard_router, prefix=settings.API_V1_STR)




    return app


app = create_application()

