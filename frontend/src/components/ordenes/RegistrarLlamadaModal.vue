<script setup lang="ts">
import { ref, watch } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import Dropdown from 'primevue/dropdown';
import Textarea from 'primevue/textarea';
import { useToast } from 'primevue/usetoast';
import { useOrdenesStore } from '../../stores/ordenes.store';
import { ResultadoLlamada, TipoLlamada } from '../../types/ordenes';

const props = defineProps<{
  visible: boolean;
  ordenId: string;
  nroOrden: string;
  pacienteNombre: string;
  telefono?: string | null;
  tipoLlamada: TipoLlamada;
}>();

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void;
  (e: 'success'): void;
}>();

const toast = useToast();
const ordenesStore = useOrdenesStore();

const resultado = ref<ResultadoLlamada>('EXITOSA');
const observaciones = ref<string>('');
const isSubmitting = ref<boolean>(false);

const opcionesResultado = [
  { label: 'Comunicación Exitosa (Avisado)', value: 'EXITOSA' },
  { label: 'No Contesta', value: 'NO_CONTESTA' },
  { label: 'Número Erróneo / Inexistente', value: 'NUMERO_ERRONEO' },
  { label: 'Volver a Intentar', value: 'REINTENTAR' },
];

watch(
  () => props.visible,
  (val) => {
    if (val) {
      resultado.value = 'EXITOSA';
      observaciones.value = '';
    }
  }
);

const handleSubmit = async () => {
  isSubmitting.value = true;
  try {
    await ordenesStore.registrarLlamada(
      props.ordenId,
      props.tipoLlamada,
      resultado.value,
      observaciones.value
    );

    toast.add({
      severity: resultado.value === 'EXITOSA' ? 'success' : 'info',
      summary: 'Llamada Registrada',
      detail:
        resultado.value === 'EXITOSA'
          ? 'Se registró el aviso exitoso. La orden salió de pendientes.'
          : 'Se guardó el intento de llamada.',
      life: 4000,
    });

    emit('update:visible', false);
    emit('success');
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo registrar la llamada',
      life: 4000,
    });
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    modal
    :header="`Registrar Llamada - ${nroOrden}`"
    :style="{ width: '500px' }"
  >
    <div class="space-y-4">
      <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
        <p class="text-xs font-semibold text-slate-500 uppercase">Paciente</p>
        <p class="text-sm font-medium text-slate-800">{{ pacienteNombre }}</p>
        <p class="text-sm text-slate-600 mt-1">
          <i class="pi pi-phone text-xs mr-1 text-primary-600"></i>
          {{ telefono || 'Sin teléfono registrado' }}
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Resultado del Contacto</label>
        <Dropdown
          v-model="resultado"
          :options="opcionesResultado"
          optionLabel="label"
          optionValue="value"
          class="w-full"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Observaciones de la Comunicación</label>
        <Textarea
          v-model="observaciones"
          rows="3"
          class="w-full"
          placeholder="Ej: Se le avisó al paciente y confirmó que pasará mañana a retirar la autorización."
        />
      </div>
    </div>

    <template #footer>
      <Button label="Cancelar" text severity="secondary" @click="emit('update:visible', false)" />
      <Button
        label="Guardar Registro"
        icon="pi pi-check"
        :loading="isSubmitting"
        @click="handleSubmit"
      />
    </template>
  </Dialog>
</template>
