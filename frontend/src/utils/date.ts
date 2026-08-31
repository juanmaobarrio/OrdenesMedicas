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
