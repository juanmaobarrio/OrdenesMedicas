<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import Tag from 'primevue/tag';
import { OrdenMedicaDetail, OrdenMedicaListItem, EstudioDetalleItem } from '../../types/ordenes';

interface ItemCalculadora {
  codigo?: string | null;
  nombre: string;
  precio: number;
  autorizado: boolean;
  seleccionado: boolean;
}

const props = defineProps<{
  visible: boolean;
  orden: OrdenMedicaDetail | OrdenMedicaListItem | null;
}>();

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
}>();

const items = ref<ItemCalculadora[]>([]);

const formatCurrency = (val: number | undefined | null) => {
  const num = Number(val || 0);
  return num.toLocaleString('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const inicializarCalculadora = () => {
  if (!props.orden) {
    items.value = [];
    return;
  }

  // 1. Si la orden tiene desglose detallado (estudios_detalle)
  if (props.orden.estudios_detalle && props.orden.estudios_detalle.length > 0) {
    items.value = props.orden.estudios_detalle.map((e: EstudioDetalleItem) => ({
      codigo: e.codigo || null,
      nombre: e.nombre,
      precio: Number(e.precio || 0),
      autorizado: Boolean(e.autorizado),
      seleccionado: true, // Por defecto todos seleccionados
    }));
    return;
  }

  // 2. Fallback de compatibilidad con listas de nombres anteriores
  const itemsGenerados: ItemCalculadora[] = [];
  const auts = props.orden.estudios_autorizados || [];
  const noAuts = props.orden.estudios_no_autorizados || [];

  auts.forEach((nombre) => {
    if (nombre && nombre.trim()) {
      itemsGenerados.push({
        codigo: null,
        nombre: nombre.trim(),
        precio: 0,
        autorizado: true,
        seleccionado: true,
      });
    }
  });

  const montoNoAutTotal = Number(props.orden.valor_estudios_no_autorizados || 0);
  const precioUnitarioEstimado = noAuts.length > 0 ? montoNoAutTotal / noAuts.length : 0;

  noAuts.forEach((nombre) => {
    if (nombre && nombre.trim()) {
      itemsGenerados.push({
        codigo: null,
        nombre: nombre.trim(),
        precio: precioUnitarioEstimado,
        autorizado: false,
        seleccionado: true,
      });
    }
  });

  items.value = itemsGenerados;
};

// Reinicializar siempre al abrir el modal (el estado efímero se resetea)
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      inicializarCalculadora();
    }
  }
);

// Cálculos reactivos en tiempo real
const copago = computed(() => Number(props.orden?.valor_copago || 0));
const apb = computed(() => {
  if (!props.orden) return 0;
  return props.orden.abona_apb ? Number(props.orden.valor_apb || 0) : 0;
});

const subtotalNoAutorizados = computed(() => {
  return items.value
    .filter((i) => !i.autorizado && i.seleccionado)
    .reduce((sum, curr) => sum + (Number(curr.precio) || 0), 0);
});

const totalEstimado = computed(() => {
  return copago.value + apb.value + subtotalNoAutorizados.value;
});

const totalEstudios = computed(() => items.value.length);
const totalAutorizados = computed(() => items.value.filter((i) => i.autorizado).length);
const totalNoAutorizados = computed(() => items.value.filter((i) => !i.autorizado).length);
const totalNoAutorizadosSeleccionados = computed(
  () => items.value.filter((i) => !i.autorizado && i.seleccionado).length
);

const todosNoAutSeleccionados = computed(() => {
  const noAuts = items.value.filter((i) => !i.autorizado);
  if (noAuts.length === 0) return true;
  return noAuts.every((i) => i.seleccionado);
});

const toggleTodosNoAutorizados = () => {
  const nuevoEstado = !todosNoAutSeleccionados.value;
  items.value.forEach((item) => {
    if (!item.autorizado) {
      item.seleccionado = nuevoEstado;
    }
  });
};

const restablecer = () => {
  inicializarCalculadora();
};

const cerrar = () => {
  emit('update:visible', false);
};
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :style="{ width: '92vw', maxWidth: '800px' }"
    :contentStyle="{ padding: '1.25rem' }"
    :closable="true"
    @update:visible="emit('update:visible', $event)"
  >
    <template #header>
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center shadow-sm">
          <i class="pi pi-calculator text-lg"></i>
        </div>
        <div>
          <h3 class="text-base font-bold text-slate-800 leading-tight">
            Calculadora de Presupuesto de Estudios
          </h3>
          <p class="text-xs text-slate-500">
            Simulador interactivo en tiempo real para cotización y consulta con el paciente
          </p>
        </div>
      </div>
    </template>

    <div v-if="orden" class="space-y-4 pt-1">
      <!-- Ficha de Referencia Rápida -->
      <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block">Paciente</span>
          <span class="font-bold text-slate-800 truncate block" :title="orden.paciente?.nombre_completo">
            {{ orden.paciente?.nombre_completo || 'S/D' }}
          </span>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block">Obra Social / Mutual</span>
          <span class="font-semibold text-slate-700 truncate block">
            {{ orden.mutual || 'S/D' }}
          </span>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block">N° Afiliado</span>
          <span class="font-medium text-slate-600 block">
            {{ orden.nro_afiliado || 'Sin credencial' }}
          </span>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block">Orden</span>
          <span class="font-mono font-bold text-blue-700 block">
            {{ orden.nro_orden }}
          </span>
        </div>
      </div>

      <!-- Resumen de Cantidades y Acciones Rápidas -->
      <div class="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div class="flex items-center space-x-2">
          <Tag severity="info" :value="`${totalEstudios} Estudios`" class="text-[11px]" />
          <Tag severity="success" :value="`${totalAutorizados} Autorizados`" class="text-[11px]" />
          <Tag
            :severity="totalNoAutorizados > 0 ? 'danger' : 'secondary'"
            :value="`${totalNoAutorizados} No Autorizados`"
            class="text-[11px]"
          />
        </div>

        <div v-if="totalNoAutorizados > 0" class="flex items-center space-x-2">
          <Button
            :label="todosNoAutSeleccionados ? 'Deseleccionar No Aut.' : 'Seleccionar Todos'"
            :icon="todosNoAutSeleccionados ? 'pi pi-filter-slash' : 'pi pi-check-square'"
            text
            size="small"
            class="text-xs p-1"
            severity="secondary"
            @click="toggleTodosNoAutorizados"
          />
          <Button
            label="Restablecer"
            icon="pi pi-refresh"
            text
            size="small"
            class="text-xs p-1"
            severity="secondary"
            @click="restablecer"
          />
        </div>
      </div>

      <!-- Listado de Estudios Interactivo -->
      <div class="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
        <div class="bg-slate-100/70 px-3 py-2 border-b border-slate-200 flex items-center text-[11px] font-bold text-slate-600 uppercase tracking-wider">
          <div class="w-12 text-center">Incluir</div>
          <div class="w-20 pl-2 hidden sm:block">Código</div>
          <div class="flex-1">Práctica / Estudio</div>
          <div class="w-32 text-center">Estado</div>
          <div class="w-24 text-right">Precio ($)</div>
        </div>

        <!-- Sin estudios cargados -->
        <div v-if="items.length === 0" class="p-8 text-center space-y-2">
          <div class="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
            <i class="pi pi-info-circle text-2xl"></i>
          </div>
          <p class="text-sm font-semibold text-slate-700">Esta orden médica no posee estudios cargados</p>
          <p class="text-xs text-slate-400 max-w-md mx-auto">
            Puedes cargar o editar los estudios de la orden mediante el sistema o enviar la información por API/n8n.
          </p>
        </div>

        <!-- Filas de Estudios -->
        <div v-else class="divide-y divide-slate-100 max-h-52 overflow-y-auto">
          <div
            v-for="(item, idx) in items"
            :key="idx"
            class="px-3 py-2.5 flex items-center hover:bg-slate-50 transition text-xs"
            :class="{
              'bg-emerald-50/30': item.autorizado,
              'bg-rose-50/20': !item.autorizado && item.seleccionado,
              'opacity-60 bg-slate-50/50': !item.autorizado && !item.seleccionado,
            }"
          >
            <!-- Checkbox -->
            <div class="w-10 flex justify-center">
              <!-- Autorizado: Siempre seleccionado y deshabilitado (cubierto) -->
              <Checkbox
                v-if="item.autorizado"
                :modelValue="true"
                disabled
                binary
                title="Estudio autorizado por la mutual (100% cubierto)"
              />
              <!-- No Autorizado: Habilitado para sumar o excluir -->
              <Checkbox
                v-else
                v-model="item.seleccionado"
                binary
                :title="item.seleccionado ? 'Desmarcar para excluir del presupuesto' : 'Marcar para sumar al presupuesto'"
              />
            </div>

            <!-- Código -->
            <div class="w-20 hidden sm:block font-mono text-[11px] text-slate-500 font-semibold">
              {{ item.codigo || '-' }}
            </div>

            <!-- Nombre de la Práctica -->
            <div class="flex-1 pr-2">
              <span
                class="font-medium text-slate-800"
                :class="{
                  'text-slate-500 line-through': !item.autorizado && !item.seleccionado,
                }"
              >
                {{ item.nombre }}
              </span>
            </div>

            <!-- Badge de Estado -->
            <div class="w-32 text-center">
              <span
                v-if="item.autorizado"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200"
              >
                <i class="pi pi-check text-[9px] mr-1"></i> Autorizado
              </span>
              <span
                v-else
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200"
              >
                <i class="pi pi-times text-[9px] mr-1"></i> No Autorizado
              </span>
            </div>

            <!-- Precio -->
            <div class="w-24 text-right font-mono">
              <span v-if="item.autorizado" class="text-emerald-700 font-semibold text-[11px]">
                $ 0.00
              </span>
              <span
                v-else
                class="font-bold text-xs"
                :class="item.seleccionado ? 'text-rose-600' : 'text-slate-400 line-through'"
              >
                ${{ formatCurrency(item.precio) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel de Totales y Liquidación Dinámica -->
      <div class="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-3 shadow-md space-y-2.5">
        <div class="flex items-center justify-between border-b border-slate-700/80 pb-1.5">
          <span class="text-[11px] uppercase font-bold text-slate-300 tracking-wider">
            Desglose de Presupuesto Estimado
          </span>
          <span class="text-[10px] text-slate-400">
            Valores en pesos argentinos (ARS)
          </span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
          <!-- Copago Mutual -->
          <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700/60">
            <span class="text-slate-400 text-[10px] block">Copago Obra Social:</span>
            <span class="text-sm font-bold text-white font-mono">
              ${{ formatCurrency(copago) }}
            </span>
          </div>

          <!-- Acto Bioquímico (APB) -->
          <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700/60">
            <span class="text-slate-400 text-[10px] block">Acto Bioquímico (APB):</span>
            <div class="flex items-center space-x-1">
              <span class="text-sm font-bold font-mono" :class="orden.abona_apb ? 'text-amber-400' : 'text-slate-400'">
                ${{ formatCurrency(apb) }}
              </span>
              <span v-if="!orden.abona_apb" class="text-[9px] text-slate-400">(no aplica)</span>
            </div>
          </div>

          <!-- Estudios Particulares Seleccionados -->
          <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700/60">
            <span class="text-slate-400 text-[10px] block">
              Prácticas No Aut. ({{ totalNoAutorizadosSeleccionados }}/{{ totalNoAutorizados }}):
            </span>
            <span class="text-sm font-bold text-rose-400 font-mono">
              ${{ formatCurrency(subtotalNoAutorizados) }}
            </span>
          </div>
        </div>

        <!-- Total Final a Abonar -->
        <div class="bg-slate-950/80 rounded-lg p-2.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border border-blue-500/30">
          <div>
            <span class="text-[11px] uppercase font-bold text-blue-400 tracking-wider">
              Total Estimado a Abonar por el Paciente
            </span>
            <p class="text-[10px] text-slate-400">
              Copago + APB + Prácticas No Autorizadas seleccionadas
            </p>
          </div>
          <div class="text-right">
            <span class="text-xl sm:text-2xl font-black text-emerald-400 font-mono">
              ${{ formatCurrency(totalEstimado) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Pie de Diálogo y Nota Aclaratoria -->
      <div class="flex items-center justify-between pt-2 border-t border-slate-100">
        <span class="text-[11px] text-slate-500 flex items-center">
          <i class="pi pi-info-circle text-blue-500 mr-1.5 text-xs"></i>
          Simulador efímero en memoria (no modifica los importes guardados de la orden)
        </span>
        <Button
          label="Cerrar Calculadora"
          icon="pi pi-times"
          severity="secondary"
          size="small"
          @click="cerrar"
        />
      </div>
    </div>
  </Dialog>
</template>
