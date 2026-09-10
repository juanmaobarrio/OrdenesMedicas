<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdenesStore } from '../../stores/ordenes.store';
import { useAuthStore } from '../../stores/auth.store';
import { useFeaturesStore } from '../../stores/features.store';
import { usersService } from '../../services/users.service';
import { OrdenLlamadaPendienteItem, Sucursal, TipoLlamada } from '../../types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import Dropdown from 'primevue/dropdown';
import ToggleSwitch from 'primevue/toggleswitch';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import EmptyState from '../../components/common/EmptyState.vue';
import RegistrarLlamadaModal from '../../components/ordenes/RegistrarLlamadaModal.vue';
import { formatDateTime } from '../../utils/date';

const router = useRouter();
const ordenesStore = useOrdenesStore();
const authStore = useAuthStore();
const featuresStore = useFeaturesStore();

const sucursales = ref<Sucursal[]>([]);
const selectedSucursal = ref<string | undefined>(undefined);

// Control de ocultar llamadas con intento hace menos de 1 hora
const ocultarLlamadasRecientes = ref(true);

const parseDateUTC = (dateStr: string): number => {
  if (!dateStr) return 0;
  const hasTimezone = dateStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateStr);
  const safeStr = hasTimezone ? dateStr : `${dateStr}Z`;
  return new Date(safeStr).getTime();
};

const esLlamadaEnEspera = (item: OrdenLlamadaPendienteItem): boolean => {
  if (!item.cant_intentos_previos || item.cant_intentos_previos < 1 || !item.ultima_llamada_fecha) {
    return false;
  }
  const callTime = parseDateUTC(item.ultima_llamada_fecha);
  if (isNaN(callTime) || callTime === 0) return false;
  const now = Date.now();
  const diffMinutes = (now - callTime) / (1000 * 60);
  // Tolerancia de 2 minutos por eventual desfase horario local hasta 60 minutos
  return diffMinutes >= -2 && diffMinutes < 60;
};

const tiempoRestanteEspera = (item: OrdenLlamadaPendienteItem): string => {
  if (!item.ultima_llamada_fecha) return '';
  const callTime = parseDateUTC(item.ultima_llamada_fecha);
  const now = Date.now();
  const diffMinutes = Math.floor((now - callTime) / (1000 * 60));
  if (diffMinutes < 0) return 'Hace instantes (espera: 60m)';
  if (diffMinutes < 60) {
    const restante = Math.max(1, 60 - diffMinutes);
    return `Intento hace ${diffMinutes}m (espera: ${restante}m)`;
  }
  return `Hace ${diffMinutes}m`;
};

const llamadasFiltradas = computed(() => {
  const list = ordenesStore.llamadasPendientes;
  if (!ocultarLlamadasRecientes.value) {
    return list;
  }
  return list.filter((item) => !esLlamadaEnEspera(item));
});

const cantOcultasPorEspera = computed(() => {
  return ordenesStore.llamadasPendientes.filter(esLlamadaEnEspera).length;
});

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
  yaSeAtendio?: boolean;
  montoAbonadoAtencion?: number;
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
    yaSeAtendio: item.ya_se_atendio,
    montoAbonadoAtencion: item.monto_abonado_atencion,
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
        <!-- Switch Ocultar llamadas con intentos en la última hora -->
        <div class="flex items-center gap-2 bg-white py-1.5 px-3 rounded-xl border border-slate-300 shadow-2xs text-xs">
          <i class="pi pi-hourglass text-amber-600"></i>
          <span class="font-medium text-slate-700 select-none cursor-pointer" @click="ocultarLlamadasRecientes = !ocultarLlamadasRecientes">
            Ocultar con intento &lt; 1h
          </span>
          <ToggleSwitch v-model="ocultarLlamadasRecientes" />
        </div>

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

    <!-- Banner Informativo de Período de Espera (1 Hora) -->
    <div
      v-if="cantOcultasPorEspera > 0"
      class="p-3.5 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs transition shadow-2xs"
      :class="ocultarLlamadasRecientes ? 'bg-amber-50/80 border-amber-300 text-amber-950' : 'bg-blue-50/80 border-blue-200 text-blue-950'"
    >
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-2xs"
          :class="ocultarLlamadasRecientes ? 'bg-amber-200 text-amber-800' : 'bg-blue-200 text-blue-800'"
        >
          <i :class="ocultarLlamadasRecientes ? 'pi pi-clock' : 'pi pi-eye'" class="text-base"></i>
        </div>
        <div>
          <span v-if="ocultarLlamadasRecientes" class="font-bold">
            Hay {{ cantOcultasPorEspera }} llamada(s) en período de espera (último intento realizado hace menos de 1 hora).
          </span>
          <span v-else class="font-bold">
            Mostrando todas las llamadas (incluyendo las {{ cantOcultasPorEspera }} en período de espera).
          </span>
          <p class="text-[11px] opacity-80 mt-0.5">
            {{ ocultarLlamadasRecientes ? 'Se ocultan temporalmente para evitar reiterar llamados de forma inmediata.' : 'Las llamadas con intento reciente muestran el tiempo de espera restante en la columna de Intentos.' }}
          </p>
        </div>
      </div>

      <Button
        :label="ocultarLlamadasRecientes ? `Mostrar Todas (${ordenesStore.llamadasPendientes.length})` : 'Ocultar Recientes (< 1h)'"
        :icon="ocultarLlamadasRecientes ? 'pi pi-eye' : 'pi pi-eye-slash'"
        :severity="ocultarLlamadasRecientes ? 'warn' : 'secondary'"
        size="small"
        class="text-xs shrink-0 font-bold"
        @click="ocultarLlamadasRecientes = !ocultarLlamadasRecientes"
      />
    </div>

    <!-- Content -->
    <LoadingSpinner v-if="ordenesStore.isLoadingLlamadas" message="Cargando llamadas pendientes..." />

    <!-- Tabla con llamadas visibles -->
    <div v-else-if="llamadasFiltradas.length > 0" class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <DataTable
        :value="llamadasFiltradas"
        stripedRows
        responsiveLayout="scroll"
        class="p-datatable-sm"
      >
        <!-- Nro Orden -->
        <Column field="nro_orden" header="N° Orden" sortable>
          <template #body="{ data }">
            <div class="flex items-center space-x-1.5 flex-wrap gap-y-1">
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
              <span
                v-if="featuresStore.isAtencionPreviaEnabled && data.ya_se_atendio"
                class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 inline-flex items-center gap-0.5"
                :title="'PACIENTE YA SE ATENDIÓ. Abonó: $' + Number(data.monto_abonado_atencion || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })"
              >
                🩺 Ya se atendió
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
            <div class="flex items-center space-x-2 py-1 flex-wrap gap-y-1">
              <Tag
                :value="data.tipo_llamada_requerida === 'SOLICITUD_AUDITORIA' ? 'OBSERVACIÓN DEL AUDITOR' : 'AUDITORÍA FINALIZADA'"
                :severity="data.tipo_llamada_requerida === 'SOLICITUD_AUDITORIA' ? 'danger' : 'success'"
                class="text-[10px]"
              />
              <span
                v-if="featuresStore.isAtencionPreviaEnabled && data.ya_se_atendio"
                class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-amber-500 text-white inline-flex items-center gap-1 shadow-xs"
                title="Avisar que debe venir a buscar reintegro"
              >
                <i class="pi pi-wallet text-[9px]"></i> REINTEGRO PENDIENTE
              </span>
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
        <Column field="cant_intentos_previos" header="Intentos" sortable style="min-width: 140px">
          <template #body="{ data }">
            <div class="space-y-1">
              <span
                class="px-2 py-0.5 rounded text-xs font-semibold inline-block"
                :class="data.cant_intentos_previos > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'"
              >
                {{ data.cant_intentos_previos }} intento(s)
              </span>

              <div
                v-if="esLlamadaEnEspera(data)"
                class="text-[10px] text-amber-800 font-bold flex items-center gap-1 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-300 w-fit"
                title="Llamada realizada hace menos de 1 hora"
              >
                <i class="pi pi-hourglass text-[10px] text-amber-600"></i>
                <span>{{ tiempoRestanteEspera(data) }}</span>
              </div>
            </div>
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

    <!-- Estado si hay llamadas en la bandeja pero todas están en período de espera de 1 hora -->
    <div
      v-else-if="cantOcultasPorEspera > 0"
      class="p-8 bg-white rounded-xl border border-amber-200 shadow-sm text-center space-y-4"
    >
      <div class="w-14 h-14 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center mx-auto text-2xl">
        <i class="pi pi-hourglass"></i>
      </div>
      <div class="space-y-1">
        <h3 class="text-base font-bold text-slate-800">
          Todas las llamadas pendientes están en período de espera
        </h3>
        <p class="text-xs text-slate-500 max-w-md mx-auto">
          Hay {{ cantOcultasPorEspera }} llamada(s) con un intento realizado hace menos de 1 hora. Están ocultas para evitar reiterar llamadas inmediatamente.
        </p>
      </div>
      <Button
        label="Mostrar las llamadas en período de espera"
        icon="pi pi-eye"
        severity="warn"
        size="small"
        @click="ocultarLlamadasRecientes = false"
      />
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
        <!-- ALERTA IMPORTANTE: PACIENTE YA SE ATENDIÓ - DEBE BUSCAR REINTEGRO (Feature Flag) -->
        <div
          v-if="featuresStore.isAtencionPreviaEnabled && selectedOrdenParaObs.ya_se_atendio"
          class="p-3.5 bg-amber-50 border-2 border-amber-400 rounded-xl text-amber-950 text-xs space-y-1.5 shadow-sm"
        >
          <div class="flex items-center justify-between font-extrabold text-xs uppercase tracking-wide text-amber-900">
            <span class="flex items-center gap-1.5">
              <i class="pi pi-exclamation-circle text-amber-600 text-base animate-pulse"></i>
              ¡ATENCIÓN: EL PACIENTE YA SE ATENDIÓ!
            </span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-200 text-amber-900 border border-amber-300">
              Abonó al atenderse: ${{ Number(selectedOrdenParaObs.monto_abonado_atencion || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
            </span>
          </div>
          <p class="font-bold text-[11px] text-amber-950 leading-tight">
            📢 <strong>Pauta de llamada:</strong> No indicarle que puede venir a atenderse cuando quiera; informarle que su auditoría médica finalizó y que <strong>debe acercarse a retirar su reintegro</strong> económico si corresponde.
          </p>
        </div>

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
          <p v-if="!featuresStore.isAtencionPreviaEnabled || !selectedOrdenParaObs.ya_se_atendio" class="text-[11px] text-blue-700 italic">
            * Indicar al paciente que su trámite está finalizado y puede acercarse al laboratorio para realizarse los estudios.
          </p>
          <p v-else class="text-[11px] text-amber-900 font-bold bg-amber-100/90 p-2 rounded-lg border border-amber-300">
            * ¡El paciente ya se atendió! Comunicarle la resolución e informarle que pase a retirar su reintegro económico correspondiente.
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
              Emitida el {{ formatDateTime(sol.created_at) }}
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
      :yaSeAtendio="featuresStore.isAtencionPreviaEnabled && selectedOrden.yaSeAtendio"
      :montoAbonadoAtencion="selectedOrden.montoAbonadoAtencion"
      @success="loadData"
    />
  </div>
</template>
