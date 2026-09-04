<script setup lang="ts">
import { ref, computed } from 'vue';
import { IndicacionEstudio } from '../../types/ordenes';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import Textarea from 'primevue/textarea';

const props = defineProps<{
  modelValue: string[]; // IDs o códigos seleccionados
  textoConsolidado?: string | null;
  indicacionesDisponibles: IndicacionEstudio[];
  readonly?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void;
  (e: 'update:textoConsolidado', value: string): void;
  (e: 'change', payload: { ids: string[]; texto: string }): void;
}>();

const isSelectorOpen = ref(false);
const isEditTextoOpen = ref(false);
const textoManual = ref('');

// Indicaciones seleccionadas completas
const selectedObjects = computed(() => {
  return props.modelValue
    .map((idOrCode) =>
      props.indicacionesDisponibles.find((i) => i.id === idOrCode || i.codigo === idOrCode)
    )
    .filter(Boolean) as IndicacionEstudio[];
});

const autoTexto = computed(() => {
  if (props.textoConsolidado && props.textoConsolidado.trim()) {
    return props.textoConsolidado;
  }
  return selectedObjects.value.map((i) => `• ${i.titulo}: ${i.instrucciones}`).join('\n\n');
});

const toggleIndicacion = (ind: IndicacionEstudio) => {
  if (props.readonly) return;
  const current = [...props.modelValue];
  const idx = current.indexOf(ind.codigo);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push(ind.codigo);
  }
  emit('update:modelValue', current);

  // Recalcular texto sugerido
  const newSelected = current
    .map((code) => props.indicacionesDisponibles.find((i) => i.codigo === code))
    .filter(Boolean) as IndicacionEstudio[];
  const newTexto = newSelected.map((i) => `• ${i.titulo}: ${i.instrucciones}`).join('\n\n');
  emit('update:textoConsolidado', newTexto);
  emit('change', { ids: current, texto: newTexto });
};

const removeIndicacion = (code: string) => {
  if (props.readonly) return;
  const current = props.modelValue.filter((c) => c !== code);
  emit('update:modelValue', current);

  const newSelected = current
    .map((c) => props.indicacionesDisponibles.find((i) => i.codigo === c))
    .filter(Boolean) as IndicacionEstudio[];
  const newTexto = newSelected.map((i) => `• ${i.titulo}: ${i.instrucciones}`).join('\n\n');
  emit('update:textoConsolidado', newTexto);
  emit('change', { ids: current, texto: newTexto });
};

const openEditTexto = () => {
  textoManual.value = autoTexto.value;
  isEditTextoOpen.value = true;
};

const saveEditTexto = () => {
  emit('update:textoConsolidado', textoManual.value.trim());
  emit('change', { ids: props.modelValue, texto: textoManual.value.trim() });
  isEditTextoOpen.value = false;
};
</script>

<template>
  <div class="space-y-2">
    <!-- Barra con chips e inserción rápida -->
    <div class="flex flex-wrap items-center gap-1.5 min-h-[32px]">
      <!-- Chips ya seleccionados -->
      <span
        v-for="ind in selectedObjects"
        :key="ind.codigo"
        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border shadow-xs transition"
        :class="{
          'bg-blue-50 text-blue-900 border-blue-300': ind.color === 'info',
          'bg-amber-50 text-amber-900 border-amber-300': ind.color === 'warn',
          'bg-emerald-50 text-emerald-900 border-emerald-300': ind.color === 'success',
          'bg-red-50 text-red-900 border-red-300': ind.color === 'danger',
          'bg-slate-100 text-slate-800 border-slate-300': ind.color === 'contrast' || ind.color === 'secondary',
        }"
      >
        <span>{{ ind.titulo }}</span>
        <button
          v-if="!readonly"
          type="button"
          class="hover:opacity-75 text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold"
          @click.stop="removeIndicacion(ind.codigo)"
          title="Remover indicación"
        >
          ✕
        </button>
      </span>

      <!-- Empty state si no hay indicaciones -->
      <span v-if="selectedObjects.length === 0" class="text-xs text-slate-400 italic">
        Sin indicaciones clínicas asignadas.
      </span>

      <!-- Botón para añadir / desplegar selector rápido -->
      <Button
        v-if="!readonly"
        icon="pi pi-plus"
        label="Agregar Indicación"
        size="small"
        text
        severity="primary"
        class="text-xs py-0.5 px-2 font-bold"
        @click="isSelectorOpen = true"
      />

      <!-- Botón para ver/editar texto final -->
      <Button
        v-if="selectedObjects.length > 0 || (textoConsolidado && textoConsolidado.trim())"
        icon="pi pi-file-edit"
        label="Editar Texto de Preparación"
        size="small"
        text
        severity="secondary"
        class="text-xs py-0.5 px-2 text-slate-600 hover:text-slate-900 ml-auto"
        @click="openEditTexto"
      />
    </div>

    <!-- Modal Selector de Chips -->
    <Dialog
      v-model:visible="isSelectorOpen"
      modal
      header="Seleccionar Indicaciones Clínicas de Preparación"
      :style="{ width: '600px' }"
    >
      <div class="space-y-3">
        <p class="text-xs text-slate-500">
          Haga clic en las indicaciones que aplican a los análisis de este paciente para agregarlas o quitarlas:
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-[360px] overflow-y-auto pr-1">
          <div
            v-for="ind in indicacionesDisponibles"
            :key="ind.codigo"
            class="p-2.5 rounded-lg border cursor-pointer transition flex items-start gap-2.5 text-xs select-none"
            :class="
              modelValue.includes(ind.codigo)
                ? 'bg-blue-50 border-blue-400 text-blue-950 shadow-xs ring-1 ring-blue-400'
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
            "
            @click="toggleIndicacion(ind)"
          >
            <div
              class="w-4 h-4 rounded flex items-center justify-center text-[10px] mt-0.5 shrink-0"
              :class="modelValue.includes(ind.codigo) ? 'bg-blue-600 text-white font-bold' : 'border border-slate-300'"
            >
              <i v-if="modelValue.includes(ind.codigo)" class="pi pi-check text-[10px]"></i>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="font-bold truncate text-xs">{{ ind.titulo }}</span>
                <span v-if="ind.categoria" class="text-[9px] px-1 py-0.2 rounded bg-slate-100 text-slate-500 uppercase">
                  {{ ind.categoria }}
                </span>
              </div>
              <p class="text-[11px] text-slate-500 line-clamp-2 mt-0.5 leading-snug">
                {{ ind.instrucciones }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Listo" severity="primary" size="small" @click="isSelectorOpen = false" />
      </template>
    </Dialog>

    <!-- Modal Editar Texto de Instrucciones -->
    <Dialog
      v-model:visible="isEditTextoOpen"
      modal
      header="Personalizar Texto de Instrucciones para el Paciente"
      :style="{ width: '560px' }"
    >
      <div class="space-y-3">
        <p class="text-xs text-slate-500">
          Este es el texto que se incorporará en el correo electrónico de resolución y preparación que recibirá el paciente:
        </p>
        <Textarea v-model="textoManual" rows="7" class="w-full text-xs font-normal leading-relaxed" placeholder="Instrucciones al paciente..." />
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isEditTextoOpen = false" />
        <Button label="Guardar Texto" icon="pi pi-check" severity="primary" @click="saveEditTexto" />
      </template>
    </Dialog>
  </div>
</template>
