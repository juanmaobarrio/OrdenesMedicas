import { OrdenMedicaDetail, ObservacionUnificada } from '../types/ordenes';
import { formatDateTime } from './date';

/**
 * Extrae y unifica cronológicamente en orden descendente (más nueva primero, más vieja última)
 * todas las observaciones, notas, solicitudes y motivos registrados en la orden médica:
 * 1. Observación de ingreso original.
 * 2. Solicitudes y notas informativas del auditor médico (con sus respuestas operativas).
 * 3. Motivos de cancelación o pase a baja administrativa.
 * 4. Observaciones registradas en cualquier cambio de estado (a través de audit_logs).
 * 5. Resolución y resultado final de auditoría médica.
 * 6. Actualizaciones de observaciones de ingreso.
 */
export function extraerObservacionesUnificadas(orden: OrdenMedicaDetail | null | undefined): ObservacionUnificada[] {
  if (!orden) return [];
  const list: ObservacionUnificada[] = [];
  const mensajesVistos = new Set<string>();

  // 1. Solicitudes y observaciones emitidas por el auditor médico
  if (orden.solicitudes && orden.solicitudes.length > 0) {
    for (const sol of orden.solicitudes) {
      const isInfo = sol.estado === 'INFORMACION';
      const isPend = sol.estado === 'PENDIENTE';
      list.push({
        id: `sol-${sol.id}`,
        tipo: 'SOLICITUD',
        titulo: sol.motivo_solicitud || (isInfo ? 'Nota Informativa del Auditor' : 'Solicitud de Auditoría'),
        mensaje: sol.mensaje_auditor,
        usuario: sol.auditor?.full_name ? `Dr/a. ${sol.auditor.full_name}` : 'Auditor Médico',
        fecha: sol.created_at,
        fechaFormateada: formatDateTime(sol.created_at),
        badgeLabel: isInfo ? 'INFORMACIÓN' : sol.estado,
        badgeSeverity: isInfo ? 'info' : (isPend ? 'warn' : 'success'),
        badgeIcon: isInfo ? 'pi pi-info-circle' : (isPend ? 'pi pi-clock' : 'pi pi-check'),
        cardBgClass: isInfo ? 'bg-blue-50/70' : (isPend ? 'bg-amber-50/60' : 'bg-slate-50'),
        cardBorderClass: isInfo ? 'border-blue-300' : (isPend ? 'border-amber-300' : 'border-slate-200'),
        solicitudId: sol.id,
        solicitudEstado: sol.estado,
        respuestaOperador: sol.respuesta_operador,
        respondidoPor: sol.respondido_por?.full_name,
      });
      mensajesVistos.add(`sol-${sol.mensaje_auditor.trim()}`);
    }
  }

  // 2. Historial de transiciones de estado y modificaciones registradas en audit_logs
  if (orden.audit_logs && orden.audit_logs.length > 0) {
    for (const log of orden.audit_logs) {
      const detalles = log.detalles || {};

      // Motivo de cambio de estado (ej: Cancelada, Dar de baja o cualquier cambio con motivo)
      if (detalles.motivo && typeof detalles.motivo === 'string' && detalles.motivo.trim()) {
        const texto = detalles.motivo.trim();
        const estNuevo = log.estado_nuevo || 'Cambio de Estado';
        const isCancel = estNuevo.toLowerCase().includes('cancelad') || estNuevo.toLowerCase().includes('baja');
        list.push({
          id: `log-motivo-${log.id}`,
          tipo: isCancel ? 'CANCELACION' : 'CAMBIO_ESTADO',
          titulo: isCancel ? `Motivo de ${estNuevo}` : `Observación: Pase a ${estNuevo}`,
          mensaje: texto,
          usuario: log.user?.full_name || 'Sistema',
          fecha: log.created_at,
          fechaFormateada: formatDateTime(log.created_at),
          badgeLabel: estNuevo.toUpperCase(),
          badgeSeverity: isCancel ? 'danger' : 'warn',
          badgeIcon: isCancel ? 'pi pi-times-circle' : 'pi pi-sync',
          cardBgClass: isCancel ? 'bg-red-50/80' : 'bg-amber-50/50',
          cardBorderClass: isCancel ? 'border-red-300' : 'border-amber-300',
        });
        mensajesVistos.add(`motivo-${texto}`);
      }

      // Observación de resultado de auditoría registrada en log
      if (detalles.observacion_resultado && typeof detalles.observacion_resultado === 'string' && detalles.observacion_resultado.trim()) {
        const texto = detalles.observacion_resultado.trim();
        list.push({
          id: `log-resultado-${log.id}`,
          tipo: 'RESOLUCION',
          titulo: 'Resolución Final de Auditoría Médica',
          mensaje: texto,
          usuario: log.user?.full_name || (orden.assigned_auditor?.full_name ? `Dr/a. ${orden.assigned_auditor.full_name}` : 'Auditor Médico'),
          fecha: log.created_at,
          fechaFormateada: formatDateTime(log.created_at),
          badgeLabel: 'RESOLUCIÓN DE AUDITORÍA',
          badgeSeverity: 'success',
          badgeIcon: 'pi pi-check-circle',
          cardBgClass: 'bg-emerald-50/90',
          cardBorderClass: 'border-emerald-300',
        });
        mensajesVistos.add(`resultado-${texto}`);
      }

      // Observaciones de ingreso actualizadas posteriormente
      if (detalles.observaciones_ingreso && typeof detalles.observaciones_ingreso === 'string' && detalles.observaciones_ingreso.trim()) {
        const texto = detalles.observaciones_ingreso.trim();
        list.push({
          id: `log-obs-edit-${log.id}`,
          tipo: 'ACTUALIZACION',
          titulo: 'Observaciones de Ingreso (Actualizadas)',
          mensaje: texto,
          usuario: log.user?.full_name || 'Operador',
          fecha: log.created_at,
          fechaFormateada: formatDateTime(log.created_at),
          badgeLabel: 'ACTUALIZACIÓN',
          badgeSeverity: 'contrast',
          badgeIcon: 'pi pi-pencil',
          cardBgClass: 'bg-slate-50',
          cardBorderClass: 'border-slate-200',
        });
        mensajesVistos.add(`ingreso-${texto}`);
      }
    }
  }

  // 3. Fallback para motivo de cancelación si no estuviera en audit_logs históricos
  if (orden.motivo_cancelacion && orden.motivo_cancelacion.trim()) {
    const texto = orden.motivo_cancelacion.trim();
    if (!mensajesVistos.has(`motivo-${texto}`)) {
      const est = orden.estado || 'Cancelada';
      list.push({
        id: 'orden-motivo-cancelacion',
        tipo: 'CANCELACION',
        titulo: `Motivo de ${est}`,
        mensaje: texto,
        usuario: orden.assigned_auditor?.full_name || orden.created_by_user?.full_name || 'Sistema',
        fecha: orden.updated_at || orden.created_at,
        fechaFormateada: formatDateTime(orden.updated_at || orden.created_at),
        badgeLabel: String(est).toUpperCase(),
        badgeSeverity: 'danger',
        badgeIcon: 'pi pi-times-circle',
        cardBgClass: 'bg-red-50/80',
        cardBorderClass: 'border-red-300',
      });
      mensajesVistos.add(`motivo-${texto}`);
    }
  }

  // 4. Fallback para resolución final si no estuviera en audit_logs históricos
  if (orden.observacion_resultado_auditoria && orden.observacion_resultado_auditoria.trim()) {
    const texto = orden.observacion_resultado_auditoria.trim();
    if (!mensajesVistos.has(`resultado-${texto}`)) {
      list.push({
        id: 'orden-observacion-resultado',
        tipo: 'RESOLUCION',
        titulo: 'Resolución Final de Auditoría Médica',
        mensaje: texto,
        usuario: orden.assigned_auditor?.full_name ? `Dr/a. ${orden.assigned_auditor.full_name}` : 'Auditor Médico',
        fecha: orden.updated_at || orden.created_at,
        fechaFormateada: formatDateTime(orden.updated_at || orden.created_at),
        badgeLabel: 'RESOLUCIÓN DE AUDITORÍA',
        badgeSeverity: 'success',
        badgeIcon: 'pi pi-check-circle',
        cardBgClass: 'bg-emerald-50/90',
        cardBorderClass: 'border-emerald-300',
      });
      mensajesVistos.add(`resultado-${texto}`);
    }
  }

  // 5. Observaciones de Ingreso originales
  if (orden.observaciones_ingreso && orden.observaciones_ingreso.trim()) {
    const texto = orden.observaciones_ingreso.trim();
    if (!mensajesVistos.has(`ingreso-${texto}`)) {
      list.push({
        id: 'orden-observaciones-ingreso',
        tipo: 'INGRESO',
        titulo: 'Observaciones de Ingreso',
        mensaje: texto,
        usuario: orden.created_by_user?.full_name || 'Operador de Ingreso',
        fecha: orden.created_at,
        fechaFormateada: formatDateTime(orden.created_at),
        badgeLabel: 'INGRESO',
        badgeSeverity: 'info',
        badgeIcon: 'pi pi-inbox',
        cardBgClass: 'bg-slate-50',
        cardBorderClass: 'border-slate-200',
      });
    }
  }

  // 6. Ordenamiento descendente estricto (más nueva primero, más vieja última)
  return list.sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime());
}
