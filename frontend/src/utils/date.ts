/**
 * Utilidades para formateo de fechas y horas en zona horaria de Argentina (GMT-3).
 */

const TIMEZONE_ARGENTINA = 'America/Argentina/Buenos_Aires';

/**
 * Formatea una fecha y hora completa en formato argentino (DD/MM/YYYY HH:mm).
 * Ejemplo: 28/08/2026 15:30
 */
export function formatDateTime(dateStr?: string | Date | null): string {
  if (!dateStr) return '-';
  try {
    const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
    if (isNaN(date.getTime())) return String(dateStr);

    return date.toLocaleString('es-AR', {
      timeZone: TIMEZONE_ARGENTINA,
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return String(dateStr);
  }
}

/**
 * Formatea solo la fecha (DD/MM/YYYY).
 * Ejemplo: 28/08/2026
 */
export function formatDate(dateStr?: string | Date | null): string {
  if (!dateStr) return '-';
  try {
    // Si viene solo como YYYY-MM-DD, interpretar en zona horaria local
    if (typeof dateStr === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-').map(Number);
      return `${day.toString().padStart(2, '0')}/${month.toString().padStart(2, '0')}/${year}`;
    }
    const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
    if (isNaN(date.getTime())) return String(dateStr);

    return date.toLocaleDateString('es-AR', {
      timeZone: TIMEZONE_ARGENTINA,
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return String(dateStr);
  }
}

/**
 * Formatea solo la hora (HH:mm).
 * Ejemplo: 15:30
 */
export function formatTime(dateStr?: string | Date | null): string {
  if (!dateStr) return '-';
  try {
    const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
    if (isNaN(date.getTime())) return String(dateStr);

    return date.toLocaleTimeString('es-AR', {
      timeZone: TIMEZONE_ARGENTINA,
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return String(dateStr);
  }
}
/**
 * Convierte una fecha del backend (YYYY-MM-DD) a un objeto Date local.
 * Evita el corrimiento de un día que produce `new Date('YYYY-MM-DD')`
 * al interpretar la cadena en UTC.
 */
export function parseDate(value?: string | Date | null): Date | null {
  if (!value) return null;
  if (value instanceof Date) return isNaN(value.getTime()) ? null : value;
  const soloFecha = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (soloFecha) {
    return new Date(Number(soloFecha[1]), Number(soloFecha[2]) - 1, Number(soloFecha[3]));
  }
  const parsed = new Date(value);
  return isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Serializa un Date a la cadena YYYY-MM-DD que espera la API.
 * Usa componentes locales para no desplazar el día por la zona horaria.
 */
export function toISODate(value?: Date | string | null): string | null {
  const date = parseDate(value);
  if (!date) return null;
  const anio = date.getFullYear();
  const mes = String(date.getMonth() + 1).padStart(2, '0');
  const dia = String(date.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

/** Semáforo de vencimiento de una prescripción médica. */
export type EstadoVencimiento = 'vencida' | 'proxima' | 'vigente' | 'sin-fecha';

export interface SemaforoVencimiento {
  estado: EstadoVencimiento;
  /** Días restantes hasta el vencimiento (negativo si ya venció). `null` si no hay fecha. */
  dias: number | null;
  /** Clases Tailwind que colorean el campo según la vigencia. */
  clases: string;
}

/** Cantidad de días de anticipación con la que se avisa un vencimiento próximo. */
export const DIAS_ALERTA_VENCIMIENTO = 10;

/**
 * Calcula el semáforo visual de una fecha de vencimiento:
 * - `vencida` (rojo):  la fecha es previa o igual al día de hoy.
 * - `proxima` (amarillo): vence dentro de los próximos 10 días.
 * - `vigente` (verde): vence a más de 10 días.
 */
export function semaforoVencimiento(value?: string | Date | null): SemaforoVencimiento {
  const fecha = parseDate(value);

  if (!fecha) {
    return {
      estado: 'sin-fecha',
      dias: null,
      clases: 'bg-white',
    };
  }

  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const objetivo = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());

  const dias = Math.round((objetivo.getTime() - hoy.getTime()) / 86400000);

  // El color se aplica a todo el campo (fondo, borde y contorno), sin leyendas de texto.
  if (dias <= 0) {
    return { estado: 'vencida', dias, clases: 'semaforo-vencida' };
  }

  if (dias <= DIAS_ALERTA_VENCIMIENTO) {
    return { estado: 'proxima', dias, clases: 'semaforo-proxima' };
  }

  return { estado: 'vigente', dias, clases: 'semaforo-vigente' };
}
