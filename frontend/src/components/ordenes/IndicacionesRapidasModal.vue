<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Checkbox from 'primevue/checkbox';
import { useToast } from 'primevue/usetoast';
import { configService } from '../../services/config.service';
import { IndicacionEstudio } from '../../types/ordenes';
import RichTextEditor from '../common/RichTextEditor.vue';
import ImpresionIndicacionesModal from './ImpresionIndicacionesModal.vue';

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
}>();

const toast = useToast();
const isLoadingIndicaciones = ref(false);
const indicacionesDisponibles = ref<IndicacionEstudio[]>([]);
const selectedCodigos = ref<string[]>([]);

// Formulario
const pacienteNombre = ref('');
const mutual = ref('Particular');
const telefono = ref('');
const indicacionesTexto = ref('');
const incluirDefault = ref(true);

// Estado de modal de impresión previa
const isPreviewPrintVisible = ref(false);
const printData = ref<any>(null);

const loadIndicaciones = async () => {
  isLoadingIndicaciones.value = true;
  try {
    const list = await configService.listIndicaciones(true);
    indicacionesDisponibles.value = list.sort((a, b) => (a.orden_secuencia ?? 0) - (b.orden_secuencia ?? 0));
  } catch (err) {
    console.error('Error cargando catálogo de indicaciones:', err);
  } finally {
    isLoadingIndicaciones.value = false;
  }
};

const toggleIndicacionChip = (ind: IndicacionEstudio) => {
  const idx = selectedCodigos.value.indexOf(ind.codigo);
  if (idx >= 0) {
    selectedCodigos.value.splice(idx, 1);
  } else {
    selectedCodigos.value.push(ind.codigo);
  }

  // Generar texto acumulado
  const selectedObjs = selectedCodigos.value
    .map((code) => indicacionesDisponibles.value.find((i) => i.codigo === code))
    .filter(Boolean) as IndicacionEstudio[];

  indicacionesTexto.value = selectedObjs
    .map((i) => `<p><strong>• ${i.titulo}:</strong> ${i.instrucciones}</p>`)
    .join('');
};

const resetForm = () => {
  pacienteNombre.value = '';
  mutual.value = 'Particular';
  telefono.value = '';
  indicacionesTexto.value = '';
  selectedCodigos.value = [];
  incluirDefault.value = true;
};

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (indicacionesDisponibles.value.length === 0) {
        loadIndicaciones();
      }
    } else {
      resetForm();
    }
  }
);

onMounted(() => {
  if (props.visible) {
    loadIndicaciones();
  }
});

const handleAbrirImpresion = () => {
  if (!pacienteNombre.value.trim()) {
    toast.add({
      severity: 'warn',
      summary: 'Nombre Requerido',
      detail: 'Por favor ingrese el nombre del paciente para confeccionar la hoja de indicaciones.',
      life: 3500,
    });
    return;
  }

  printData.value = {
    paciente_nombre: pacienteNombre.value.trim(),
    mutual: mutual.value.trim() || 'Particular',
    contacto_telefono: telefono.value.trim(),
    fecha: new Date().toLocaleDateString('es-AR'),
    indicaciones_html: indicacionesTexto.value.trim(),
  };

  isPreviewPrintVisible.value = true;
};
</script>

<template>
  <div>
    <Dialog
      :visible="visible"
      modal
      :style="{ width: '680px', maxWidth: '95vw' }"
      header="Impresión Rápida de Indicaciones para Pacientes"
      @update:visible="(v) => emit('update:visible', v)"
    >
      <div class="space-y-4 pt-1">
        <!-- Banner Informativo -->
        <div class="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
          <i class="pi pi-print text-blue-600 text-lg mt-0.5"></i>
          <div class="text-xs text-blue-900 leading-relaxed">
            <p class="font-bold">Emisión rápida de indicaciones sin registro de orden</p>
            <p class="text-blue-700 mt-0.5">
              Ideal para entregar instrucciones impresas a pacientes que consultan en recepción o por ventanilla antes de su fecha de estudio.
            </p>
          </div>
        </div>

        <!-- Campos Principales -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Nombre del Paciente <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="pacienteNombre"
              placeholder="Ej: Pérez, Juan Carlos"
              class="w-full text-xs font-semibold"
              autofocus
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Obra Social / Cobertura
            </label>
            <InputText
              v-model="mutual"
              placeholder="Ej: OSDE, PAMI, Particular..."
              class="w-full text-xs"
            />
          </div>
        </div>

        <!-- Chips de Indicaciones Disponibles -->
        <div v-if="indicacionesDisponibles.length > 0" class="space-y-1.5">
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            Seleccionar Indicaciones Frecuentes (clic para sumar):
          </label>
          <div class="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto p-1.5 bg-slate-50 border border-slate-200 rounded-lg">
            <span
              v-for="ind in indicacionesDisponibles"
              :key="ind.codigo"
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer transition select-none"
              :class="
                selectedCodigos.includes(ind.codigo)
                  ? 'bg-blue-600 text-white shadow-xs font-semibold'
                  : 'bg-white text-slate-700 border border-slate-200 hover:border-blue-400 hover:bg-blue-50'
              "
              @click="toggleIndicacionChip(ind)"
            >
              <i v-if="selectedCodigos.includes(ind.codigo)" class="pi pi-check text-[10px]"></i>
              <span>{{ ind.titulo }}</span>
            </span>
          </div>
        </div>

        <!-- Editor Enriquecido -->
        <div class="space-y-1.5">
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            Texto de Indicaciones Clínicas:
          </label>
          <RichTextEditor
            v-model="indicacionesTexto"
            min-height="160px"
            placeholder="Seleccione indicaciones arriba o redacte libremente aquí..."
          />
        </div>

        <!-- Opción Indicación por Defecto -->
        <div class="p-3 bg-amber-50/60 border border-amber-200 rounded-lg flex items-center gap-2.5 text-xs text-amber-950">
          <Checkbox v-model="incluirDefault" inputId="chkRapidoDefault" binary />
          <label for="chkRapidoDefault" class="cursor-pointer select-none font-medium">
            Incluir recuadro institucional con requisitos generales (DNI, orden médica y horarios de atención)
          </label>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" size="small" @click="emit('update:visible', false)" />
        <Button
          label="Vista Previa e Imprimir"
          icon="pi pi-print"
          severity="primary"
          size="small"
          @click="handleAbrirImpresion"
        />
      </template>
    </Dialog>

    <!-- Modal de Impresión Final -->
    <ImpresionIndicacionesModal
      v-model:visible="isPreviewPrintVisible"
      :initial-data="printData"
    />
  </div>
</template>
