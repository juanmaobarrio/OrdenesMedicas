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
            ("users:manage", "users", "Administración total de usuarios y roles"),
            ("sucursales:manage", "sucursales", "Administración de sedes y sucursales"),
            ("pacientes:manage", "pacientes", "Gestión y edición del padrón de pacientes"),
            ("mutuales:manage", "mutuales", "Administración del catálogo de Obras Sociales y copagos"),
            ("ordenes:create", "ordenes", "Ingreso y registro de nuevas órdenes médicas"),
            ("ordenes:view", "ordenes", "Visualización y búsqueda de órdenes médicas"),
            ("ordenes:update", "ordenes", "Modificación de datos, cambio de estado y adjuntos"),
            ("ordenes:audit", "ordenes", "Auditoría médica, observaciones y resolución"),
            ("ordenes:calls", "ordenes", "Bandeja y registro de llamadas a pacientes"),
            ("ordenes:mail", "ordenes", "Previsualización y envío de correos electrónicos a pacientes"),
            ("dashboard:view", "dashboard", "Visualización de reportes, KPIs y exportación"),
            ("config:manage", "config", "Configuración de motivos de cancelación y estados"),
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
                "description": "Acceso absoluto a todos los módulos y configuraciones",
                "permissions": list(permission_map.values()),
                "hierarchy_level": 100,
                "is_system": True,
            },
            "AUDITOR": {
                "name": "Auditor Médico",
                "description": "Evaluación técnica, auditoría, observaciones, llamadas y gestión",
                "permissions": [
                    permission_map["ordenes:view"],
                    permission_map["ordenes:update"],
                    permission_map["ordenes:audit"],
                    permission_map["ordenes:calls"],
                    permission_map["ordenes:mail"],
                    permission_map["pacientes:manage"],
                    permission_map["dashboard:view"],
                    permission_map["mutuales:manage"],
                ],
                "hierarchy_level": 50,
                "is_system": True,
            },
            "USUARIO": {
                "name": "Operador de Sucursal",
                "description": "Admisión, carga de órdenes, adjuntos y atención a pacientes",
                "permissions": [
                    permission_map["pacientes:manage"],
                    permission_map["ordenes:create"],
                    permission_map["ordenes:view"],
                    permission_map["ordenes:update"],
                    permission_map["ordenes:calls"],
                ],
                "hierarchy_level": 10,
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
                    hierarchy_level=data["hierarchy_level"],
                    is_system=data["is_system"],
                    permissions=data["permissions"],
                )
                db.add(role)
                await db.flush()
                logger.info(f"Rol '{code}' creado.")
            else:
                # Asegurar que los roles base tengan los permisos y niveles actualizados
                if code == "ADMIN":
                    role.permissions = list(permission_map.values())
                    role.hierarchy_level = 100
                elif code == "AUDITOR":
                    role.permissions = data["permissions"]
                    role.hierarchy_level = 50
                elif code == "USUARIO":
                    role.permissions = data["permissions"]
                    role.hierarchy_level = 10
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

        # 8. Configuración General del Sistema (APB y Mail)
        from backend.app.modules.ordenes.models import ConfiguracionSistema, IndicacionEstudio, PlantillaEmail
        stmt_apb = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "VALOR_APB")
        apb_cfg = (await db.execute(stmt_apb)).scalar_one_or_none()
        if not apb_cfg:
            apb_cfg = ConfiguracionSistema(
                clave="VALOR_APB",
                valor="0.00",
                descripcion="Valor vigente de referencia del Acto Profesional Bioquímico (APB)",
            )
            db.add(apb_cfg)
            await db.flush()

        stmt_mail_auto = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "ENVIO_MAIL_AUTOMATICO")
        mail_auto_cfg = (await db.execute(stmt_mail_auto)).scalar_one_or_none()
        if not mail_auto_cfg:
            db.add(ConfiguracionSistema(
                clave="ENVIO_MAIL_AUTOMATICO",
                valor="false",
                descripcion="Indica si el envio de correos por auditoria finalizada es automatico (true) o manual (false)"
            ))

        stmt_gracia = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "MINUTOS_GRACIA_ENVIO_MAIL")
        gracia_cfg = (await db.execute(stmt_gracia)).scalar_one_or_none()
        if not gracia_cfg:
            db.add(ConfiguracionSistema(
                clave="MINUTOS_GRACIA_ENVIO_MAIL",
                valor="120",
                descripcion="Minutos de espera programada antes del envio automatico del mail"
            ))

        # 9. Indicaciones de preparación clínicas
        # Se inicia la tabla vacía para carga manual personalizada por el operador (sin precarga automática)

        # 10. Plantilla de Correo por Defecto
        from backend.app.core.templates_email import obtener_plantilla_base_html
        codigo_html_base = obtener_plantilla_base_html()

        stmt_tpl = select(PlantillaEmail).where(PlantillaEmail.codigo == "DEFAULT")
        tpl_existente = (await db.execute(stmt_tpl)).scalar_one_or_none()
        if not tpl_existente:
            db.add(PlantillaEmail(
                codigo="DEFAULT",
                nombre="Plantilla Estándar de Resolución Médica",
                asunto="Resolución de Auditoría Médica - Orden N° {{nro_orden}}",
                cuerpo_html=codigo_html_base,
                es_default=True,
                activa=True,
            ))
            await db.flush()
        else:
            # Si existía pero estaba vacía, inyectamos el código HTML base para que sea visible y editable
            if not tpl_existente.cuerpo_html or not tpl_existente.cuerpo_html.strip():
                tpl_existente.cuerpo_html = codigo_html_base
                await db.flush()

        # 11. Feature Flags del Sistema: Todas inactivas por defecto
        feature_defaults = [
            ("FEATURE_MODULO_MAIL", "false", "Activa el módulo y despacho de correos electrónicos de resolución médica"),
            ("FEATURE_CALCULADORA_ESTUDIOS", "false", "Activa el botón y modal de calculadora interactiva de presupuestos"),
            ("FEATURE_ESTUDIOS_AUTORIZACION", "false", "Activa los campos clínicos de prácticas autorizadas y no autorizadas"),
            ("FEATURE_INDICACIONES_ESTUDIOS", "false", "Activa la asignación y catálogo de indicaciones clínicas de preparación"),
            ("FEATURE_ASIGNAR_AUDITOR", "false", "Activa la asignación de auditor médico a la orden médica"),
        ]
        for f_key, f_val, f_desc in feature_defaults:
            stmt_f = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == f_key)
            if not (await db.execute(stmt_f)).scalar_one_or_none():
                db.add(ConfiguracionSistema(clave=f_key, valor=f_val, descripcion=f_desc))

        await db.commit()
        logger.info("Siembra de datos finalizada con exito.")



if __name__ == "__main__":
    asyncio.run(seed_initial_data())
