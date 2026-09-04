import { Paciente } from './pacientes';
import { Sucursal, UserSummary } from './users';

export type EstadoOrden =
  | 'Ingreso'
  | 'en Auditoria'
  | 'Solicitudes de auditoria'
  | 'Actualizada'
  | 'Auditoria Finalizada'
  | 'Dar de baja'
  | 'Cancelada'
  | 'Cerrada';

export type EstadoSolicitud = 'PENDIENTE' | 'INFORMACION' | 'RESPONDIDA' | 'CERRADA';
export type TipoLlamada =
  | 'SOLICITUD_AUDITORIA'
  | 'AUDITORIA_FINALIZADA'
  | 'CONSULTA_PACIENTE'
  | 'SEGUIMIENTO_SUCURSAL'
  | 'OTRO';
export type ResultadoLlamada = 'EXITOSA' | 'NO_CONTESTA' | 'NUMERO_ERRONEO' | 'REINTENTAR';

export interface EstudioDetalleItem {
  codigo?: string | null;
  nombre: string;
  precio: number;
  autorizado: boolean;
}

export interface AdjuntoOrden {
  id: string;
  nombre_archivo_original: string;
  nombre_archivo_almacenado: string;
  tipo_mime: string;
  tamano_bytes: number;
  subido_por?: UserSummary;
  created_at: string;
}

export interface AuditoriaSolicitud {
  id: string;
  orden_id: string;
  motivo_solicitud: string;
  mensaje_auditor: string;
  respuesta_operador?: string | null;
  fecha_respuesta?: string | null;
  estado: EstadoSolicitud;
  auditor?: UserSummary;
  respondido_por?: UserSummary;
  created_at: string;
  updated_at: string;
}

export interface RegistroLlamada {
  id: string;
  orden_id: string;
  tipo_llamada: TipoLlamada;
  resultado: ResultadoLlamada;
  observaciones?: string | null;
  operador?: UserSummary;
  created_at: string;
}

export interface AuditoriaLog {
  id: string;
  orden_id: string;
  accion: string;
  estado_anterior?: string | null;
  estado_nuevo?: string | null;
  detalles: Record<string, any>;
  ip_address?: string | null;
  user?: UserSummary | null;
  created_at: string;
}

export interface MotivoCancelacion {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  activo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface MotivoCancelacionCreate {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  activo?: boolean;
}

export interface MotivoCancelacionUpdate {
  nombre?: string;
  descripcion?: string | null;
  activo?: boolean;
}

export type TipoEstadoOrden = 'PROCESO' | 'FINALIZACION';

export interface EstadoOrdenConfig {
  id: number;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  tipo: TipoEstadoOrden;
  requiere_motivo: boolean;
  color_badge: string;
  icono?: string | null;
  es_sistema: boolean;
  activo: boolean;
  orden_secuencia: number;
  created_at?: string;
  updated_at?: string;
}

export interface EstadoOrdenConfigCreate {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  tipo: TipoEstadoOrden;
  requiere_motivo?: boolean;
  color_badge?: string;
  icono?: string | null;
  activo?: boolean;
  orden_secuencia?: number;
}

export interface EstadoOrdenConfigUpdate {
  nombre?: string;
  descripcion?: string | null;
  tipo?: TipoEstadoOrden;
  requiere_motivo?: boolean;
  color_badge?: string;
  icono?: string | null;
  activo?: boolean;
  orden_secuencia?: number;
}

export interface OrdenMedicaListItem {
  id: string;
  nro_orden: string;
  estado: EstadoOrden;
  fecha_prescripcion: string;
  mutual: string;
  nro_afiliado?: string | null;
  valor_copago: number;
  valor_estudios_no_autorizados?: number;
  abona_apb?: boolean;
  valor_apb?: number;
  cantidad_ordenes_fisicas: number;

  numeros_auditoria: string[];
  estudios_autorizados?: string[];
  estudios_no_autorizados?: string[];
  estudios_detalle?: EstudioDetalleItem[];
  debe_orden_medica?: boolean;
  indicaciones_ids?: string[];
  mail_enviado?: boolean;
  paciente: Paciente;
  sucursal: Sucursal;
  created_by_user: UserSummary;
  assigned_auditor?: UserSummary | null;
  cant_adjuntos: number;
  cant_solicitudes_pendientes: number;
  llamada_solicitud_completada: boolean;
  llamada_finalizada_completada: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrdenMedicaDetail {
  id: string;
  nro_orden: string;
  estado: EstadoOrden;
  fecha_prescripcion: string;
  cantidad_ordenes_fisicas: number;
  sucursal_id?: string;
  mutual: string;
  nro_afiliado?: string | null;
  valor_copago: number;
  valor_estudios_no_autorizados?: number;
  abona_apb?: boolean;
  valor_apb?: number;
  fecha_vencimiento?: string | null;

  numeros_auditoria: string[];
  estudios_autorizados?: string[];
  estudios_no_autorizados?: string[];
  estudios_detalle?: EstudioDetalleItem[];
  debe_orden_medica?: boolean;
  indicaciones_ids?: string[];
  indicaciones_texto?: string | null;
  mail_enviado?: boolean;
  mail_enviado_fecha?: string | null;
  mail_enviado_por_id?: string | null;
  mail_destinatario?: string | null;
  mail_asunto?: string | null;
  mail_cuerpo_html?: string | null;
  mail_message_id?: string | null;
  mail_programado_para?: string | null;
  mail_auto_cancelado?: boolean;
  contacto_nombre?: string | null;
  contacto_horario?: string | null;
  contacto_telefono?: string | null;
  contacto_celular?: string | null;
  contacto_email?: string | null;
  observaciones_ingreso?: string | null;
  observacion_resultado_auditoria?: string | null;
  motivo_cancelacion?: string | null;
  llamada_solicitud_completada: boolean;
  llamada_solicitud_fecha?: string | null;
  llamada_solicitud_observacion?: string | null;
  llamada_finalizada_completada: boolean;
  llamada_finalizada_fecha?: string | null;
  llamada_finalizada_observacion?: string | null;
  paciente: Paciente;
  sucursal: Sucursal;
  created_by_user: UserSummary;
  assigned_auditor?: UserSummary | null;
  adjuntos: AdjuntoOrden[];
  solicitudes: AuditoriaSolicitud[];
  llamadas_registro: RegistroLlamada[];
  audit_logs: AuditoriaLog[];
  created_at: string;
  updated_at: string;
}

export interface OrdenMedicaCreate {
  paciente_id: string;
  sucursal_id: string;
  fecha_prescripcion: string;
  cantidad_ordenes_fisicas: number;
  mutual: string;
  nro_afiliado: string;
  valor_copago: number;
  valor_estudios_no_autorizados?: number;
  abona_apb?: boolean;
  valor_apb?: number;
  fecha_vencimiento?: string | null;

  numeros_auditoria: string[];
  estudios_detalle?: EstudioDetalleItem[];
  contacto_nombre?: string | null;
  contacto_horario?: string | null;
  contacto_telefono?: string | null;
  contacto_celular?: string | null;
  contacto_email?: string | null;
  observaciones_ingreso?: string | null;
  debe_orden_medica?: boolean;
}

export interface OrdenLlamadaPendienteItem {
  id: string;
  nro_orden: string;
  estado: EstadoOrden;
  tipo_llamada_requerida: TipoLlamada;
  motivo_aviso: string;
  fecha_estado: string;
  paciente_nombre: string;
  paciente_documento: string;
  paciente_telefono?: string | null;
  contacto_nombre?: string | null;
  contacto_horario?: string | null;
  contacto_telefono?: string | null;
  contacto_celular?: string | null;
  contacto_email?: string | null;
  sucursal_nombre: string;
  mutual: string;
  observaciones_ingreso?: string | null;
  observacion_resultado_auditoria?: string | null;
  debe_orden_medica?: boolean;
  cant_intentos_previos: number;
  solicitudes_pendientes?: AuditoriaSolicitud[];
}

export interface ConfiguracionAPB {
  valor_apb: number;
  descripcion?: string;
  updated_at?: string;
}

// ==========================================
// FEATURE FLAGS / FUNCIONALIDADES
// ==========================================
export interface SystemFeaturesConfig {
  modulo_mail: boolean;
  calculadora_estudios: boolean;
  estudios_autorizacion: boolean;
  indicaciones_estudios: boolean;
  asignar_auditor: boolean;
}

export interface SystemFeaturesConfigUpdate {
  modulo_mail?: boolean;
  calculadora_estudios?: boolean;
  estudios_autorizacion?: boolean;
  indicaciones_estudios?: boolean;
  asignar_auditor?: boolean;
}


// ==========================================
// INDICACIONES DE ESTUDIOS Y NOTIFICACIONES EMAIL
// ==========================================
export interface IndicacionEstudio {
  id: string;
  codigo: string;
  titulo: string;
  instrucciones: string;
  categoria?: string | null;
  color: string;
  orden_secuencia: number;
  activa: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface IndicacionEstudioCreate {
  codigo: string;
  titulo: string;
  instrucciones: string;
  categoria?: string | null;
  color?: string;
  orden_secuencia?: number;
  activa?: boolean;
}

export interface IndicacionEstudioUpdate {
  codigo?: string;
  titulo?: string;
  instrucciones?: string;
  categoria?: string | null;
  color?: string;
  orden_secuencia?: number;
  activa?: boolean;
}

export interface ConfiguracionMailAutomatizacion {
  envio_automatico: boolean;
  minutos_gracia: number;
  zeptomail_configurado: boolean;
  remitente_email: string;
  remitente_nombre: string;
}

export interface PreviewEmailResolucion {
  destinatario_email: string;
  destinatario_nombre: string;
  asunto: string;
  cuerpo_html: string;
  tiene_email: boolean;
  ya_enviado: boolean;
  mail_enviado_fecha?: string | null;
  plantilla_id?: string | null;
  plantillas_disponibles?: PlantillaEmail[];
}

export interface EnviarEmailResolucionPayload {
  destinatario_email?: string;
  asunto?: string;
  cuerpo_html?: string;
  plantilla_id?: string | null;
  observaciones_adicionales?: string;
}


export interface PlantillaEmail {
  id: string;
  codigo: string;
  nombre: string;
  asunto: string;
  cuerpo_html: string;
  es_default: boolean;
  activa: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PlantillaEmailCreate {
  codigo: string;
  nombre: string;
  asunto: string;
  cuerpo_html?: string;
  es_default?: boolean;
  activa?: boolean;
}

export interface PlantillaEmailUpdate {
  codigo?: string;
  nombre?: string;
  asunto?: string;
  cuerpo_html?: string;
  es_default?: boolean;
  activa?: boolean;
}
