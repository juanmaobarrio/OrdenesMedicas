import asyncio
import uuid
from loguru import logger
from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.modules.pacientes.models import ObraSocial
from backend.app.modules.users.models import Permission, Role, Sucursal, User



async def seed_initial_data():
    """Siembra roles base, permisos del sistema, sucursal inicial y usuario administrador."""
    from backend.app.core.database import engine
    from backend.app.shared.base_model import Base
    import backend.app.modules.users.models  # noqa
    import backend.app.modules.pacientes.models  # noqa
    import backend.app.modules.ordenes.models  # noqa

    # Asegurar que todas las tablas y esquemas existan en PostgreSQL / SQLite
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        logger.info("Iniciando siembra de datos iniciales (Seed)...")

        # 1. Sucursal Inicial
        stmt_sucursal = select(Sucursal).where(Sucursal.codigo == "CENTRAL")
        sucursal = (await db.execute(stmt_sucursal)).scalar_one_or_none()
        if not sucursal:
            sucursal = Sucursal(
                nombre="Sede Central",
                codigo="CENTRAL",
                activa=True,
            )
            db.add(sucursal)
            await db.flush()
            logger.info("Sucursal 'Sede Central' creada.")

        # 2. Permisos del Sistema
        default_permissions = [
            ("users:manage", "users", "Administracion total de usuarios y roles"),
            ("sucursales:manage", "sucursales", "Administracion de sucursales"),
            ("pacientes:manage", "pacientes", "Gestion y edicion de pacientes"),
            ("ordenes:create", "ordenes", "Ingreso y carga de ordenes medicas"),
            ("ordenes:view", "ordenes", "Visualizacion y busqueda de ordenes"),
            ("ordenes:update", "ordenes", "Actualizacion y respuesta de ordenes"),
            ("ordenes:audit", "ordenes", "Auditoria medica, observaciones y aprobacion"),
            ("ordenes:calls", "ordenes", "Gestion de llamadas y aviso a pacientes"),
            ("dashboard:view", "dashboard", "Visualizacion de reportes y KPIs"),
        ]

        permission_map = {}
        for code, module, desc in default_permissions:
            stmt = select(Permission).where(Permission.code == code)
            perm = (await db.execute(stmt)).scalar_one_or_none()
            if not perm:
                perm = Permission(code=code, module=module, description=desc)
                db.add(perm)
                await db.flush()
            permission_map[code] = perm

        # 3. Roles del Sistema
        roles_config = {
            "ADMIN": {
                "name": "Administrador General",
                "description": "Acceso absoluto al sistema y configuraciones",
                "permissions": list(permission_map.values()),
                "is_system": True,
            },
            "AUDITOR": {
                "name": "Auditor",
                "description": "Evaluacion tecnica, solicitudes de cambio y aprobacion medica",
                "permissions": [
                    permission_map["ordenes:view"],
                    permission_map["ordenes:audit"],
                    permission_map["dashboard:view"],
                ],
                "is_system": True,
            },
            "USUARIO": {
                "name": "Operador de Sucursal",
                "description": "Admision, carga de ordenes, adjuntos y atencion telefonica al paciente",
                "permissions": [
                    permission_map["pacientes:manage"],
                    permission_map["ordenes:create"],
                    permission_map["ordenes:view"],
                    permission_map["ordenes:update"],
                    permission_map["ordenes:calls"],
                ],
                "is_system": True,
            },
        }

        role_map = {}
        for code, data in roles_config.items():
            stmt = select(Role).where(Role.code == code)
            role = (await db.execute(stmt)).scalar_one_or_none()
            if not role:
                role = Role(
                    code=code,
                    name=data["name"],
                    description=data["description"],
                    is_system=data["is_system"],
                    permissions=data["permissions"],
                )
                db.add(role)
                await db.flush()
                logger.info(f"Rol '{code}' creado.")
            else:
                if role.name != data["name"]:
                    role.name = data["name"]
                    await db.flush()
            role_map[code] = role

        # 4. Usuario Administrador por Defecto
        stmt_admin = select(User).where(User.username == "admin")
        admin_user = (await db.execute(stmt_admin)).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@auditoriasmedicas.local",
                hashed_password=get_password_hash("admin123456"),
                first_name="Administrador",
                last_name="General",
                is_active=True,
                is_superuser=True,
                role_id=role_map["ADMIN"].id,
                sucursal_id=sucursal.id,
            )
            db.add(admin_user)
            await db.flush()
            logger.info("Usuario inicial 'admin' creado exitosamente con credenciales por defecto.")

        # 5. Obras Sociales y Mutuales por Defecto
        default_mutuales = [
            ("OSDE", "OSDE", "OSDE Organizacion de Servicios Directos Empresarios", "EXT-OSDE", 30),
            ("SM", "SWISS MEDICAL", "Swiss Medical Medicina Privada", "EXT-SM", 30),
            ("PAMI", "PAMI", "INSSJP - Instituto Nacional de Servicios Sociales", "EXT-PAMI", 60),
            ("IOMA", "IOMA", "Instituto de Obra Medico Asistencial", "EXT-IOMA", 30),
            ("GALENO", "GALENO", "Galeno Argentina S.A.", "EXT-GALENO", 30),
            ("MEDICUS", "MEDICUS", "Medicus Medicina Prepaga", "EXT-MEDICUS", 30),
            ("OMINT", "OMINT", "Omint de Servicios de Salud", "EXT-OMINT", 30),
            ("OSECAC", "OSECAC", "Obra Social de Empleados de Comercio", "EXT-OSECAC", 30),
            ("PARTICULAR", "PARTICULAR", "Atencion Particular / Sin Cobertura", None, 365),
        ]

        for cod, sigla, nom, cod_ext, dias in default_mutuales:
            stmt_m = select(ObraSocial).where(ObraSocial.codigo == cod)
            mut = (await db.execute(stmt_m)).scalar_one_or_none()
            if not mut:
                mut = ObraSocial(
                    codigo=cod,
                    sigla=sigla,
                    nombre=nom,
                    codigo_externo=cod_ext,
                    dias_vencimiento=dias,
                    activa=True,
                )
                db.add(mut)
                await db.flush()

        # 6. Motivos de Cancelacion por Defecto
        from backend.app.modules.ordenes.models import EstadoOrdenConfig, MotivoCancelacion, TipoEstadoOrden
        default_motivos = [
            ("ORDEN_VENCIDA", "Orden Vencida", "La prescripción médica superó el plazo máximo de validez"),
            ("NO_CUMPLE_CONDICIONES", "Orden que no cumple las condiciones", "Falta documentación requerida o requisitos legales de la mutual"),
            ("PACIENTE_NO_ACEPTO", "El paciente no aceptó el resultado", "El paciente desiste del estudio por copago o condiciones de auditoría"),
        ]

        for cod_mot, nom_mot, desc_mot in default_motivos:
            stmt_mot = select(MotivoCancelacion).where(MotivoCancelacion.codigo == cod_mot)
            mot_obj = (await db.execute(stmt_mot)).scalar_one_or_none()
            if not mot_obj:
                mot_obj = MotivoCancelacion(
                    codigo=cod_mot,
                    nombre=nom_mot,
                    descripcion=desc_mot,
                    activo=True,
                )
                db.add(mot_obj)
                await db.flush()

        # 7. Estados de Orden Configurables por Defecto (con IDs 1 a 8 para integraciones API / n8n)
        default_estados = [
            (1, "INGRESO", "Ingreso", "Orden ingresada en sede esperando evaluación", TipoEstadoOrden.PROCESO, False, "info", "pi pi-inbox", 1),
            (2, "EN_AUDITORIA", "en Auditoria", "Auditor evaluando prescripción médica", TipoEstadoOrden.PROCESO, False, "warn", "pi pi-search", 2),
            (3, "SOLICITUDES_AUDITORIA", "Solicitudes de auditoria", "Observación o requerimiento médico emitido", TipoEstadoOrden.PROCESO, False, "danger", "pi pi-exclamation-circle", 3),
            (4, "ACTUALIZADA", "Actualizada", "Documentación adicional adjuntada por sucursal", TipoEstadoOrden.PROCESO, False, "contrast", "pi pi-refresh", 4),
            (5, "AUDITORIA_FINALIZADA", "Auditoria Finalizada", "Auditoría aprobada; requiere aviso al paciente", TipoEstadoOrden.PROCESO, False, "info", "pi pi-phone", 5),
            (6, "DAR_DE_BAJA", "Dar de baja", "Baja administrativa previa a toma de muestra", TipoEstadoOrden.FINALIZACION, True, "secondary", "pi pi-ban", 6),
            (7, "CANCELADA", "Cancelada", "Orden rechazada o anulada formalmente", TipoEstadoOrden.FINALIZACION, True, "danger", "pi pi-times-circle", 7),
            (8, "CERRADA", "Cerrada", "Resolución exitosa: Paciente atendido", TipoEstadoOrden.FINALIZACION, False, "success", "pi pi-check-circle", 8),
        ]

        for est_id, est_cod, est_nom, est_desc, est_tipo, est_req_mot, est_badge, est_ico, est_seq in default_estados:
            stmt_est = select(EstadoOrdenConfig).where(EstadoOrdenConfig.codigo == est_cod)
            est_obj = (await db.execute(stmt_est)).scalar_one_or_none()
            if not est_obj:
                est_obj = EstadoOrdenConfig(
                    id=est_id,
                    codigo=est_cod,
                    nombre=est_nom,
                    descripcion=est_desc,
                    tipo=est_tipo,
                    requiere_motivo=est_req_mot,
                    color_badge=est_badge,
                    icono=est_ico,
                    es_sistema=True,
                    activo=True,
                    orden_secuencia=est_seq,
                )
                db.add(est_obj)
                await db.flush()

        await db.commit()
        logger.info("Siembra de datos finalizada con exito.")



if __name__ == "__main__":
    asyncio.run(seed_initial_data())
