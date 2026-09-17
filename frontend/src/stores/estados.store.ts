import { defineStore } from 'pinia';
import { ref } from 'vue';
import { configService } from '../services/config.service';
import { EstadoOrdenConfig } from '../types/ordenes';

/**
 * Store del catálogo de Estados del Sistema.
 *
 * Los estados se administran desde `/configuracion` (nombre, tipo, requiere motivo,
 * color del badge e ícono). Este store mantiene ese catálogo disponible en memoria para
 * que los componentes de presentación (StatusTag, filtros, listados) pinten el estado con
 * el color REALMENTE configurado por el usuario y no con una paleta por defecto.
 */
export const useEstadosStore = defineStore('estados', () => {
  const estados = ref<EstadoOrdenConfig[]>([]);
  const isLoaded = ref(false);
  const isLoading = ref(false);
  let inflight: Promise<EstadoOrdenConfig[]> | null = null;

  /** Mapa `nombre de estado -> configuración` para búsquedas O(1) por nombre. */
  const indexByNombre = (lista: EstadoOrdenConfig[]): Record<string, EstadoOrdenConfig> =>
    lista.reduce<Record<string, EstadoOrdenConfig>>((acc, item) => {
      acc[item.nombre] = item;
      acc[item.codigo] = item;
      return acc;
    }, {});

  const byNombre = ref<Record<string, EstadoOrdenConfig>>({});

  /**
   * Carga el catálogo de estados. Se cachea en memoria: use `force = true` para
   * refrescarlo después de crear, editar o desactivar un estado en Configuración.
   */
  const fetchEstados = async (force = false): Promise<EstadoOrdenConfig[]> => {
    if (isLoaded.value && !force) return estados.value;

    // Evita peticiones duplicadas cuando varios componentes montan a la vez
    if (inflight && !force) return inflight;

    isLoading.value = true;
    inflight = configService
      .listEstados(false)
      .then((data) => {
        estados.value = data || [];
        byNombre.value = indexByNombre(estados.value);
        isLoaded.value = true;
        return estados.value;
      })
      .catch((err) => {
        console.warn('No se pudo cargar el catálogo de estados del sistema:', err);
        return estados.value;
      })
      .finally(() => {
        isLoading.value = false;
        inflight = null;
      });

    return inflight;
  };

  /**
   * Devuelve la configuración de un estado por su nombre o código.
   * Acepta `undefined` para simplificar el uso directo desde el template.
   */
  const getEstado = (nombreOCodigo?: string | null): EstadoOrdenConfig | undefined => {
    if (!nombreOCodigo) return undefined;
    return byNombre.value[nombreOCodigo];
  };

  /**
   * Color del badge configurado para un estado ('info', 'warn', 'danger', 'success',
   * 'secondary', 'contrast'). Devuelve `undefined` si el estado no está en el catálogo,
   * para que el consumidor pueda aplicar su propio fallback.
   */
  const getColorBadge = (nombreOCodigo?: string | null): string | undefined => {
    return getEstado(nombreOCodigo)?.color_badge || undefined;
  };

  /** Ícono configurado para un estado (formato PrimeIcons, ej: `pi pi-inbox`). */
  const getIcono = (nombreOCodigo?: string | null): string | undefined => {
    return getEstado(nombreOCodigo)?.icono || undefined;
  };

  /** ¿El estado exige motivo obligatorio (cancelación / baja) según la configuración? */
  const requiereMotivo = (nombreOCodigo?: string | null): boolean => {
    return Boolean(getEstado(nombreOCodigo)?.requiere_motivo);
  };

  return {
    estados,
    isLoaded,
    isLoading,
    fetchEstados,
    getEstado,
    getColorBadge,
    getIcono,
    requiereMotivo,
  };
});
