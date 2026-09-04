import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from backend.app.core.exceptions import (
    AppException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    ForbiddenActionException,
)
from backend.app.modules.ordenes.models import (
    AdjuntoOrden,
    AuditoriaLog,
    AuditoriaSolicitud,
    ConfiguracionSistema,
    EstadoOrden,
    EstadoOrdenConfig,
    EstadoSolicitudAuditoria,
    IndicacionEstudio,
    MotivoCancelacion,
    OrdenMedica,
    PlantillaEmail,
    RegistroLlamadaPaciente,
    ResultadoLlamada,
    TipoEstadoOrden,
    TipoLlamadaPaciente,
)
from backend.app.modules.ordenes.repository import (
    EstadoOrdenConfigRepository,
    MotivoCancelacionRepository,
    OrdenMedicaRepository,
)
from backend.app.modules.ordenes.schemas import (
    AuditoriaSolicitudCreate,
    AuditoriaSolicitudResponder,
    ConfiguracionAPBRead,
    ConfiguracionAPBUpdate,
    ConfiguracionMailAutomatizacionRead,
    ConfiguracionMailAutomatizacionUpdate,
    EnviarEmailResolucionRequest,
    EstadoOrdenConfigCreate,
    EstadoOrdenConfigUpdate,
    IndicacionEstudioCreate,
    IndicacionEstudioRead,
    IndicacionEstudioUpdate,
    MotivoCancelacionCreate,
    MotivoCancelacionUpdate,
    OrdenLlamadaPendienteItem,
    OrdenMedicaAsignarAuditor,
    OrdenMedicaCambioEstado,
    OrdenMedicaCreate,
    OrdenMedicaUpdate,
    PlantillaEmailCreate,
    PlantillaEmailRead,
    PlantillaEmailUpdate,
    PreviewEmailResolucionRead,
    RegistroLlamadaCreate,
    SystemFeaturesConfig,
    SystemFeaturesConfigUpdate,
)

from backend.app.modules.pacientes.repository import PacienteRepository
from backend.app.modules.users.models import User
from backend.app.modules.users.repository import SucursalRepository, UserRepository


def _enum_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    return v.value if hasattr(v, "value") else str(v)


def _sincronizar_estudios_y_totales(
    estudios_detalle: Optional[List[Any]],
    estudios_autorizados: Optional[List[str]],
    estudios_no_autorizados: Optional[List[str]],
    valor_estudios_no_autorizados: Optional[Decimal],
):
    """
    Sincroniza y autocalcula listas de nombres y monto de no autorizados
    a partir del desglose JSON de estudios_detalle si se proporciona.
    """
    detalle_dicts = None
    if estudios_detalle is not None:
        detalle_dicts = []
        for e in estudios_detalle:
            if hasattr(e, "model_dump"):
                d = e.model_dump(mode="json")
            elif isinstance(e, dict):
                d = dict(e)
            else:
                d = {"nombre": str(e), "precio": 0.0, "autorizado": True}
            d["nombre"] = str(d.get("nombre") or "").strip()
            d["codigo"] = str(d.get("codigo") or "").strip() if d.get("codigo") else None
            try:
                d["precio"] = float(d.get("precio") or 0.0)
            except (ValueError, TypeError):
                d["precio"] = 0.0
            d["autorizado"] = bool(d.get("autorizado", True))
            detalle_dicts.append(d)

        # Si no se proveyeron listas explícitas de nombres, derivarlas automáticamente
        if estudios_autorizados is None or len(estudios_autorizados) == 0:
            estudios_autorizados = [
                d["nombre"] for d in detalle_dicts if d["autorizado"] and d["nombre"]
            ]
        if estudios_no_autorizados is None or len(estudios_no_autorizados) == 0:
            estudios_no_autorizados = [
                d["nombre"] for d in detalle_dicts if not d["autorizado"] and d["nombre"]
            ]
        # Si no se pasó un valor específico o es 0, sumar precios de no autorizados
        if valor_estudios_no_autorizados is None or valor_estudios_no_autorizados == Decimal("0.00"):
            suma_no_aut = Decimal(str(sum(d["precio"] for d in detalle_dicts if not d["autorizado"])))
            if suma_no_aut > Decimal("0.00") or valor_estudios_no_autorizados is None:
                valor_estudios_no_autorizados = suma_no_aut

    return detalle_dicts, estudios_autorizados, estudios_no_autorizados, valor_estudios_no_autorizados


class OrdenMedicaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrdenMedicaRepository(db)
        self.paciente_repo = PacienteRepository(db)
        self.sucursal_repo = SucursalRepository(db)
        self.user_repo = UserRepository(db)

    async def get_by_id(self, orden_id: uuid.UUID) -> OrdenMedica:
        orden = await self.repo.get_by_id(orden_id)
        if not orden:
            raise EntityNotFoundException("Orden Medica", orden_id)
        return orden

    async def list_ordenes(
        self,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[EstadoOrden] = None,
        sucursal_id: Optional[uuid.UUID] = None,
        paciente_id: Optional[uuid.UUID] = None,
        auditor_id: Optional[uuid.UUID] = None,
        mutual: Optional[str] = None,
        search: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Tuple[Sequence[OrdenMedica], int]:
        return await self.repo.list_paginated(
            skip=skip,
            limit=limit,
            estado=estado,
            sucursal_id=sucursal_id,
            paciente_id=paciente_id,
            auditor_id=auditor_id,
            mutual=mutual,
            search=search,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

    async def create_orden(
        self,
        dto: OrdenMedicaCreate,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrdenMedica:
        # Validar existencia de paciente
        paciente = await self.paciente_repo.get_by_id(dto.paciente_id)
        if not paciente:
            raise EntityNotFoundException("Paciente", dto.paciente_id)

        # Validar existencia de sucursal
        sucursal = await self.sucursal_repo.get_by_id(dto.sucursal_id)
        if not sucursal:
            raise EntityNotFoundException("Sucursal", dto.sucursal_id)

        # Generar numero correlativo unico
        nro_orden = await self.repo.generate_next_nro_orden()

        (
            detalle_dicts,
            estudios_aut,
            estudios_no_aut,
            valor_no_aut,
        ) = _sincronizar_estudios_y_totales(
            estudios_detalle=dto.estudios_detalle,
            estudios_autorizados=dto.estudios_autorizados,
            estudios_no_autorizados=dto.estudios_no_autorizados,
            valor_estudios_no_autorizados=dto.valor_estudios_no_autorizados,
        )

        orden = OrdenMedica(
            nro_orden=nro_orden,
            paciente_id=dto.paciente_id,
            sucursal_id=dto.sucursal_id,
            created_by_user_id=current_user.id,
            estado=EstadoOrden.INGRESO,
            fecha_prescripcion=dto.fecha_prescripcion,
            cantidad_ordenes_fisicas=dto.cantidad_ordenes_fisicas,
            mutual=dto.mutual.strip().upper(),
            nro_afiliado=dto.nro_afiliado.strip() if dto.nro_afiliado else None,
            valor_copago=dto.valor_copago,
            valor_estudios_no_autorizados=valor_no_aut or Decimal("0.00"),
            abona_apb=dto.abona_apb,
            valor_apb=dto.valor_apb if dto.abona_apb else Decimal("0.00"),
            fecha_vencimiento=dto.fecha_vencimiento,
            numeros_auditoria=dto.numeros_auditoria,
            estudios_autorizados=estudios_aut or [],
            estudios_no_autorizados=estudios_no_aut or [],
            estudios_detalle=detalle_dicts or [],
            debe_orden_medica=dto.debe_orden_medica,

            contacto_nombre=dto.contacto_nombre.strip() if dto.contacto_nombre else None,
            contacto_horario=dto.contacto_horario.strip() if dto.contacto_horario else None,
            contacto_telefono=dto.contacto_telefono.strip() if dto.contacto_telefono else None,
            contacto_celular=dto.contacto_celular.strip() if dto.contacto_celular else None,
            contacto_email=dto.contacto_email.strip().lower() if dto.contacto_email else None,
            observaciones_ingreso=dto.observaciones_ingreso,
        )

        created_orden = await self.repo.create(orden)

        # Registrar log inmutable de auditoria
        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=created_orden.id,
                user_id=current_user.id,
                accion="CREACION_ORDEN",
                estado_anterior=None,
                estado_nuevo=EstadoOrden.INGRESO.value,
                detalles={
                    "nro_orden": nro_orden,
                    "paciente": paciente.nombre_completo,
                    "documento": paciente.documento,
                    "sucursal": sucursal.nombre,
                    "mutual": dto.mutual,
                    "copago": str(dto.valor_copago),
                    "apb": str(dto.valor_apb if dto.abona_apb else Decimal("0.00")),
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        return await self.get_by_id(created_orden.id)

    async def update_orden(
        self,
        orden_id: uuid.UUID,
        dto: OrdenMedicaUpdate,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrdenMedica:
        orden = await self.get_by_id(orden_id)

        # Bloquear modificaciones si la orden ya esta cerrada, cancelada o dada de baja
        if _enum_str(orden.estado) in [EstadoOrden.CANCELADA.value, EstadoOrden.DAR_DE_BAJA.value, EstadoOrden.CERRADA.value]:
            raise ForbiddenActionException(
                f"No se puede modificar una orden en estado final '{_enum_str(orden.estado)}'"
            )

        # Validar nivel jerárquico para modificar cantidad de recetas o sede de ingreso (requiere jerarquía > 30)
        user_hierarchy = 100 if current_user.is_superuser else (current_user.role.hierarchy_level if current_user.role else 10)
        if user_hierarchy <= 30:
            if dto.cantidad_ordenes_fisicas is not None and dto.cantidad_ordenes_fisicas != orden.cantidad_ordenes_fisicas:
                raise ForbiddenActionException(
                    "Se requiere un nivel jerárquico superior a 30 (Auditor o Administrador) para modificar la cantidad de recetas de la orden."
                )
            if dto.sucursal_id is not None and dto.sucursal_id != orden.sucursal_id:
                raise ForbiddenActionException(
                    "Se requiere un nivel jerárquico superior a 30 (Auditor o Administrador) para modificar la sede de ingreso de la orden."
                )

        diff = {}
        if dto.fecha_prescripcion is not None:
            diff["fecha_prescripcion"] = str(dto.fecha_prescripcion)
            orden.fecha_prescripcion = dto.fecha_prescripcion

        if dto.cantidad_ordenes_fisicas is not None and dto.cantidad_ordenes_fisicas != orden.cantidad_ordenes_fisicas:
            diff["cantidad_ordenes_fisicas"] = dto.cantidad_ordenes_fisicas
            orden.cantidad_ordenes_fisicas = dto.cantidad_ordenes_fisicas

        if dto.sucursal_id is not None and dto.sucursal_id != orden.sucursal_id:
            sucursal = await self.sucursal_repo.get_by_id(dto.sucursal_id)
            if not sucursal:
                raise EntityNotFoundException("Sucursal", dto.sucursal_id)
            diff["sucursal"] = sucursal.nombre
            orden.sucursal_id = dto.sucursal_id

        if dto.mutual is not None:
            diff["mutual"] = dto.mutual.strip().upper()
            orden.mutual = dto.mutual.strip().upper()

        if dto.nro_afiliado is not None:
            diff["nro_afiliado"] = dto.nro_afiliado.strip() if dto.nro_afiliado else None
            orden.nro_afiliado = dto.nro_afiliado.strip() if dto.nro_afiliado else None

        if dto.valor_copago is not None:
            diff["valor_copago"] = str(dto.valor_copago)
            orden.valor_copago = dto.valor_copago

        if dto.valor_estudios_no_autorizados is not None:
            diff["valor_estudios_no_autorizados"] = str(dto.valor_estudios_no_autorizados)
            orden.valor_estudios_no_autorizados = dto.valor_estudios_no_autorizados

        if dto.abona_apb is not None:
            diff["abona_apb"] = dto.abona_apb
            orden.abona_apb = dto.abona_apb

        if dto.valor_apb is not None:
            diff["valor_apb"] = str(dto.valor_apb)
            orden.valor_apb = dto.valor_apb

        if dto.fecha_vencimiento is not None:
            diff["fecha_vencimiento"] = str(dto.fecha_vencimiento)
            orden.fecha_vencimiento = dto.fecha_vencimiento

        if dto.numeros_auditoria is not None:
            diff["numeros_auditoria"] = dto.numeros_auditoria
            orden.numeros_auditoria = dto.numeros_auditoria
            # Si se agrega número de auditoría y estaba en Ingreso, pasa automáticamente a 'en Auditoria'
            if len(dto.numeros_auditoria) > 0 and orden.estado == EstadoOrden.INGRESO:
                orden.estado = EstadoOrden.EN_AUDITORIA
                diff["autotransicion_estado"] = EstadoOrden.EN_AUDITORIA.value

        if dto.estudios_detalle is not None:
            (
                detalle_dicts,
                estudios_aut,
                estudios_no_aut,
                valor_no_aut,
            ) = _sincronizar_estudios_y_totales(
                estudios_detalle=dto.estudios_detalle,
                estudios_autorizados=dto.estudios_autorizados,
                estudios_no_autorizados=dto.estudios_no_autorizados,
                valor_estudios_no_autorizados=dto.valor_estudios_no_autorizados,
            )
            orden.estudios_detalle = detalle_dicts or []
            diff["estudios_detalle"] = detalle_dicts or []
            if estudios_aut is not None:
                orden.estudios_autorizados = estudios_aut
                diff["estudios_autorizados"] = estudios_aut
            if estudios_no_aut is not None:
                orden.estudios_no_autorizados = estudios_no_aut
                diff["estudios_no_autorizados"] = estudios_no_aut
            if valor_no_aut is not None:
                orden.valor_estudios_no_autorizados = valor_no_aut
                diff["valor_estudios_no_autorizados"] = str(valor_no_aut)
        else:
            if dto.estudios_autorizados is not None:
                diff["estudios_autorizados"] = dto.estudios_autorizados
                orden.estudios_autorizados = dto.estudios_autorizados
            if dto.estudios_no_autorizados is not None:
                diff["estudios_no_autorizados"] = dto.estudios_no_autorizados
                orden.estudios_no_autorizados = dto.estudios_no_autorizados


        if dto.contacto_nombre is not None:
            orden.contacto_nombre = dto.contacto_nombre.strip()

        if dto.contacto_horario is not None:
            orden.contacto_horario = dto.contacto_horario.strip()

        if dto.contacto_telefono is not None:
            orden.contacto_telefono = dto.contacto_telefono.strip()

        if dto.contacto_celular is not None:
            orden.contacto_celular = dto.contacto_celular.strip()

        if dto.contacto_email is not None:
            orden.contacto_email = dto.contacto_email.strip().lower()

        if dto.observaciones_ingreso is not None:
            orden.observaciones_ingreso = dto.observaciones_ingreso

        if dto.debe_orden_medica is not None:
            diff["debe_orden_medica"] = dto.debe_orden_medica
            orden.debe_orden_medica = dto.debe_orden_medica

        await self.db.flush()

        # Registrar en la bitacora de auditoria
        if diff:
            await self.repo.create_audit_log(
                AuditoriaLog(
                    orden_id=orden.id,
                    user_id=current_user.id,
                    accion="ACTUALIZACION_DATOS",
                    estado_anterior=orden.estado.value,
                    estado_nuevo=orden.estado.value,
                    detalles=diff,
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            )

        return await self.get_by_id(orden_id)

    async def cambiar_estado(
        self,
        orden_id: uuid.UUID,
        dto: OrdenMedicaCambioEstado,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrdenMedica:
        orden = await self.get_by_id(orden_id)
        estado_anterior = orden.estado

        # Determinar el estado destino por estado_id numerico o por string
        target_estado: Optional[EstadoOrden] = None
        estado_cfg: Optional[EstadoOrdenConfig] = None
        estado_cfg_repo = EstadoOrdenConfigRepository(self.db)

        if dto.estado_id is not None:
            estado_cfg = await estado_cfg_repo.get_by_id(dto.estado_id)
            if not estado_cfg:
                raise EntityNotFoundException("Estado de orden con ID", dto.estado_id)
            for e in EstadoOrden:
                if e.value.lower() == estado_cfg.nombre.lower() or e.name.lower() == estado_cfg.codigo.lower():
                    target_estado = e
                    break
        elif dto.nuevo_estado:
            for e in EstadoOrden:
                if e.value.lower() == dto.nuevo_estado.strip().lower() or e.name.lower() == dto.nuevo_estado.strip().lower():
                    target_estado = e
                    break
            if not target_estado:
                estado_cfg = await estado_cfg_repo.get_by_codigo(dto.nuevo_estado) or await estado_cfg_repo.get_by_nombre(dto.nuevo_estado)

        if not target_estado and not estado_cfg:
            raise AppException(status_code=400, detail="Debe especificar un estado_id o nuevo_estado valido")

        # Asignar Enum si existe, o usar el estado por defecto
        final_estado_enum = target_estado or EstadoOrden.INGRESO

        # Comprobar requerimiento de motivo (si es cancelacion, baja o si la configuracion lo exige)
        requiere_motivo = (
            final_estado_enum in (EstadoOrden.CANCELADA, EstadoOrden.DAR_DE_BAJA)
            or (estado_cfg and estado_cfg.requiere_motivo)
            or (estado_cfg and estado_cfg.tipo == TipoEstadoOrden.FINALIZACION and final_estado_enum != EstadoOrden.CERRADA)
        )

        if requiere_motivo and not dto.motivo:
            raise AppException(status_code=400, detail="Debe indicar el motivo del cambio de estado")

        if final_estado_enum in (EstadoOrden.CANCELADA, EstadoOrden.DAR_DE_BAJA):
            orden.motivo_cancelacion = dto.motivo

        # Si pasa a 'Auditoria Finalizada', registrar observacion de resultado y habilitar llamada
        if final_estado_enum == EstadoOrden.AUDITORIA_FINALIZADA:
            if dto.observacion_resultado:
                orden.observacion_resultado_auditoria = dto.observacion_resultado
            elif dto.motivo:
                orden.observacion_resultado_auditoria = dto.motivo
            orden.llamada_finalizada_completada = False

            # Programar envío automático de mail si está configurado
            try:
                stmt_mail_cfg = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "ENVIO_MAIL_AUTOMATICO")
                res_mail_cfg = await self.db.execute(stmt_mail_cfg)
                cfg_obj = res_mail_cfg.scalar_one_or_none()
                is_auto = cfg_obj and cfg_obj.valor.strip().lower() == "true"

                if is_auto and not orden.mail_enviado:
                    stmt_gracia = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "MINUTOS_GRACIA_ENVIO_MAIL")
                    res_gracia = await self.db.execute(stmt_gracia)
                    gracia_obj = res_gracia.scalar_one_or_none()
                    minutos = int(gracia_obj.valor) if gracia_obj and gracia_obj.valor.isdigit() else 120
                    from datetime import timezone, timedelta
                    orden.mail_programado_para = datetime.now(timezone.utc) + timedelta(minutes=minutos)
                    orden.mail_auto_cancelado = False
            except Exception as e:
                logger.warning(f"Error comprobando programacion automatica de mail: {e}")

        # Si se modificó copago o no autorizados al cambiar estado (ej: al finalizar auditoría)
        if dto.valor_copago is not None:
            orden.valor_copago = dto.valor_copago
        if dto.valor_estudios_no_autorizados is not None:
            orden.valor_estudios_no_autorizados = dto.valor_estudios_no_autorizados
        if dto.valor_apb is not None:
            orden.valor_apb = dto.valor_apb
        if getattr(dto, "estudios_detalle", None) is not None:
            (
                detalle_dicts,
                estudios_aut,
                estudios_no_aut,
                valor_no_aut,
            ) = _sincronizar_estudios_y_totales(
                estudios_detalle=dto.estudios_detalle,
                estudios_autorizados=dto.estudios_autorizados,
                estudios_no_autorizados=dto.estudios_no_autorizados,
                valor_estudios_no_autorizados=dto.valor_estudios_no_autorizados,
            )
            orden.estudios_detalle = detalle_dicts or []
            if estudios_aut is not None:
                orden.estudios_autorizados = estudios_aut
            if estudios_no_aut is not None:
                orden.estudios_no_autorizados = estudios_no_aut
            if valor_no_aut is not None:
                orden.valor_estudios_no_autorizados = valor_no_aut
        else:
            if dto.estudios_autorizados is not None:
                orden.estudios_autorizados = dto.estudios_autorizados
            if dto.estudios_no_autorizados is not None:
                orden.estudios_no_autorizados = dto.estudios_no_autorizados

        # Si pasa a 'Solicitudes de auditoria', habilitar llamada
        if final_estado_enum == EstadoOrden.SOLICITUDES_AUDITORIA:
            orden.llamada_solicitud_completada = False

        orden.estado = final_estado_enum

        await self.db.flush()

        # Log de transicion de estado
        detalles_log = {}
        if dto.motivo:
            detalles_log["motivo"] = dto.motivo
        if dto.observacion_resultado:
            detalles_log["observacion_resultado"] = dto.observacion_resultado
        if dto.valor_copago is not None:
            detalles_log["valor_copago"] = str(dto.valor_copago)
        if dto.valor_estudios_no_autorizados is not None:
            detalles_log["valor_estudios_no_autorizados"] = str(dto.valor_estudios_no_autorizados)
        if dto.valor_apb is not None:
            detalles_log["valor_apb"] = str(dto.valor_apb)
        if dto.motivo_cancelacion_id:
            detalles_log["motivo_cancelacion_id"] = str(dto.motivo_cancelacion_id)
        if dto.estado_id:
            detalles_log["estado_id"] = dto.estado_id

        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="CAMBIO_ESTADO",
                estado_anterior=estado_anterior.value,
                estado_nuevo=final_estado_enum.value,
                detalles=detalles_log,
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        return await self.get_by_id(orden_id)

    async def asignar_auditor(
        self,
        orden_id: uuid.UUID,
        dto: OrdenMedicaAsignarAuditor,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrdenMedica:
        orden = await self.get_by_id(orden_id)
        estado_anterior = orden.estado

        if dto.auditor_id:
            auditor = await self.user_repo.get_by_id(dto.auditor_id)
            if not auditor:
                raise EntityNotFoundException("Auditor", dto.auditor_id)
            orden.assigned_auditor_id = dto.auditor_id

            # Si la orden estaba en Ingreso, transiciona a en Auditoria
            if orden.estado == EstadoOrden.INGRESO:
                orden.estado = EstadoOrden.EN_AUDITORIA
        else:
            orden.assigned_auditor_id = None

        await self.db.flush()

        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="ASIGNAR_AUDITOR",
                estado_anterior=estado_anterior.value,
                estado_nuevo=orden.estado.value,
                detalles={"auditor_id": str(dto.auditor_id) if dto.auditor_id else None},
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        return await self.get_by_id(orden_id)

    async def agregar_solicitud_auditoria(
        self,
        orden_id: uuid.UUID,
        dto: AuditoriaSolicitudCreate,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditoriaSolicitud:
        orden = await self.get_by_id(orden_id)
        estado_anterior = orden.estado

        es_info = bool(dto.es_informativa)
        estado_sol = EstadoSolicitudAuditoria.INFORMACION if es_info else EstadoSolicitudAuditoria.PENDIENTE

        solicitud = AuditoriaSolicitud(
            orden_id=orden_id,
            auditor_id=current_user.id,
            motivo_solicitud=dto.motivo_solicitud.strip(),
            mensaje_auditor=dto.mensaje_auditor.strip(),
            estado=estado_sol,
        )
        created_solicitud = await self.repo.create_solicitud(solicitud)

        if not es_info:
            # Transicionar orden a Solicitudes de auditoria y marcar llamada pendiente
            orden.estado = EstadoOrden.SOLICITUDES_AUDITORIA
            orden.llamada_solicitud_completada = False
            await self.db.flush()

            await self.repo.create_audit_log(
                AuditoriaLog(
                    orden_id=orden.id,
                    user_id=current_user.id,
                    accion="NUEVA_SOLICITUD_AUDITORIA",
                    estado_anterior=estado_anterior.value,
                    estado_nuevo=EstadoOrden.SOLICITUDES_AUDITORIA.value,
                    detalles={
                        "solicitud_id": str(created_solicitud.id),
                        "motivo": dto.motivo_solicitud,
                        "mensaje": dto.mensaje_auditor,
                        "es_informativa": False,
                    },
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            )
        else:
            # Es solo informativa: NO altera estado ni genera llamada pendiente
            await self.db.flush()
            await self.repo.create_audit_log(
                AuditoriaLog(
                    orden_id=orden.id,
                    user_id=current_user.id,
                    accion="NUEVA_OBSERVACION_INFORMATIVA",
                    estado_anterior=estado_anterior.value,
                    estado_nuevo=estado_anterior.value,
                    detalles={
                        "solicitud_id": str(created_solicitud.id),
                        "motivo": dto.motivo_solicitud,
                        "mensaje": dto.mensaje_auditor,
                        "es_informativa": True,
                    },
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            )

        return (await self.repo.get_solicitud_by_id(created_solicitud.id)) or created_solicitud

    async def responder_solicitud_auditoria(
        self,
        solicitud_id: uuid.UUID,
        dto: AuditoriaSolicitudResponder,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditoriaSolicitud:
        solicitud = await self.repo.get_solicitud_by_id(solicitud_id)
        if not solicitud:
            raise EntityNotFoundException("Solicitud de auditoria", solicitud_id)

        orden = await self.get_by_id(solicitud.orden_id)
        estado_anterior = orden.estado

        solicitud.respuesta_operador = dto.respuesta_operador.strip()
        solicitud.respondido_por_id = current_user.id
        solicitud.fecha_respuesta = datetime.now(timezone.utc)
        solicitud.estado = EstadoSolicitudAuditoria.RESPONDIDA

        # Pasar estado de orden a Actualizada
        orden.estado = EstadoOrden.ACTUALIZADA
        await self.db.flush()

        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="RESPUESTA_SOLICITUD_AUDITORIA",
                estado_anterior=estado_anterior.value,
                estado_nuevo=EstadoOrden.ACTUALIZADA.value,
                detalles={
                    "solicitud_id": str(solicitud.id),
                    "respuesta": dto.respuesta_operador,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        return (await self.repo.get_solicitud_by_id(solicitud.id)) or solicitud

    async def registrar_adjunto(
        self,
        orden_id: uuid.UUID,
        nombre_original: str,
        nombre_almacenado: str,
        ruta_almacenamiento: str,
        tipo_mime: str,
        tamano_bytes: int,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdjuntoOrden:
        orden = await self.get_by_id(orden_id)

        adjunto = AdjuntoOrden(
            orden_id=orden_id,
            subido_por_id=current_user.id,
            nombre_archivo_original=nombre_original,
            nombre_archivo_almacenado=nombre_almacenado,
            ruta_almacenamiento=ruta_almacenamiento,
            tipo_mime=tipo_mime,
            tamano_bytes=tamano_bytes,
        )
        created_adjunto = await self.repo.create_adjunto(adjunto)

        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="SUBIDA_ADJUNTO",
                estado_anterior=orden.estado.value,
                estado_nuevo=orden.estado.value,
                detalles={
                    "adjunto_id": str(created_adjunto.id),
                    "nombre_archivo": nombre_original,
                    "tamano_bytes": tamano_bytes,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        return created_adjunto

    async def eliminar_adjunto(
        self,
        adjunto_id: uuid.UUID,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        adjunto = await self.repo.get_adjunto_by_id(adjunto_id)
        if not adjunto:
            raise EntityNotFoundException("Adjunto", adjunto_id)

        orden = await self.get_by_id(adjunto.orden_id)

        # Validar si la orden está en estado terminal
        if orden.estado in [EstadoOrden.CANCELADA, EstadoOrden.DAR_DE_BAJA, EstadoOrden.CERRADA]:
            raise ForbiddenActionException(
                f"No se pueden eliminar adjuntos de una orden en estado final '{orden.estado.value}'"
            )

        # Borrar archivo físico del disco si existe
        if os.path.exists(adjunto.ruta_almacenamiento):
            try:
                os.remove(adjunto.ruta_almacenamiento)
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo físico {adjunto.ruta_almacenamiento}: {e}")

        # Registrar log inmutable de auditoría antes de borrar el registro
        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="ELIMINACION_ADJUNTO",
                estado_anterior=orden.estado.value,
                estado_nuevo=orden.estado.value,
                detalles={
                    "adjunto_id": str(adjunto.id),
                    "nombre_archivo": adjunto.nombre_archivo_original,
                    "tamano_bytes": adjunto.tamano_bytes,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        await self.repo.delete_adjunto(adjunto)

    async def registrar_llamada_paciente(
        self,
        orden_id: uuid.UUID,
        dto: RegistroLlamadaCreate,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RegistroLlamadaPaciente:
        orden = await self.get_by_id(orden_id)

        # Crear registro de intento/llamada
        registro = RegistroLlamadaPaciente(
            orden_id=orden.id,
            user_id=current_user.id,
            tipo_llamada=dto.tipo_llamada,
            resultado=dto.resultado,
            observaciones=dto.observaciones.strip() if dto.observaciones else None,
        )
        created_registro = await self.repo.create_registro_llamada(registro)

        # Si la comunicacion fue exitosa, marcar la bandera correspondiente sin alterar el estado de la orden
        comunicacion_exitosa = dto.resultado == ResultadoLlamada.EXITOSA
        now = datetime.now(timezone.utc)

        if comunicacion_exitosa:
            if dto.tipo_llamada == TipoLlamadaPaciente.SOLICITUD_AUDITORIA:
                orden.llamada_solicitud_completada = True
                orden.llamada_solicitud_fecha = now
                orden.llamada_solicitud_observacion = dto.observaciones
            elif dto.tipo_llamada == TipoLlamadaPaciente.AUDITORIA_FINALIZADA:
                orden.llamada_finalizada_completada = True
                orden.llamada_finalizada_fecha = now
                orden.llamada_finalizada_observacion = dto.observaciones

            # Si el operador marcó completar aviso pendiente (o si el paciente llamó y se resolvió el aviso)
            if dto.completar_aviso_pendiente:
                if not orden.llamada_solicitud_completada:
                    orden.llamada_solicitud_completada = True
                    orden.llamada_solicitud_fecha = now
                    orden.llamada_solicitud_observacion = dto.observaciones
                if not orden.llamada_finalizada_completada and orden.estado == EstadoOrden.AUDITORIA_FINALIZADA:
                    orden.llamada_finalizada_completada = True
                    orden.llamada_finalizada_fecha = now
                    orden.llamada_finalizada_observacion = dto.observaciones

        await self.db.flush()

        # Auditoria
        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="REGISTRO_LLAMADA_PACIENTE",
                estado_anterior=_enum_str(orden.estado),
                estado_nuevo=_enum_str(orden.estado),
                detalles={
                    "tipo_llamada": _enum_str(dto.tipo_llamada),
                    "resultado": _enum_str(dto.resultado),
                    "exitoso": comunicacion_exitosa,
                    "observaciones": dto.observaciones,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        return created_registro

    async def obtener_llamadas_pendientes(
        self, sucursal_id: Optional[uuid.UUID] = None
    ) -> Sequence[OrdenLlamadaPendienteItem]:
        ordenes = await self.repo.list_ordenes_con_llamadas_pendientes(sucursal_id=sucursal_id)

        items: List[OrdenLlamadaPendienteItem] = []
        for o in ordenes:
            # Filtrar solicitudes pendientes para el operador
            sols_pendientes = [
                s for s in (o.solicitudes or [])
                if s.estado == EstadoSolicitudAuditoria.PENDIENTE
            ]

            # Determinar tipo de llamada pendiente
            if (
                o.estado == EstadoOrden.SOLICITUDES_AUDITORIA
                and not o.llamada_solicitud_completada
            ):
                tipo = TipoLlamadaPaciente.SOLICITUD_AUDITORIA
                ult_solicitud = o.solicitudes[0] if o.solicitudes else None
                motivo = (
                    f"Observación del auditor: {ult_solicitud.motivo_solicitud}"
                    if ult_solicitud
                    else "Requiere documentación adicional de auditoría"
                )
            elif (
                o.estado == EstadoOrden.AUDITORIA_FINALIZADA
                and not o.llamada_finalizada_completada
            ):
                tipo = TipoLlamadaPaciente.AUDITORIA_FINALIZADA
                motivo = (
                    f"Auditoría Finalizada: {o.observacion_resultado_auditoria}"
                    if o.observacion_resultado_auditoria
                    else "Avisar que la orden médica ha sido aprobada y finalizada para toma de muestra"
                )
            else:
                continue

            # Cantidad de llamadas previas para este tipo
            intentos = len([l for l in o.llamadas_registro if l.tipo_llamada == tipo])

            item = OrdenLlamadaPendienteItem(
                id=o.id,
                nro_orden=o.nro_orden,
                estado=o.estado,
                tipo_llamada_requerida=tipo,
                motivo_aviso=motivo,
                fecha_estado=o.updated_at,
                paciente_nombre=o.paciente.nombre_completo,
                paciente_documento=o.paciente.documento,
                paciente_telefono=o.paciente.telefono,
                contacto_nombre=o.contacto_nombre,
                contacto_horario=o.contacto_horario,
                contacto_telefono=o.contacto_telefono,
                contacto_celular=o.contacto_celular,
                contacto_email=o.contacto_email,
                sucursal_nombre=o.sucursal.nombre,
                mutual=o.mutual,
                observaciones_ingreso=o.observaciones_ingreso,
                observacion_resultado_auditoria=o.observacion_resultado_auditoria,
                debe_orden_medica=o.debe_orden_medica,
                cant_intentos_previos=intentos,
                solicitudes_pendientes=sols_pendientes,
            )
            items.append(item)

        return items


class MotivoCancelacionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotivoCancelacionRepository(db)

    async def list_motivos(self, only_active: bool = True) -> Sequence[MotivoCancelacion]:
        return await self.repo.list_all(only_active=only_active)

    async def get_by_id(self, motivo_id: uuid.UUID) -> MotivoCancelacion:
        motivo = await self.repo.get_by_id(motivo_id)
        if not motivo:
            raise EntityNotFoundException("Motivo de Cancelación", motivo_id)
        return motivo

    async def create_motivo(self, dto: MotivoCancelacionCreate) -> MotivoCancelacion:
        existing_cod = await self.repo.get_by_codigo(dto.codigo)
        if existing_cod:
            raise EntityAlreadyExistsException("Motivo de Cancelación", "codigo", dto.codigo)
        existing_nom = await self.repo.get_by_nombre(dto.nombre)
        if existing_nom:
            raise EntityAlreadyExistsException("Motivo de Cancelación", "nombre", dto.nombre)

        motivo = MotivoCancelacion(
            codigo=dto.codigo.strip().upper(),
            nombre=dto.nombre.strip(),
            descripcion=dto.descripcion.strip() if dto.descripcion else None,
            activo=dto.activo,
        )
        return await self.repo.create(motivo)

    async def update_motivo(self, motivo_id: uuid.UUID, dto: MotivoCancelacionUpdate) -> MotivoCancelacion:
        motivo = await self.get_by_id(motivo_id)
        data = {}
        if dto.nombre is not None:
            existing_nom = await self.repo.get_by_nombre(dto.nombre)
            if existing_nom and existing_nom.id != motivo_id:
                raise EntityAlreadyExistsException("Motivo de Cancelación", "nombre", dto.nombre)
            data["nombre"] = dto.nombre.strip()
        if dto.descripcion is not None:
            data["descripcion"] = dto.descripcion.strip() if dto.descripcion else None
        if dto.activo is not None:
            data["activo"] = dto.activo

        return await self.repo.update(motivo, data)

    async def toggle_active(self, motivo_id: uuid.UUID) -> MotivoCancelacion:
        motivo = await self.get_by_id(motivo_id)
        return await self.repo.update(motivo, {"activo": not motivo.activo})

    async def delete_motivo(self, motivo_id: uuid.UUID) -> None:
        motivo = await self.get_by_id(motivo_id)
        await self.repo.delete(motivo)


class EstadoOrdenConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EstadoOrdenConfigRepository(db)

    async def list_estados(self, only_active: bool = False) -> Sequence[EstadoOrdenConfig]:
        return await self.repo.list_all(only_active=only_active)

    async def get_by_id(self, estado_id: int) -> EstadoOrdenConfig:
        estado = await self.repo.get_by_id(estado_id)
        if not estado:
            raise EntityNotFoundException("Estado de Orden con ID", estado_id)
        return estado

    async def create_estado(self, dto: EstadoOrdenConfigCreate) -> EstadoOrdenConfig:
        existing_cod = await self.repo.get_by_codigo(dto.codigo)
        if existing_cod:
            raise EntityAlreadyExistsException("Estado de Orden", "codigo", dto.codigo)
        existing_nom = await self.repo.get_by_nombre(dto.nombre)
        if existing_nom:
            raise EntityAlreadyExistsException("Estado de Orden", "nombre", dto.nombre)

        estado = EstadoOrdenConfig(
            codigo=dto.codigo.strip().upper(),
            nombre=dto.nombre.strip(),
            descripcion=dto.descripcion.strip() if dto.descripcion else None,
            tipo=dto.tipo,
            requiere_motivo=dto.requiere_motivo,
            color_badge=dto.color_badge,
            icono=dto.icono,
            es_sistema=False,
            activo=dto.activo,
            orden_secuencia=dto.orden_secuencia,
        )
        return await self.repo.create(estado)

    async def update_estado(self, estado_id: int, dto: EstadoOrdenConfigUpdate) -> EstadoOrdenConfig:
        estado = await self.get_by_id(estado_id)
        data = {}
        if dto.nombre is not None:
            existing_nom = await self.repo.get_by_nombre(dto.nombre)
            if existing_nom and existing_nom.id != estado_id:
                raise EntityAlreadyExistsException("Estado de Orden", "nombre", dto.nombre)
            data["nombre"] = dto.nombre.strip()
        if dto.descripcion is not None:
            data["descripcion"] = dto.descripcion.strip() if dto.descripcion else None
        if dto.tipo is not None:
            data["tipo"] = dto.tipo
        if dto.requiere_motivo is not None:
            data["requiere_motivo"] = dto.requiere_motivo
        if dto.color_badge is not None:
            data["color_badge"] = dto.color_badge
        if dto.icono is not None:
            data["icono"] = dto.icono
        if dto.activo is not None:
            data["activo"] = dto.activo
        if dto.orden_secuencia is not None:
            data["orden_secuencia"] = dto.orden_secuencia

        return await self.repo.update(estado, data)

    async def toggle_active(self, estado_id: int) -> EstadoOrdenConfig:
        estado = await self.get_by_id(estado_id)
        return await self.repo.update(estado, {"activo": not estado.activo})

    async def delete_estado(self, estado_id: int) -> None:
        estado = await self.get_by_id(estado_id)
        if estado.es_sistema:
            raise ForbiddenActionException("No se pueden eliminar estados base del sistema")
        await self.repo.delete(estado)


class ConfiguracionSistemaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config_apb(self) -> ConfiguracionAPBRead:
        stmt = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "VALOR_APB")
        res = await self.db.execute(stmt)
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = ConfiguracionSistema(
                clave="VALOR_APB",
                valor="0.00",
                descripcion="Valor vigente de referencia del Acto Profesional Bioquímico (APB)",
            )
            self.db.add(cfg)
            await self.db.commit()
            await self.db.refresh(cfg)
        try:
            val = Decimal(cfg.valor)
        except Exception:
            val = Decimal("0.00")
        return ConfiguracionAPBRead(
            valor_apb=val,
            descripcion=cfg.descripcion,
            updated_at=cfg.updated_at,
        )

    async def update_valor_apb(self, dto: ConfiguracionAPBUpdate) -> ConfiguracionAPBRead:
        stmt = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "VALOR_APB")
        res = await self.db.execute(stmt)
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = ConfiguracionSistema(
                clave="VALOR_APB",
                valor=str(dto.valor_apb),
                descripcion="Valor vigente de referencia del Acto Profesional Bioquímico (APB)",
            )
            self.db.add(cfg)
        else:
            cfg.valor = str(dto.valor_apb)
        await self.db.commit()
        await self.db.refresh(cfg)
        return ConfiguracionAPBRead(
            valor_apb=Decimal(cfg.valor),
            descripcion=cfg.descripcion,
            updated_at=cfg.updated_at,
        )

    FEATURE_KEYS = {
        "modulo_mail": ("FEATURE_MODULO_MAIL", "Activa el módulo y despacho de correos electrónicos de resolución médica"),
        "calculadora_estudios": ("FEATURE_CALCULADORA_ESTUDIOS", "Activa el botón y modal de calculadora interactiva de presupuestos"),
        "estudios_autorizacion": ("FEATURE_ESTUDIOS_AUTORIZACION", "Activa los campos clínicos de prácticas autorizadas y no autorizadas"),
        "indicaciones_estudios": ("FEATURE_INDICACIONES_ESTUDIOS", "Activa la asignación y catálogo de indicaciones clínicas de preparación"),
        "asignar_auditor": ("FEATURE_ASIGNAR_AUDITOR", "Activa la asignación de auditor médico a la orden médica"),
    }

    async def get_features(self) -> SystemFeaturesConfig:
        stmt = select(ConfiguracionSistema).where(
            ConfiguracionSistema.clave.in_([k[0] for k in self.FEATURE_KEYS.values()])
        )
        res = await self.db.execute(stmt)
        rows = {r.clave: r.valor.lower() in ["true", "1", "yes", "si"] for r in res.scalars().all()}

        return SystemFeaturesConfig(
            modulo_mail=rows.get(self.FEATURE_KEYS["modulo_mail"][0], False),
            calculadora_estudios=rows.get(self.FEATURE_KEYS["calculadora_estudios"][0], False),
            estudios_autorizacion=rows.get(self.FEATURE_KEYS["estudios_autorizacion"][0], False),
            indicaciones_estudios=rows.get(self.FEATURE_KEYS["indicaciones_estudios"][0], False),
            asignar_auditor=rows.get(self.FEATURE_KEYS["asignar_auditor"][0], False),
        )

    async def update_features(self, dto: SystemFeaturesConfigUpdate) -> SystemFeaturesConfig:
        for attr, (db_key, desc) in self.FEATURE_KEYS.items():
            val = getattr(dto, attr, None)
            if val is not None:
                stmt = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == db_key)
                res = await self.db.execute(stmt)
                cfg = res.scalar_one_or_none()
                if not cfg:
                    cfg = ConfiguracionSistema(
                        clave=db_key,
                        valor="true" if val else "false",
                        descripcion=desc,
                    )
                    self.db.add(cfg)
                else:
                    cfg.valor = "true" if val else "false"
        await self.db.commit()
        return await self.get_features()






class IndicacionEstudioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_indicaciones(self, only_active: bool = False) -> List[IndicacionEstudio]:
        stmt = select(IndicacionEstudio).order_by(IndicacionEstudio.orden_secuencia.asc(), IndicacionEstudio.titulo.asc())
        if only_active:
            stmt = stmt.where(IndicacionEstudio.activa == True)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, indicacion_id: uuid.UUID) -> IndicacionEstudio:
        stmt = select(IndicacionEstudio).where(IndicacionEstudio.id == indicacion_id)
        res = await self.db.execute(stmt)
        ind = res.scalar_one_or_none()
        if not ind:
            raise EntityNotFoundException("IndicacionEstudio", indicacion_id)
        return ind

    async def create_indicacion(self, dto: IndicacionEstudioCreate) -> IndicacionEstudio:
        cod = dto.codigo.strip().upper()
        stmt = select(IndicacionEstudio).where(IndicacionEstudio.codigo == cod)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise EntityAlreadyExistsException("IndicacionEstudio", "codigo", cod)

        ind = IndicacionEstudio(
            codigo=cod,
            titulo=dto.titulo.strip(),
            instrucciones=dto.instrucciones.strip(),
            categoria=dto.categoria.strip() if dto.categoria else None,
            color=dto.color.strip() if dto.color else "info",
            orden_secuencia=dto.orden_secuencia,
            activa=dto.activa,
        )
        self.db.add(ind)
        await self.db.commit()
        await self.db.refresh(ind)
        return ind

    async def update_indicacion(self, indicacion_id: uuid.UUID, dto: IndicacionEstudioUpdate) -> IndicacionEstudio:
        ind = await self.get_by_id(indicacion_id)
        if dto.codigo is not None:
            cod = dto.codigo.strip().upper()
            if cod != ind.codigo:
                stmt = select(IndicacionEstudio).where(IndicacionEstudio.codigo == cod)
                res = await self.db.execute(stmt)
                if res.scalar_one_or_none():
                    raise EntityAlreadyExistsException("IndicacionEstudio", "codigo", cod)
                ind.codigo = cod
        if dto.titulo is not None:
            ind.titulo = dto.titulo.strip()
        if dto.instrucciones is not None:
            ind.instrucciones = dto.instrucciones.strip()
        if dto.categoria is not None:
            ind.categoria = dto.categoria.strip() if dto.categoria else None
        if dto.color is not None:
            ind.color = dto.color.strip()
        if dto.orden_secuencia is not None:
            ind.orden_secuencia = dto.orden_secuencia
        if dto.activa is not None:
            ind.activa = dto.activa

        await self.db.commit()
        await self.db.refresh(ind)
        return ind

    async def delete_indicacion(self, indicacion_id: uuid.UUID) -> None:
        ind = await self.get_by_id(indicacion_id)
        await self.db.delete(ind)
        await self.db.commit()


class EmailResolucionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config_automatizacion(self) -> ConfiguracionMailAutomatizacionRead:
        stmt_auto = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "ENVIO_MAIL_AUTOMATICO")
        res_auto = await self.db.execute(stmt_auto)
        cfg_auto = res_auto.scalar_one_or_none()
        envio_auto = (cfg_auto.valor.strip().lower() == "true") if cfg_auto else False

        stmt_gracia = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "MINUTOS_GRACIA_ENVIO_MAIL")
        res_gracia = await self.db.execute(stmt_gracia)
        cfg_gracia = res_gracia.scalar_one_or_none()
        minutos = int(cfg_gracia.valor) if cfg_gracia and cfg_gracia.valor.isdigit() else 120

        from backend.app.core.zeptomail import zepto_mail_service
        return ConfiguracionMailAutomatizacionRead(
            envio_automatico=envio_auto,
            minutos_gracia=minutos,
            zeptomail_configurado=zepto_mail_service.is_configured,
            remitente_email=zepto_mail_service.from_email,
            remitente_nombre=zepto_mail_service.from_name,
        )

    async def update_config_automatizacion(self, dto: ConfiguracionMailAutomatizacionUpdate) -> ConfiguracionMailAutomatizacionRead:
        stmt_auto = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "ENVIO_MAIL_AUTOMATICO")
        res_auto = await self.db.execute(stmt_auto)
        cfg_auto = res_auto.scalar_one_or_none()
        val_auto_str = "true" if dto.envio_automatico else "false"
        if not cfg_auto:
            self.db.add(ConfiguracionSistema(clave="ENVIO_MAIL_AUTOMATICO", valor=val_auto_str, descripcion="Envio automatico de emails"))
        else:
            cfg_auto.valor = val_auto_str

        stmt_gracia = select(ConfiguracionSistema).where(ConfiguracionSistema.clave == "MINUTOS_GRACIA_ENVIO_MAIL")
        res_gracia = await self.db.execute(stmt_gracia)
        cfg_gracia = res_gracia.scalar_one_or_none()
        val_gracia_str = str(dto.minutos_gracia)
        if not cfg_gracia:
            self.db.add(ConfiguracionSistema(clave="MINUTOS_GRACIA_ENVIO_MAIL", valor=val_gracia_str, descripcion="Minutos de gracia"))
        else:
            cfg_gracia.valor = val_gracia_str

        await self.db.commit()
        return await self.get_config_automatizacion()

    async def build_preview_email(self, orden_id: uuid.UUID) -> PreviewEmailResolucionRead:
        stmt = (
            select(OrdenMedica)
            .where(OrdenMedica.id == orden_id)
            .options(
                selectinload(OrdenMedica.paciente),
                selectinload(OrdenMedica.sucursal),
            )
        )
        res = await self.db.execute(stmt)
        orden = res.scalar_one_or_none()
        if not orden:
            raise EntityNotFoundException("OrdenMedica", orden_id)

        destinatario_email = (orden.contacto_email or (orden.paciente.email if orden.paciente else None) or "").strip().lower()
        paciente_nombre = orden.contacto_nombre or (f"{orden.paciente.nombres} {orden.paciente.apellidos}" if orden.paciente else "Paciente")
        asunto = f"Resolución de Auditoría Médica - Orden N° {orden.nro_orden}"

        copago = Decimal(str(orden.valor_copago or 0))
        estudios_no = Decimal(str(orden.valor_estudios_no_autorizados or 0))
        apb = Decimal(str(orden.valor_apb or 0))
        total_abonar = copago + estudios_no + apb

        resolucion_texto = orden.observacion_resultado_auditoria or "Auditoría médica aprobada. Se autorizan las prácticas solicitadas para su realización."

        # Cargar plantillas disponibles
        stmt_tpls = select(PlantillaEmail).where(PlantillaEmail.activa == True).order_by(PlantillaEmail.es_default.desc(), PlantillaEmail.nombre.asc())
        res_tpls = await self.db.execute(stmt_tpls)
        plantillas_list = list(res_tpls.scalars().all())

        tpl_default = next((t for t in plantillas_list if t.es_default), None)
        tpl_custom_html = tpl_default.cuerpo_html if (tpl_default and tpl_default.cuerpo_html and tpl_default.cuerpo_html.strip()) else None

        from backend.app.core.templates_email import generar_plantilla_email_resolucion
        cuerpo_html = generar_plantilla_email_resolucion(
            paciente_nombre=paciente_nombre,
            nro_orden=orden.nro_orden,
            mutual_nombre=orden.mutual,
            observacion_resolucion=resolucion_texto,
            copago=copago,
            estudios_no_autorizados_valor=estudios_no,
            valor_apb=apb,
            total_abonar=total_abonar,
            indicaciones_texto=orden.indicaciones_texto,
            sucursal_nombre=orden.sucursal.nombre if orden.sucursal else "Sede Central",
            contacto_telefono=orden.contacto_telefono or orden.contacto_celular,
            lista_estudios_autorizados=orden.estudios_autorizados or [],
            lista_estudios_no_autorizados=orden.estudios_no_autorizados or [],
            cuerpo_template_custom=tpl_custom_html,
        )

        from backend.app.modules.ordenes.schemas import PlantillaEmailRead
        return PreviewEmailResolucionRead(
            destinatario_email=destinatario_email,
            destinatario_nombre=paciente_nombre,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
            tiene_email=bool(destinatario_email),
            ya_enviado=orden.mail_enviado,
            mail_enviado_fecha=orden.mail_enviado_fecha,
            plantilla_id=tpl_default.id if tpl_default else None,
            plantillas_disponibles=[PlantillaEmailRead.model_validate(t) for t in plantillas_list],
        )

    async def enviar_email_resolucion(
        self,
        orden_id: uuid.UUID,
        dto: EnviarEmailResolucionRequest,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrdenMedica:
        stmt = (
            select(OrdenMedica)
            .where(OrdenMedica.id == orden_id)
            .options(
                selectinload(OrdenMedica.paciente),
                selectinload(OrdenMedica.sucursal),
            )
        )
        res = await self.db.execute(stmt)
        orden = res.scalar_one_or_none()
        if not orden:
            raise EntityNotFoundException("OrdenMedica", orden_id)

        target_email = dto.destinatario_email or orden.contacto_email or (orden.paciente.email if orden.paciente else None)
        if not target_email or not str(target_email).strip():
            raise AppException(status_code=400, detail="La orden médica no cuenta con una dirección de correo válida para el envío.")

        target_email = str(target_email).strip().lower()
        paciente_nombre = orden.contacto_nombre or (f"{orden.paciente.nombres} {orden.paciente.apellidos}" if orden.paciente else "Paciente")
        asunto = (dto.asunto or f"Resolución de Auditoría Médica - Orden N° {orden.nro_orden}").strip()

        copago = Decimal(str(orden.valor_copago or 0))
        estudios_no = Decimal(str(orden.valor_estudios_no_autorizados or 0))
        apb = Decimal(str(orden.valor_apb or 0))
        total_abonar = copago + estudios_no + apb

        if dto.cuerpo_html and dto.cuerpo_html.strip():
            cuerpo_html = dto.cuerpo_html.strip()
        else:
            resolucion_texto = orden.observacion_resultado_auditoria or "Auditoría médica aprobada."
            tpl_custom_html = None
            if dto.plantilla_id:
                stmt_t = select(PlantillaEmail).where(PlantillaEmail.id == dto.plantilla_id)
                res_t = await self.db.execute(stmt_t)
                t_obj = res_t.scalar_one_or_none()
                if t_obj and t_obj.cuerpo_html and t_obj.cuerpo_html.strip():
                    tpl_custom_html = t_obj.cuerpo_html

            from backend.app.core.templates_email import generar_plantilla_email_resolucion
            cuerpo_html = generar_plantilla_email_resolucion(
                paciente_nombre=paciente_nombre,
                nro_orden=orden.nro_orden,
                mutual_nombre=orden.mutual,
                observacion_resolucion=resolucion_texto,
                copago=copago,
                estudios_no_autorizados_valor=estudios_no,
                valor_apb=apb,
                total_abonar=total_abonar,
                indicaciones_texto=orden.indicaciones_texto,
                sucursal_nombre=orden.sucursal.nombre if orden.sucursal else "Sede Central",
                contacto_telefono=orden.contacto_telefono or orden.contacto_celular,
                lista_estudios_autorizados=orden.estudios_autorizados or [],
                lista_estudios_no_autorizados=orden.estudios_no_autorizados or [],
                cuerpo_template_custom=tpl_custom_html,
            )

        from backend.app.core.zeptomail import zepto_mail_service
        resultado = await zepto_mail_service.enviar_correo(
            destinatario_email=target_email,
            destinatario_nombre=paciente_nombre,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
        )

        if not resultado.get("success"):
            raise AppException(status_code=502, detail=f"No se pudo despachar el correo: {resultado.get('message')}")

        from datetime import timezone
        ahora = datetime.now(timezone.utc)
        orden.mail_enviado = True
        orden.mail_enviado_fecha = ahora
        orden.mail_enviado_por_id = current_user.id
        orden.mail_destinatario = target_email
        orden.mail_asunto = asunto
        orden.mail_cuerpo_html = cuerpo_html
        orden.mail_message_id = resultado.get("message_id")
        orden.mail_programado_para = None  # Ya no requiere despacho programado

        # Bitácora inmutable
        self.db.add(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="ENVIO_MAIL_RESOLUCION",
                estado_anterior=orden.estado.value,
                estado_nuevo=orden.estado.value,
                detalles={
                    "destinatario": target_email,
                    "asunto": asunto,
                    "message_id": resultado.get("message_id"),
                    "mock": resultado.get("mock", False),
                    "observaciones": dto.observaciones_adicionales,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )

        await self.db.commit()
        await self.db.refresh(orden)
        logger.info(f"Correo de resolucion despachado y registrado para orden {orden.nro_orden}")
        return orden

    async def cancelar_envio_automatico(
        self,
        orden_id: uuid.UUID,
        current_user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OrdenMedica:
        stmt = select(OrdenMedica).where(OrdenMedica.id == orden_id)
        res = await self.db.execute(stmt)
        orden = res.scalar_one_or_none()
        if not orden:
            raise EntityNotFoundException("OrdenMedica", orden_id)

        orden.mail_auto_cancelado = True
        orden.mail_programado_para = None

        self.db.add(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="CANCELACION_ENVIO_AUTO_MAIL",
                estado_anterior=orden.estado.value,
                estado_nuevo=orden.estado.value,
                detalles={"mensaje": "Operador frenó el despacho automático del correo"},
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        await self.db.commit()
        await self.db.refresh(orden)
        return orden

    async def actualizar_indicaciones_orden(
        self,
        orden_id: uuid.UUID,
        indicaciones_ids: List[str],
        indicaciones_texto: Optional[str],
        current_user: User,
    ) -> OrdenMedica:
        stmt = select(OrdenMedica).where(OrdenMedica.id == orden_id)
        res = await self.db.execute(stmt)
        orden = res.scalar_one_or_none()
        if not orden:
            raise EntityNotFoundException("OrdenMedica", orden_id)

        orden.indicaciones_ids = indicaciones_ids
        if indicaciones_texto is not None:
            orden.indicaciones_texto = indicaciones_texto

        await self.db.commit()
        await self.db.refresh(orden)
        return orden

    async def actualizar_estudios_auditoria(
        self,
        orden_id: uuid.UUID,
        estudios_autorizados: Optional[List[str]],
        estudios_no_autorizados: Optional[List[str]],
        current_user: User,
        estudios_detalle: Optional[List[Any]] = None,
    ) -> OrdenMedica:
        stmt = select(OrdenMedica).where(OrdenMedica.id == orden_id)
        res = await self.db.execute(stmt)
        orden = res.scalar_one_or_none()
        if not orden:
            raise EntityNotFoundException("OrdenMedica", orden_id)

        if estudios_detalle is not None:
            (
                detalle_dicts,
                estudios_aut,
                estudios_no_aut,
                valor_no_aut,
            ) = _sincronizar_estudios_y_totales(
                estudios_detalle=estudios_detalle,
                estudios_autorizados=estudios_autorizados,
                estudios_no_autorizados=estudios_no_autorizados,
                valor_estudios_no_autorizados=None,
            )
            orden.estudios_detalle = detalle_dicts or []
            if estudios_aut is not None:
                orden.estudios_autorizados = [s.strip() for s in estudios_aut if s.strip()]
            if estudios_no_aut is not None:
                orden.estudios_no_autorizados = [s.strip() for s in estudios_no_aut if s.strip()]
            if valor_no_aut is not None:
                orden.valor_estudios_no_autorizados = valor_no_aut
        else:
            if estudios_autorizados is not None:
                orden.estudios_autorizados = [s.strip() for s in estudios_autorizados if s.strip()]
            if estudios_no_autorizados is not None:
                orden.estudios_no_autorizados = [s.strip() for s in estudios_no_autorizados if s.strip()]

        await self.db.commit()
        await self.db.refresh(orden)
        return orden


class PlantillaEmailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plantillas(self, only_active: bool = False) -> List[PlantillaEmail]:
        stmt = select(PlantillaEmail).order_by(PlantillaEmail.es_default.desc(), PlantillaEmail.nombre.asc())
        if only_active:
            stmt = stmt.where(PlantillaEmail.activa == True)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, plantilla_id: uuid.UUID) -> PlantillaEmail:
        stmt = select(PlantillaEmail).where(PlantillaEmail.id == plantilla_id)
        res = await self.db.execute(stmt)
        tpl = res.scalar_one_or_none()
        if not tpl:
            raise EntityNotFoundException("PlantillaEmail", plantilla_id)
        return tpl

    async def create_plantilla(self, dto: PlantillaEmailCreate) -> PlantillaEmail:
        cod = dto.codigo.strip().upper()
        stmt = select(PlantillaEmail).where(PlantillaEmail.codigo == cod)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise EntityAlreadyExistsException("PlantillaEmail", "codigo", cod)

        if dto.es_default:
            # Desmarcar default previo
            await self.db.execute(
                select(PlantillaEmail).where(PlantillaEmail.es_default == True)
            )
            # update
            from sqlalchemy import update
            await self.db.execute(update(PlantillaEmail).values(es_default=False))

        tpl = PlantillaEmail(
            codigo=cod,
            nombre=dto.nombre.strip(),
            asunto=dto.asunto.strip(),
            cuerpo_html=dto.cuerpo_html or "",
            es_default=dto.es_default,
            activa=dto.activa,
        )
        self.db.add(tpl)
        await self.db.commit()
        await self.db.refresh(tpl)
        return tpl

    async def update_plantilla(self, plantilla_id: uuid.UUID, dto: PlantillaEmailUpdate) -> PlantillaEmail:
        tpl = await self.get_by_id(plantilla_id)
        if dto.codigo is not None:
            cod = dto.codigo.strip().upper()
            if cod != tpl.codigo:
                stmt = select(PlantillaEmail).where(PlantillaEmail.codigo == cod)
                res = await self.db.execute(stmt)
                if res.scalar_one_or_none():
                    raise EntityAlreadyExistsException("PlantillaEmail", "codigo", cod)
                tpl.codigo = cod

        if dto.es_default:
            from sqlalchemy import update
            await self.db.execute(update(PlantillaEmail).values(es_default=False))
            tpl.es_default = True
        elif dto.es_default is False:
            tpl.es_default = False

        if dto.nombre is not None:
            tpl.nombre = dto.nombre.strip()
        if dto.asunto is not None:
            tpl.asunto = dto.asunto.strip()
        if dto.cuerpo_html is not None:
            tpl.cuerpo_html = dto.cuerpo_html
        if dto.activa is not None:
            tpl.activa = dto.activa

        await self.db.commit()
        await self.db.refresh(tpl)
        return tpl

    async def delete_plantilla(self, plantilla_id: uuid.UUID) -> None:
        tpl = await self.get_by_id(plantilla_id)
        if tpl.es_default:
            raise ForbiddenActionException("No se puede eliminar la plantilla de correo predeterminada del sistema")
        await self.db.delete(tpl)
        await self.db.commit()
