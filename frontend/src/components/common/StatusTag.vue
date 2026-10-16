<script setup lang="ts">
import { computed, onMounted } from 'vue';
import Tag from 'primevue/tag';
import { EstadoOrden } from '../../types/ordenes';
import { useEstadosStore } from '../../stores/estados.store';

const props = defineProps<{
  value: EstadoOrden | string;
}>();

const estadosStore = useEstadosStore();

onMounted(() => {
  // Carga el catálogo de estados (cacheado) para respetar el color configurado.
  estadosStore.fetchEstados();
});

/**
 * Paleta de respaldo por estado del sistema, usada únicamente mientras el catálogo
 * configurable todavía no se cargó (o si el estado no existe en la configuración).
 */
const SEVERITY_FALLBACK: Record<string, string> = {
  Ingreso: 'info',
  INGRESO: 'info',
  'en Auditoria': 'warn',
  EN_AUDITORIA: 'warn',
  'Solicitudes de auditoria': 'danger',
  SOLICITUDES_AUDITORIA: 'danger',
  Actualizada: 'contrast',
  ACTUALIZADA: 'contrast',
  'Auditoria Finalizada': 'info',
  AUDITORIA_FINALIZADA: 'info',
  Cerrada: 'success',
  CERRADA: 'success',
  Cancelada: 'danger',
  CANCELADA: 'danger',
  'Dar de baja': 'secondary',
  DAR_DE_BAJA: 'secondary',
};

const FALLBACK_ICONO: Record<string, string> = {
  Ingreso: 'pi pi-inbox',
  INGRESO: 'pi pi-inbox',
  'en Auditoria': 'pi pi-search',
  EN_AUDITORIA: 'pi pi-search',
  'Solicitudes de auditoria': 'pi pi-exclamation-circle',
  SOLICITUDES_AUDITORIA: 'pi pi-exclamation-circle',
  Actualizada: 'pi pi-refresh',
  ACTUALIZADA: 'pi pi-refresh',
  'Auditoria Finalizada': 'pi pi-phone',
  AUDITORIA_FINALIZADA: 'pi pi-phone',
  Cerrada: 'pi pi-check-circle',
  CERRADA: 'pi pi-check-circle',
  Cancelada: 'pi pi-times-circle',
  CANCELADA: 'pi pi-times-circle',
  'Dar de baja': 'pi pi-ban',
  DAR_DE_BAJA: 'pi pi-ban',
};

// Si viene el código en mayúsculas (ej: 'INGRESO'), traduce a la descripción legible ('Ingreso')
const label = computed(() => {
  if (!props.value) return '';
  const cfg = estadosStore.getEstado(props.value);
  return cfg?.nombre || props.value;
});

// El color y el ícono se toman del catálogo administrable en /configuracion.
const severity = computed(
  () => estadosStore.getColorBadge(props.value) || SEVERITY_FALLBACK[props.value] || 'info'
);

const icon = computed(
  () => estadosStore.getIcono(props.value) || FALLBACK_ICONO[props.value] || undefined
);
</script>

<template>
  <Tag :value="label" :severity="severity" :icon="icon" rounded class="px-2.5 py-1 text-xs font-semibold" />
</template>
