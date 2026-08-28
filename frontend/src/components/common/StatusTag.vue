<script setup lang="ts">
import { computed } from 'vue';
import Tag from 'primevue/tag';
import { EstadoOrden } from '../../types/ordenes';

const props = defineProps<{
  value: EstadoOrden | string;
}>();

const severity = computed(() => {
  switch (props.value) {
    case 'Ingreso':
      return 'info';
    case 'en Auditoria':
      return 'warn';
    case 'Solicitudes de auditoria':
      return 'danger';
    case 'Actualizada':
      return 'contrast';
    case 'Auditoria Finalizada':
      return 'info';
    case 'Cerrada':
      return 'success';
    case 'Cancelada':
      return 'danger';
    case 'Dar de baja':
      return 'secondary';
    default:
      return 'info';
  }
});

const icon = computed(() => {
  switch (props.value) {
    case 'Ingreso':
      return 'pi pi-inbox';
    case 'en Auditoria':
      return 'pi pi-search';
    case 'Solicitudes de auditoria':
      return 'pi pi-exclamation-circle';
    case 'Actualizada':
      return 'pi pi-refresh';
    case 'Auditoria Finalizada':
      return 'pi pi-phone';
    case 'Cerrada':
      return 'pi pi-check-circle';
    case 'Cancelada':
      return 'pi pi-times-circle';
    case 'Dar de baja':
      return 'pi pi-ban';
    default:
      return undefined;
  }
});
</script>

<template>
  <Tag :value="value" :severity="severity" :icon="icon" rounded class="px-2.5 py-1 text-xs font-semibold" />
</template>
