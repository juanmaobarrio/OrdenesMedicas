import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
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






def sync_database_columns(connection):
    from sqlalchemy import text
    dialect = connection.dialect.name

    if dialect == "sqlite":
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
            if cols and "valor_apb" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN valor_apb NUMERIC(12, 2) DEFAULT 0.00"))
            if cols and "estudios_autorizados" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN estudios_autorizados JSON DEFAULT '[]'"))
            if cols and "estudios_no_autorizados" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN estudios_no_autorizados JSON DEFAULT '[]'"))
            if cols and "estudios_detalle" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN estudios_detalle JSON DEFAULT '[]'"))
            if cols and "indicaciones_ids" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN indicaciones_ids JSON DEFAULT '[]'"))
            if cols and "indicaciones_texto" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN indicaciones_texto TEXT"))
            if cols and "mail_enviado" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_enviado BOOLEAN DEFAULT 0"))
            if cols and "mail_enviado_fecha" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_enviado_fecha TIMESTAMP"))
            if cols and "mail_enviado_por_id" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_enviado_por_id VARCHAR(36)"))
            if cols and "mail_destinatario" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_destinatario VARCHAR(255)"))
            if cols and "mail_asunto" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_asunto VARCHAR(255)"))
            if cols and "mail_cuerpo_html" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_cuerpo_html TEXT"))
            if cols and "mail_message_id" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_message_id VARCHAR(150)"))
            if cols and "mail_programado_para" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_programado_para TIMESTAMP"))
            if cols and "mail_auto_cancelado" not in cols:
                connection.execute(text("ALTER TABLE ordenes_medicas ADD COLUMN mail_auto_cancelado BOOLEAN DEFAULT 0"))

            res_mut = connection.execute(text("PRAGMA table_info(obras_sociales)")).fetchall()
            cols_mut = [r[1] for r in res_mut]
            if cols_mut and "copago_default" not in cols_mut:
                connection.execute(text("ALTER TABLE obras_sociales ADD COLUMN copago_default NUMERIC(12, 2) DEFAULT 0.00"))
            if cols_mut and "porcentaje_cobertura_apb" not in cols_mut:
                connection.execute(text("ALTER TABLE obras_sociales ADD COLUMN porcentaje_cobertura_apb NUMERIC(5, 2) DEFAULT 0.00"))

            res_roles = connection.execute(text("PRAGMA table_info(roles)")).fetchall()
            cols_roles = [r[1] for r in res_roles]
            if cols_roles and "hierarchy_level" not in cols_roles:
                connection.execute(text("ALTER TABLE roles ADD COLUMN hierarchy_level INTEGER DEFAULT 10"))

            # Tabla de configuración general del sistema
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    clave VARCHAR(100) PRIMARY KEY,
                    valor VARCHAR(255) NOT NULL,
                    descripcion VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            row_apb = connection.execute(text("SELECT clave FROM configuracion_sistema WHERE clave = 'VALOR_APB'")).fetchone()
            if not row_apb:
                connection.execute(text("INSERT INTO configuracion_sistema (clave, valor, descripcion) VALUES ('VALOR_APB', '0.00', 'Valor vigente de referencia del Acto Profesional Bioquímico (APB)')"))

            feature_defaults = [
                ("FEATURE_MODULO_MAIL", "false", "Activa el módulo y despacho de correos electrónicos de resolución médica"),
                ("FEATURE_CALCULADORA_ESTUDIOS", "false", "Activa el botón y modal de calculadora interactiva de presupuestos"),
                ("FEATURE_ESTUDIOS_AUTORIZACION", "false", "Activa los campos clínicos de prácticas autorizadas y no autorizadas"),
                ("FEATURE_INDICACIONES_ESTUDIOS", "false", "Activa la asignación y catálogo de indicaciones clínicas de preparación"),
                ("FEATURE_ASIGNAR_AUDITOR", "false", "Activa la asignación de auditor médico a la orden médica"),
            ]
            for f_key, f_val, f_desc in feature_defaults:
                r_feat = connection.execute(text(f"SELECT clave FROM configuracion_sistema WHERE clave = '{f_key}'")).fetchone()
                if not r_feat:
                    connection.execute(text(f"INSERT INTO configuracion_sistema (clave, valor, descripcion) VALUES ('{f_key}', '{f_val}', '{f_desc}')"))
        except Exception as err:
            logger.warning(f"Error comprobando columnas SQLite: {err}")

    elif dialect == "postgresql":
        postgres_statements = [
            "ALTER TABLE roles ADD COLUMN IF NOT EXISTS hierarchy_level INTEGER DEFAULT 10",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS nro_afiliado VARCHAR(50)",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS valor_estudios_no_autorizados NUMERIC(12, 2) DEFAULT 0.00",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS observacion_resultado_auditoria TEXT",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS debe_orden_medica BOOLEAN DEFAULT FALSE",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS abona_apb BOOLEAN DEFAULT FALSE",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS valor_apb NUMERIC(12, 2) DEFAULT 0.00",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS estudios_autorizados JSONB DEFAULT '[]'",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS estudios_no_autorizados JSONB DEFAULT '[]'",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS estudios_detalle JSONB DEFAULT '[]'",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS indicaciones_ids JSONB DEFAULT '[]'",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS indicaciones_texto TEXT",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_enviado BOOLEAN DEFAULT FALSE",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_enviado_fecha TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_enviado_por_id UUID REFERENCES users(id) ON DELETE SET NULL",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_destinatario VARCHAR(255)",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_asunto VARCHAR(255)",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_cuerpo_html TEXT",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_message_id VARCHAR(150)",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_programado_para TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE ordenes_medicas ADD COLUMN IF NOT EXISTS mail_auto_cancelado BOOLEAN DEFAULT FALSE",
            "ALTER TABLE obras_sociales ADD COLUMN IF NOT EXISTS copago_default NUMERIC(12, 2) DEFAULT 0.00",
            "ALTER TABLE obras_sociales ADD COLUMN IF NOT EXISTS porcentaje_cobertura_apb NUMERIC(5, 2) DEFAULT 0.00",
            """
            CREATE TABLE IF NOT EXISTS configuracion_sistema (
                clave VARCHAR(100) PRIMARY KEY,
                valor VARCHAR(255) NOT NULL,
                descripcion VARCHAR(255),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('VALOR_APB', '0.00', 'Valor vigente de referencia del Acto Profesional Bioquímico (APB)')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('ENVIO_MAIL_AUTOMATICO', 'false', 'Indica si el envio de correos por auditoria finalizada es automatico (true) o manual (false)')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('MINUTOS_GRACIA_ENVIO_MAIL', '120', 'Minutos de espera programada antes del envio automatico del mail (permite cancelacion manual)')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('FEATURE_MODULO_MAIL', 'false', 'Activa el módulo y despacho de correos electrónicos de resolución médica')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('FEATURE_CALCULADORA_ESTUDIOS', 'false', 'Activa el botón y modal de calculadora interactiva de presupuestos')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('FEATURE_ESTUDIOS_AUTORIZACION', 'false', 'Activa los campos clínicos de prácticas autorizadas y no autorizadas')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('FEATURE_INDICACIONES_ESTUDIOS', 'false', 'Activa la asignación y catálogo de indicaciones clínicas de preparación')
            ON CONFLICT (clave) DO NOTHING
            """,
            """
            INSERT INTO configuracion_sistema (clave, valor, descripcion)
            VALUES ('FEATURE_ASIGNAR_AUDITOR', 'false', 'Activa la asignación de auditor médico a la orden médica')
            ON CONFLICT (clave) DO NOTHING
            """,
        ]
        for stmt in postgres_statements:
            try:
                connection.execute(text(stmt))
            except Exception as e:
                logger.warning(f"Aviso ejecutando '{stmt}': {e}")


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
            await conn.run_sync(sync_database_columns)
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



    # Manejo de errores de validación de Pydantic / FastAPI
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        messages = []
        for err in errors:
            loc = err.get("loc", [])
            field = str(loc[-1]) if loc else ""
            msg = err.get("msg", "")
            err_type = err.get("type", "")

            if field == "password" and ("string_too_short" in err_type or "at least" in msg or "characters" in msg):
                messages.append("La contraseña debe tener al menos 6 caracteres.")
            elif field == "email" and "value_error" in err_type:
                messages.append("El formato del correo electrónico ingresado no es válido.")
            elif field == "username" and "string_too_short" in err_type:
                messages.append("El nombre de usuario debe tener al menos 3 caracteres.")
            elif field == "documento" and "string_too_short" in err_type:
                messages.append("El número de documento debe tener al menos 4 caracteres.")
            elif "missing" in err_type:
                messages.append(f"El campo '{field}' es obligatorio.")
            else:
                messages.append(f"{field}: {msg}" if field else msg)

        formatted_detail = " ".join(messages) if messages else "Los datos enviados son inválidos."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": formatted_detail},
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
        logger.error(f"Error no controlado en {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Error interno del servidor: {str(exc)}"},
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

