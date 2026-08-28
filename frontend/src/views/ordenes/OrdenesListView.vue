<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useOrdenesStore } from '../../stores/ordenes.store';
import { useAuthStore } from '../../stores/auth.store';
import { usersService } from '../../services/users.service';
import { EstadoOrden, OrdenMedicaListItem, Sucursal } from '../../types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import StatusTag from '../../components/common/StatusTag.vue';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import EmptyState from '../../components/common/EmptyState.vue';
import OrdenDetailPanel from '../../components/ordenes/OrdenDetailPanel.vue';
import { formatDate } from '../../utils/date';

const route = useRoute();
const router = useRouter();
const ordenesStore = useOrdenesStore();
const authStore = useAuthStore();

const sucursales = ref<Sucursal[]>([]);
const searchInput = ref('');
const selectedOrdenId = ref<string | null>(null);

const opcionesEstados: { label: string; value: EstadoOrden }[] = [
  { label: 'Ingreso', value: 'Ingreso' },
  { label: 'En Auditoría', value: 'en Auditoria' },
  { label: 'Solicitudes de Auditoría', value: 'Solicitudes de auditoria' },
  { label: 'Actualizada', value: 'Actualizada' },
  { label: 'Auditoría Finalizada', value: 'Auditoria Finalizada' },
  { label: 'Dar de baja', value: 'Dar de baja' },
  { label: 'Cancelada', value: 'Cancelada' },
  { label: 'Cerrada', value: 'Cerrada' },
];

onMounted(async () => {
  if (authStore.isAdmin) {
    sucursales.value = await usersService.listSucursales();
  }
  await ordenesStore.fetchOrdenes();

  // Si viene con parametro en URL (ej: /ordenes/:id o ?id=...)
  if (route.params.id) {
    selectedOrdenId.value = route.params.id as string;
  }
});

watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      selectedOrdenId.value = newId as string;
    }
  }
);

const handleSelectOrden = (orden: OrdenMedicaListItem) => {
  selectedOrdenId.value = orden.id;
};

const handleSearch = () => {
  ordenesStore.filters.search = searchInput.value.trim() || undefined;
  ordenesStore.filters.skip = 0;
  ordenesStore.fetchOrdenes();
};

const handleResetFilters = () => {
  searchInput.value = '';
  ordenesStore.filters.search = undefined;
  ordenesStore.filters.estado = undefined;
  ordenesStore.filters.sucursal_id = undefined;
  ordenesStore.filters.skip = 0;
  ordenesStore.fetchOrdenes();
};

const handlePageChange = (event: any) => {
  ordenesStore.filters.skip = event.first;
  ordenesStore.filters.limit = event.rows;
  ordenesStore.fetchOrdenes();
};
</script>

<template>
  <div class="space-y-4">
    <!-- Header & Action -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Órdenes Médicas</h2>
        <p class="text-xs text-slate-500">Gestión de prescripciones, seguimiento de estados y auditorías clínicas</p>
      </div>

      <div class="flex items-center space-x-2">
        <Button
          v-if="selectedOrdenId"
          label="Ver Pantalla Completa"
          icon="pi pi-window-maximize"
          outlined
          severity="primary"
          size="small"
          class="text-xs"
          @click="router.push(`/ordenes/${selectedOrdenId}`)"
          title="Abrir orden médica a pantalla completa"
        />
        <Button
          v-if="selectedOrdenId"
          label="Cerrar Detalle"
          icon="pi pi-times"
          text
          severity="secondary"
          size="small"
          class="text-xs"
          @click="selectedOrdenId = null"
        />
        <router-link to="/ordenes/nueva">
          <Button label="Nueva Orden" icon="pi pi-plus" severity="primary" size="small" />
        </router-link>
      </div>
    </div>

    <!-- Filter Bar (Compact) -->
    <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-2">
      <!-- Search Input -->
      <div class="flex-1 min-w-[200px]">
        <span class="p-input-icon-left w-full">
          <i class="pi pi-search text-slate-400 text-xs"></i>
          <InputText
            v-model="searchInput"
            placeholder="Buscar por N° Orden, DNI o Paciente..."
            class="w-full text-xs"
            @keyup.enter="handleSearch"
          />
        </span>
      </div>

      <!-- Estado Filter -->
      <Dropdown
        v-model="ordenesStore.filters.estado"
        :options="opcionesEstados"
        optionLabel="label"
        optionValue="value"
        placeholder="Todos los estados"
        showClear
        class="w-44 text-xs"
        @change="ordenesStore.fetchOrdenes"
      />

      <!-- Sucursal Filter (Admin) -->
      <Dropdown
        v-if="authStore.isAdmin"
        v-model="ordenesStore.filters.sucursal_id"
        :options="sucursales"
        optionLabel="nombre"
        optionValue="id"
        placeholder="Todas las sucursales"
        showClear
        class="w-44 text-xs"
        @change="ordenesStore.fetchOrdenes"
      />

      <Button icon="pi pi-filter" label="Buscar" size="small" class="text-xs" @click="handleSearch" />
      <Button icon="pi pi-times" severity="secondary" text rounded size="small" @click="handleResetFilters" title="Limpiar filtros" />
    </div>

    <!-- Main Layout: Full or Split View -->
    <LoadingSpinner v-if="ordenesStore.isLoading && ordenesStore.items.length === 0" message="Cargando órdenes médicas..." />

    <div v-else-if="ordenesStore.items.length > 0" class="grid grid-cols-12 gap-4 items-start">
      <!-- Left Column: Master Table / List -->
      <div
        class="transition-all duration-300"
        :class="selectedOrdenId ? 'col-span-12 xl:col-span-5 2xl:col-span-4' : 'col-span-12'"
      >
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <DataTable
            :value="ordenesStore.items"
            lazy
            paginator
            :rows="ordenesStore.filters.limit || 50"
            :totalRecords="ordenesStore.total"
            :first="ordenesStore.filters.skip || 0"
            @page="handlePageChange"
            responsiveLayout="scroll"
            rowHover
            selectionMode="single"
            @row-click="handleSelectOrden($event.data)"
            class="p-datatable-sm cursor-pointer"
          >
            <!-- Nro Orden & Estado -->
            <Column header="Orden">
              <template #body="{ data }">
                <div
                  class="py-1 -my-1 -mx-2 px-2 rounded transition"
                  :class="selectedOrdenId === data.id ? 'bg-blue-50 border-l-4 border-blue-600 font-bold' : ''"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-1.5">
                      <span class="font-mono text-xs font-bold text-slate-800">{{ data.nro_orden }}</span>
                      <span
                        v-if="data.debe_orden_medica"
                        class="text-red-600 font-bold text-xs"
                        title="¡ATENCIÓN! El paciente DEBE la orden médica física (recibida digital/mail)"
                      >
                        <i class="pi pi-exclamation-triangle text-xs"></i>
                      </span>
                    </div>
                    <StatusTag :value="data.estado" />
                  </div>
                  <p class="text-xs font-semibold text-slate-700 truncate mt-1">{{ data.paciente?.nombre_completo }}</p>
                  <div class="flex items-center justify-between text-[11px] text-slate-500 mt-0.5">
                    <span>DNI: {{ data.paciente?.documento }}</span>
                    <span class="font-bold text-blue-700" title="Total a abonar: Copago + No autorizados">
                      Total: ${{ (Number(data.valor_copago || 0) + Number(data.valor_estudios_no_autorizados || 0)).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                    </span>
                  </div>
                </div>

              </template>
            </Column>

            <!-- Columnas adicionales sólo cuando NO está seleccionada una orden (pantalla completa) -->
            <Column v-if="!selectedOrdenId" field="mutual" header="Mutual" sortable class="text-xs">
              <template #body="{ data }">
                <div>
                  <span class="font-semibold text-slate-700">{{ data.mutual }}</span>
                  <p v-if="data.nro_afiliado" class="text-[11px] text-slate-500">Af: {{ data.nro_afiliado }}</p>
                </div>
              </template>
            </Column>
            <Column v-if="!selectedOrdenId" header="Valores ($)" class="text-xs">
              <template #body="{ data }">
                <div class="text-xs space-y-0.5">
                  <p class="font-bold text-slate-800">
                    Total: ${{ (Number(data.valor_copago || 0) + Number(data.valor_estudios_no_autorizados || 0)).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                  </p>
                  <p class="text-[11px] text-slate-500 flex items-center gap-2">
                    <span>Copago: ${{ Number(data.valor_copago || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</span>
                    <span v-if="Number(data.valor_estudios_no_autorizados || 0) > 0" class="text-amber-700 font-medium">
                      | No aut: ${{ Number(data.valor_estudios_no_autorizados).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
                    </span>
                  </p>
                </div>
              </template>
            </Column>
            <Column v-if="!selectedOrdenId" field="fecha_prescripcion" header="Prescripción" sortable class="text-xs">
              <template #body="{ data }">
                <span>{{ formatDate(data.fecha_prescripcion) }}</span>
              </template>
            </Column>
            <Column v-if="!selectedOrdenId" field="sucursal.nombre" header="Sucursal" sortable class="text-xs" />
            <Column v-if="!selectedOrdenId" header="Auditor">
              <template #body="{ data }">
                <span class="text-xs text-slate-600">{{ data.assigned_auditor?.full_name || 'Sin asignar' }}</span>
              </template>
            </Column>
            <Column v-if="!selectedOrdenId" header="Detalles">
              <template #body="{ data }">
                <div class="flex items-center space-x-2 text-xs">
                  <span v-if="data.cant_adjuntos > 0" class="text-slate-500 flex items-center gap-1">
                    <i class="pi pi-paperclip text-xs"></i> {{ data.cant_adjuntos }}
                  </span>
                  <span v-if="data.cant_solicitudes_pendientes > 0" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                    {{ data.cant_solicitudes_pendientes }} obs.
                  </span>
                </div>
              </template>
            </Column>

            <Column header="" style="width: 76px">
              <template #body="{ data }">
                <div class="flex items-center space-x-0.5">
                  <Button
                    :icon="selectedOrdenId === data.id ? 'pi pi-chevron-right' : 'pi pi-eye'"
                    text
                    rounded
                    size="small"
                    :severity="selectedOrdenId === data.id ? 'primary' : 'secondary'"
                    @click.stop="handleSelectOrden(data)"
                    :title="selectedOrdenId === data.id ? 'Seleccionada' : 'Ver en panel lateral'"
                  />
                  <Button
                    icon="pi pi-window-maximize"
                    text
                    rounded
                    size="small"
                    severity="secondary"
                    class="text-slate-400 hover:text-blue-600"
                    @click.stop="router.push(`/ordenes/${data.id}`)"
                    title="Ver en pantalla completa"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>

      <!-- Right Column: Detail Panel (Expediente) -->
      <div
        v-if="selectedOrdenId"
        class="col-span-12 xl:col-span-7 2xl:col-span-8 sticky top-4 h-[calc(100vh-140px)] min-h-[600px]"
      >
        <OrdenDetailPanel
          :ordenId="selectedOrdenId"
          @close="selectedOrdenId = null"
          @updated="ordenesStore.fetchOrdenes"
        />
      </div>
    </div>

    <EmptyState
      v-else
      title="No se encontraron órdenes médicas"
      description="Prueba ajustando los filtros de búsqueda o registra una nueva orden médica."
      icon="pi pi-search"
    >
      <template #action>
        <router-link to="/ordenes/nueva" class="mt-4">
          <Button label="Crear Primera Orden" icon="pi pi-plus" size="small" />
        </router-link>
      </template>
    </EmptyState>
  </div>
</template>

