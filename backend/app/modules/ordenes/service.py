import os
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional, Sequence, Tuple
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

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
    EstadoOrden,
    EstadoOrdenConfig,
    EstadoSolicitudAuditoria,
    MotivoCancelacion,
    OrdenMedica,
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
    EstadoOrdenConfigCreate,
    EstadoOrdenConfigUpdate,
    MotivoCancelacionCreate,
    MotivoCancelacionUpdate,
    OrdenLlamadaPendienteItem,
    OrdenMedicaAsignarAuditor,
    OrdenMedicaCambioEstado,
    OrdenMedicaCreate,
    OrdenMedicaUpdate,
    RegistroLlamadaCreate,
)

from backend.app.modules.pacientes.repository import PacienteRepository
from backend.app.modules.users.models import User
from backend.app.modules.users.repository import SucursalRepository, UserRepository


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
            valor_estudios_no_autorizados=dto.valor_estudios_no_autorizados,
            fecha_vencimiento=dto.fecha_vencimiento,
            numeros_auditoria=dto.numeros_auditoria,
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
        if orden.estado in [EstadoOrden.CANCELADA, EstadoOrden.DAR_DE_BAJA, EstadoOrden.CERRADA]:
            raise ForbiddenActionException(
                f"No se puede modificar una orden en estado final '{orden.estado.value}'"
            )

        diff = {}
        if dto.fecha_prescripcion is not None:
            diff["fecha_prescripcion"] = str(dto.fecha_prescripcion)
            orden.fecha_prescripcion = dto.fecha_prescripcion

        if dto.cantidad_ordenes_fisicas is not None:
            diff["cantidad_ordenes_fisicas"] = dto.cantidad_ordenes_fisicas
            orden.cantidad_ordenes_fisicas = dto.cantidad_ordenes_fisicas

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

        solicitud = AuditoriaSolicitud(
            orden_id=orden_id,
            auditor_id=current_user.id,
            motivo_solicitud=dto.motivo_solicitud.strip(),
            mensaje_auditor=dto.mensaje_auditor.strip(),
            estado=EstadoSolicitudAuditoria.PENDIENTE,
        )
        created_solicitud = await self.repo.create_solicitud(solicitud)

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

        await self.db.flush()

        # Auditoria
        await self.repo.create_audit_log(
            AuditoriaLog(
                orden_id=orden.id,
                user_id=current_user.id,
                accion="REGISTRO_LLAMADA_PACIENTE",
                estado_anterior=orden.estado.value,
                estado_nuevo=orden.estado.value,
                detalles={
                    "tipo_llamada": dto.tipo_llamada.value,
                    "resultado": dto.resultado.value,
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


