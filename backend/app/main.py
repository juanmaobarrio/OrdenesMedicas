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
        # SQLite migrations
        res = connection.execute(text("PRAGMA table_info(ordenes_medicas)")).fetchall()
        cols = [r[1] for r in res]
        if cols and "nro_afiliado" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN nro_afiliado VARCHAR(50)"))
        if cols and "observacion_resultado_auditoria" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN observacion_resultado_auditoria TEXT"))
        if cols and "valor_estudios_no_autorizados" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00"))
        if cols and "debe_orden_medica" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN debe_orden_medica BOOLEAN DEFAULT 0"))
        if cols and "abona_apb" not in cols:
            connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN abona_apb BOOLEAN DEFAULT 0"))

        res_mut = connection.execute(text("PRAGMA table_info(obras_sociales)")).fetchall()
        cols_mut = [r[1] for r in res_mut]
        if cols_mut and "copago_default" not in cols_mut:
            connection.execute(text("ALTER TABLE obras_sociales ADD COLUMN copago_default NUMERIC(12, 2) DEFAULT 0.00"))

        res_roles = connection.execute(text("PRAGMA table_info(roles)")).fetchall()
        cols_roles = [r[1] for r in res_roles]
        if cols_roles and "hierarchy_level" not in cols_roles:
            connection.execute(text("ALTER TABLE roles ADD COLUMN hierarchy_level INTEGER DEFAULT 10"))
    except Exception as err:
        logger.warning(f"Error comprobando columnas SQLite: {err}")

    try:
        # PostgreSQL migrations (si la columna no existe)
        connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='roles' AND column_name='hierarchy_level'
                ) THEN
                    ALTER TABLE roles ADD COLUMN hierarchy_level INTEGER DEFAULT 10;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='ordenes_medicas' AND column_name='nro_afiliado'
                ) THEN
                    ALTER TABLE ordenes_medicas ADD COLUMN nro_afiliado VARCHAR(50);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='ordenes_medicas' AND column_name='valor_estudios_no_autorizados'
                ) THEN
                    ALTER TABLE ordenes_medicas ADD COLUMN valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='ordenes_medicas' AND column_name='observacion_resultado_auditoria'
                ) THEN
                    ALTER TABLE ordenes_medicas ADD COLUMN observacion_resultado_auditoria TEXT;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='ordenes_medicas' AND column_name='debe_orden_medica'
                ) THEN
                    ALTER TABLE ordenes_medicas ADD COLUMN debe_orden_medica BOOLEAN DEFAULT FALSE;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='ordenes_medicas' AND column_name='abona_apb'
                ) THEN
                    ALTER TABLE ordenes_medicas ADD COLUMN abona_apb BOOLEAN DEFAULT FALSE;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='obras_sociales' AND column_name='copago_default'
                ) THEN
                    ALTER TABLE obras_sociales ADD COLUMN copago_default NUMERIC(12, 2) DEFAULT 0.00;
                END IF;
            END $$;
        """))
        for val in ["INFORMACION"]:
            try:
                connection.execute(text(f"ALTER TYPE estado_solicitud_enum ADD VALUE IF NOT EXISTS '{val}';"))
            except Exception:
                pass
        for val in ["CONSULTA_PACIENTE", "SEGUIMIENTO_SUCURSAL", "OTRO"]:
            try:
                connection.execute(text(f"ALTER TYPE tipo_llamada_enum ADD VALUE IF NOT EXISTS '{val}';"))
            except Exception:
                pass
    except Exception:
        pass


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



OPENAPI_TAGS = [
    {
        "name": "Autenticacion",
        "description": "Emisión y refresco de tokens de seguridad JWT (OAuth2 Bearer), perfil de usuario activo y cierre de sesión.",
    },
    {
        "name": "Ordenes Medicas",
        "description": "Ciclo de vida completo de prescripciones médicas, montos totales (copago + no autorizados), nro de afiliado, números de auditoría, adjuntos fotográficos/PDF y trazabilidad inmutable.",
    },
    {
        "name": "Auditoria Medica",
        "description": "Panel de evaluación clínica para auditores médicos, emisión de observaciones/requerimientos y respuestas operativas de sucursales.",
    },
    {
        "name": "Pacientes",
        "description": "Padrón centralizado de afiliados, historial clínico, búsqueda rápida para autocompletado y vinculación de Obras Sociales.",
    },
    {
        "name": "Obras Sociales / Mutuales",
        "description": "Catálogo de prestadores médicos, cálculo dinámico de días de vencimiento de prescripciones y códigos de integración.",
    },
    {
        "name": "Dashboard & Reportes",
        "description": "Métricas clave (KPIs), flujo diario de órdenes, distribución por sucursal y exportación tabular CSV para Microsoft Excel.",
    },
    {
        "name": "Usuarios y Roles (RBAC)",
        "description": "Gestión de operadores, auditores y administradores, control de jerarquía de roles (`hierarchy_level`) y asignación granular de permisos.",
    },
    {
        "name": "Configuracion de Estados y Motivos",
        "description": "Catálogo administrable de motivos de cancelación y estados del sistema con ID numérico para integraciones API / n8n.",
    },
    {
        "name": "Health",
        "description": "Monitoreo de estado operativo y verificación de salud de la plataforma.",
    },
]

API_DESCRIPTION = """
### 🏥 API REST - Sistema Integral de Gestión de Órdenes Médicas
Plataforma moderna, resiliente y de alta disponibilidad para la administración, auditoría médica, bitácora de trazabilidad legal y seguimiento de prescripciones clínicas.

#### 🛡️ Autenticación y Seguridad:
* Utiliza autenticación **OAuth2 Bearer Token (JWT)** en el header `Authorization: Bearer <token>`.
* Inicie sesión en `/api/v1/auth/login` con su usuario o correo electrónico para obtener el Access Token.

#### 🔄 Estados del Ciclo de Vida de las Órdenes:
1. `Ingreso` (1): Orden recibida en sede esperando revisión.
2. `en Auditoria` (2): Auditor médico evaluando la prescripción o código de auditoría asignado.
3. `Solicitudes de auditoria` (3): Observación clínica emitida; genera llamada pendiente al paciente.
4. `Actualizada` (4): Documentación adicional incorporada por la sucursal.
5. `Auditoria Finalizada` (5): Aprobación médica completada; genera llamada de aviso al paciente.
6. `Dar de baja` (6): Anulación administrativa antes de toma de muestra.
7. `Cancelada` (7): Rechazo formal con motivo obligatorio del catálogo.
8. `Cerrada` (8): Resolución exitosa; paciente atendido.
"""


def create_application() -> FastAPI:
    """Fabrica de creacion y configuracion de la aplicacion FastAPI."""
    app = FastAPI(
        title="Sistema de Gestión de Órdenes Médicas API",
        description=API_DESCRIPTION,
        version="1.3.0",
        openapi_tags=OPENAPI_TAGS,
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

