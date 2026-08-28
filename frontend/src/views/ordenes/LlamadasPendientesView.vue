<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdenesStore } from '../../stores/ordenes.store';
import { useAuthStore } from '../../stores/auth.store';
import { usersService } from '../../services/users.service';
import { OrdenLlamadaPendienteItem, Sucursal, TipoLlamada } from '../../types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import Dropdown from 'primevue/dropdown';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import EmptyState from '../../components/common/EmptyState.vue';
import RegistrarLlamadaModal from '../../components/ordenes/RegistrarLlamadaModal.vue';

const router = useRouter();
const ordenesStore = useOrdenesStore();
const authStore = useAuthStore();

const sucursales = ref<Sucursal[]>([]);
const selectedSucursal = ref<string | undefined>(undefined);

// Modal state
const isModalVisible = ref(false);
const isObservacionesModalVisible = ref(false);
const selectedOrdenParaObs = ref<OrdenLlamadaPendienteItem | null>(null);
const selectedOrden = ref<{
  id: string;
  nroOrden: string;
  pacienteNombre: string;
  telefono?: string | null;
  tipoLlamada: TipoLlamada;
} | null>(null);

const handleOpenObservacionesModal = (item: OrdenLlamadaPendienteItem) => {
  selectedOrdenParaObs.value = item;
  isObservacionesModalVisible.value = true;
};

const loadData = async () => {
  if (authStore.isAdmin) {
    sucursales.value = await usersService.listSucursales();
  }
  await ordenesStore.fetchLlamadasPendientes(selectedSucursal.value);
};

onMounted(() => {
  loadData();
});

const handleOpenLlamadaModal = (item: OrdenLlamadaPendienteItem) => {
  selectedOrden.value = {
    id: item.id,
    nroOrden: item.nro_orden,
    pacienteNombre: item.paciente_nombre,
    telefono: item.contacto_telefono || item.contacto_celular || item.paciente_telefono,
    tipoLlamada: item.tipo_llamada_requerida,
  };
  isModalVisible.value = true;
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <span>Bandeja de Llamadas a Pacientes</span>
          <span
            v-if="ordenesStore.llamadasPendientes.length > 0"
            class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700"
          >
            {{ ordenesStore.llamadasPendientes.length }} pendientes
          </span>
        </h2>
        <p class="text-sm text-slate-500">
          Pacientes con órdenes en observación del auditor o con auditoría aprobada listos para ser notificados
        </p>
      </div>

      <div class="flex items-center space-x-3">
        <Dropdown
          v-if="authStore.isAdmin"
          v-model="selectedSucursal"
          :options="sucursales"
          optionLabel="nombre"
          optionValue="id"
          placeholder="Todas las sucursales"
          showClear
          @change="loadData"
          class="w-56"
        />
        <Button
          icon="pi pi-refresh"
          severity="secondary"
          rounded
          text
          :loading="ordenesStore.isLoadingLlamadas"
          @click="loadData"
          title="Recargar"
        />
      </div>
    </div>

    <!-- Content -->
    <LoadingSpinner v-if="ordenesStore.isLoadingLlamadas" message="Cargando llamadas pendientes..." />

    <div v-else-if="ordenesStore.llamadasPendientes.length > 0" class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <DataTable
        :value="ordenesStore.llamadasPendientes"
        stripedRows
        responsiveLayout="scroll"
        class="p-datatable-sm"
      >
        <!-- Nro Orden -->
        <Column field="nro_orden" header="N° Orden" sortable>
          <template #body="{ data }">
            <div class="flex items-center space-x-1.5">
              <router-link
                :to="`/ordenes/${data.id}`"
                class="font-mono text-xs font-bold text-blue-600 hover:underline"
              >
                {{ data.nro_orden }}
              </router-link>
              <span
                v-if="data.debe_orden_medica"
                class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 inline-flex items-center gap-0.5"
                title="¡ATENCIÓN! El paciente DEBE la orden médica física"
              >
                <i class="pi pi-exclamation-triangle text-[10px]"></i> Debe receta
              </span>
            </div>
          </template>
        </Column>

        <!-- Paciente & Contacto -->
        <Column header="Paciente / Contacto">
          <template #body="{ data }">
            <div>
              <p class="text-sm font-semibold text-slate-800">{{ data.paciente_nombre }}</p>
              <p class="text-xs text-slate-500">DNI: {{ data.paciente_documento }} &bull; {{ data.mutual }}</p>
              <p class="text-xs text-blue-700 font-medium mt-0.5 flex items-center gap-1">
                <i class="pi pi-phone text-[10px]"></i>
                {{ data.contacto_telefono || data.contacto_celular || data.paciente_telefono || 'Sin teléfono' }}
                <span v-if="data.contacto_horario" class="text-slate-400 font-normal">({{ data.contacto_horario }})</span>
              </p>

            </div>
          </template>
        </Column>

        <!-- Tipo de Aviso & Boton Observaciones -->
        <Column header="Motivo del Aviso" style="min-width: 280px">
          <template #body="{ data }">
            <div class="flex items-center space-x-2 py-1">
              <Tag
                :value="data.tipo_llamada_requerida === 'SOLICITUD_AUDITORIA' ? 'OBSERVACIÓN DEL AUDITOR' : 'AUDITORÍA FINALIZADA'"
                :severity="data.tipo_llamada_requerida === 'SOLICITUD_AUDITORIA' ? 'danger' : 'success'"
                class="text-[10px]"
              />
              <Button
                icon="pi pi-comments"
                label="Ver Observaciones"
                text
                size="small"
                severity="info"
                class="text-xs p-1 font-semibold text-blue-600 hover:text-blue-800"
                @click="handleOpenObservacionesModal(data)"
                title="Abrir ventana con las observaciones"
              />
            </div>
          </template>
        </Column>

        <!-- Sucursal -->
        <Column field="sucursal_nombre" header="Sucursal" sortable style="width: 120px" />

        <!-- Intentos Previos -->
        <Column field="cant_intentos_previos" header="Intentos" sortable style="width: 100px">
          <template #body="{ data }">
            <span
              class="px-2 py-0.5 rounded text-xs font-semibold"
              :class="data.cant_intentos_previos > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'"
            >
              {{ data.cant_intentos_previos }} intentos
            </span>
          </template>
        </Column>

        <!-- Acciones -->
        <Column header="Acciones" style="width: 200px" alignFrozen="right" frozen>
          <template #body="{ data }">
            <div class="flex items-center space-x-1.5">
              <Button
                icon="pi pi-window-maximize"
                text
                rounded
                size="small"
                severity="secondary"
                class="text-slate-500 hover:text-blue-600"
                @click="router.push(`/ordenes/${data.id}`)"
                title="Abrir expediente en pantalla completa"
              />
              <Button
                label="Llamar"
                icon="pi pi-phone"
                size="small"
                severity="primary"
                @click="handleOpenLlamadaModal(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <EmptyState
      v-else
      title="¡Excelente! No hay llamadas pendientes"
      description="Todos los pacientes con observaciones o auditorías finalizadas ya han sido contactados."
      icon="pi pi-check-circle"
    />

    <!-- Modal Popup: Observaciones de la Orden Médica -->
    <Dialog
      v-model:visible="isObservacionesModalVisible"
      modal
      :header="`Observaciones y Notas - Orden N° ${selectedOrdenParaObs?.nro_orden || ''}`"
      :style="{ width: '560px' }"
    >
      <div v-if="selectedOrdenParaObs" class="space-y-4 text-xs">
        <!-- ALERTA IMPORTANTE: DEBE RECETA MEDICA FISICA -->
        <div
          v-if="selectedOrdenParaObs.debe_orden_medica"
          class="p-3 bg-red-100 border-2 border-red-400 rounded-xl text-red-900 text-xs space-y-1 shadow-sm"
        >
          <div class="flex items-center gap-1.5 text-red-900 font-extrabold text-xs uppercase tracking-wide">
            <i class="pi pi-exclamation-triangle text-red-600 text-base animate-pulse"></i>
            <span>¡ALERTA: EL PACIENTE DEBE LA ORDEN MÉDICA FÍSICA!</span>
          </div>
          <p class="font-semibold text-[11px] text-red-800 leading-tight pl-5">
            Recordarle obligatoriamente durante la llamada que debe traer la receta médica física original el día de la toma de muestra.
          </p>
        </div>

        <!-- Ficha de Contacto Rápida -->
        <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 grid grid-cols-2 gap-2">
          <div>
            <p class="text-[10px] font-bold text-slate-400 uppercase">Paciente</p>
            <p class="font-bold text-slate-800 text-sm">{{ selectedOrdenParaObs.paciente_nombre }}</p>
            <p class="text-slate-500">DNI: {{ selectedOrdenParaObs.paciente_documento }}</p>
          </div>
          <div>
            <p class="text-[10px] font-bold text-slate-400 uppercase">Mutual & Sede</p>
            <p class="font-semibold text-slate-800">{{ selectedOrdenParaObs.mutual }}</p>
            <p class="text-slate-500">{{ selectedOrdenParaObs.sucursal_nombre }}</p>
          </div>
          <div class="col-span-2 pt-1 border-t border-slate-200 flex items-center justify-between text-blue-900">
            <span class="font-semibold flex items-center gap-1">
              <i class="pi pi-phone text-blue-600"></i>
              {{ selectedOrdenParaObs.contacto_telefono || selectedOrdenParaObs.contacto_celular || selectedOrdenParaObs.paciente_telefono || 'Sin teléfono' }}
            </span>
            <span v-if="selectedOrdenParaObs.contacto_horario" class="text-slate-500 italic">
              Horario: {{ selectedOrdenParaObs.contacto_horario }}
            </span>
          </div>
        </div>

        <!-- 1. Si la auditoría está finalizada: mostrar resultado de auditoría -->
        <div
          v-if="selectedOrdenParaObs.tipo_llamada_requerida === 'AUDITORIA_FINALIZADA' || selectedOrdenParaObs.observacion_resultado_auditoria"
          class="p-3.5 bg-blue-50/70 rounded-xl border border-blue-200 space-y-1.5"
        >
          <div class="flex items-center gap-1.5 text-blue-900 font-bold text-xs uppercase tracking-wide">
            <i class="pi pi-check-circle text-blue-600"></i>
            <span>Resultado de la Auditoría</span>
          </div>
          <p class="text-slate-800 font-medium text-xs leading-relaxed bg-white p-2.5 rounded-lg border border-blue-100">
            {{ selectedOrdenParaObs.observacion_resultado_auditoria || selectedOrdenParaObs.motivo_aviso }}
          </p>
          <p class="text-[11px] text-blue-700 italic">
            * Indicar al paciente que su trámite está finalizado y puede acercarse al laboratorio para realizarse los estudios.
          </p>
        </div>

        <!-- 2. Observaciones del auditor pendientes -->
        <div
          v-if="selectedOrdenParaObs.solicitudes_pendientes && selectedOrdenParaObs.solicitudes_pendientes.length > 0"
          class="space-y-2.5"
        >
          <p class="text-[11px] font-bold text-amber-900 uppercase tracking-wide flex items-center gap-1">
            <i class="pi pi-exclamation-circle text-amber-600"></i>
            <span>Observaciones del Auditor ({{ selectedOrdenParaObs.solicitudes_pendientes.length }})</span>
          </p>
          <div
            v-for="sol in selectedOrdenParaObs.solicitudes_pendientes"
            :key="sol.id"
            class="p-3 bg-amber-50/80 rounded-xl border border-amber-200 space-y-1.5"
          >
            <div class="flex items-center justify-between font-bold text-amber-900 text-xs">
              <span>{{ sol.motivo_solicitud }}</span>
              <span v-if="sol.auditor" class="text-[10px] text-amber-700 font-normal">Dr/a. {{ sol.auditor.full_name }}</span>
            </div>
            <p class="text-slate-700 bg-white p-2.5 rounded-lg border border-amber-100 font-medium leading-relaxed">
              {{ sol.mensaje_auditor }}
            </p>
            <p class="text-[10px] text-slate-400">
              Emitida el {{ sol.created_at.slice(0, 16).replace('T', ' ') }}
            </p>
          </div>
        </div>

        <!-- 3. Observaciones de Ingreso -->
        <div v-if="selectedOrdenParaObs.observaciones_ingreso" class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
          <p class="text-[10px] font-bold text-slate-500 uppercase tracking-wide flex items-center gap-1">
            <i class="pi pi-info-circle text-slate-400"></i> Observaciones de Ingreso
          </p>
          <p class="text-slate-700 italic bg-white p-2 rounded border border-slate-100">
            "{{ selectedOrdenParaObs.observaciones_ingreso }}"
          </p>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between w-full">
          <Button
            label="Ver Pantalla Completa"
            icon="pi pi-window-maximize"
            text
            size="small"
            severity="secondary"
            @click="isObservacionesModalVisible = false; router.push(`/ordenes/${selectedOrdenParaObs?.id}`)"
          />
          <div class="space-x-2">
            <Button
              label="Cerrar"
              text
              severity="secondary"
              size="small"
              @click="isObservacionesModalVisible = false"
            />
            <Button
              label="Llamar al Paciente"
              icon="pi pi-phone"
              size="small"
              severity="primary"
              @click="isObservacionesModalVisible = false; handleOpenLlamadaModal(selectedOrdenParaObs!)"
            />
          </div>
        </div>
      </template>
    </Dialog>

    <!-- Modal para registrar llamada -->
    <RegistrarLlamadaModal
      v-if="selectedOrden"
      v-model:visible="isModalVisible"
      :ordenId="selectedOrden.id"
      :nroOrden="selectedOrden.nroOrden"
      :pacienteNombre="selectedOrden.pacienteNombre"
      :telefono="selectedOrden.telefono"
      :tipoLlamada="selectedOrden.tipoLlamada"
      @success="loadData"
    />
  </div>
</template>
