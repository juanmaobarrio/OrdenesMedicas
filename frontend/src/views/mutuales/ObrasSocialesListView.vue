<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { mutualesService } from '../../services/mutuales.service';
import { ObraSocial, ObraSocialCreate, ObraSocialUpdate } from '../../types/mutuales';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Checkbox from 'primevue/checkbox';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import EmptyState from '../../components/common/EmptyState.vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const mutuales = ref<ObraSocial[]>([]);
const isLoading = ref(true);
const searchInput = ref('');
const filterOnlyActive = ref(false);

// Modal state
const isDialogVisible = ref(false);
const isEditing = ref(false);
const isSaving = ref(false);
const editingId = ref<string | null>(null);

const form = ref<ObraSocialCreate>({
  codigo: '',
  sigla: '',
  nombre: '',
  codigo_externo: '',
  dias_vencimiento: 30,
  copago_default: 0,
  activa: true,
});

const loadMutuales = async () => {
  isLoading.value = true;
  try {
    mutuales.value = await mutualesService.list(false);
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar las obras sociales',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadMutuales();
});

const filteredMutuales = computed(() => {
  let list = mutuales.value;
  if (filterOnlyActive.value) {
    list = list.filter((m) => m.activa);
  }
  const q = searchInput.value.trim().toLowerCase();
  if (q) {
    list = list.filter(
      (m) =>
        m.sigla.toLowerCase().includes(q) ||
        m.nombre.toLowerCase().includes(q) ||
        m.codigo.toLowerCase().includes(q) ||
        (m.codigo_externo && m.codigo_externo.toLowerCase().includes(q))
    );
  }
  return list;
});

const openNewDialog = () => {
  isEditing.value = false;
  editingId.value = null;
  form.value = {
    codigo: '',
    sigla: '',
    nombre: '',
    codigo_externo: '',
    dias_vencimiento: 30,
    copago_default: 0,
    activa: true,
  };
  isDialogVisible.value = true;
};

const openEditDialog = (m: ObraSocial) => {
  isEditing.value = true;
  editingId.value = m.id;
  form.value = {
    codigo: m.codigo,
    sigla: m.sigla,
    nombre: m.nombre,
    codigo_externo: m.codigo_externo || '',
    dias_vencimiento: m.dias_vencimiento,
    copago_default: m.copago_default !== undefined && m.copago_default !== null ? Number(m.copago_default) : 0,
    activa: m.activa,
  };
  isDialogVisible.value = true;
};

const handleSave = async () => {
  if (!form.value.codigo.trim() || !form.value.sigla.trim() || !form.value.nombre.trim()) {
    toast.add({
      severity: 'warn',
      summary: 'Atención',
      detail: 'Código, Sigla y Nombre son campos requeridos',
      life: 3000,
    });
    return;
  }

  isSaving.value = true;
  try {
    if (isEditing.value && editingId.value) {
      const updatePayload: ObraSocialUpdate = {
        sigla: form.value.sigla.trim().toUpperCase(),
        nombre: form.value.nombre.trim(),
        codigo_externo: form.value.codigo_externo?.trim() || null,
        dias_vencimiento: form.value.dias_vencimiento,
        copago_default: form.value.copago_default !== undefined && form.value.copago_default !== null ? Number(form.value.copago_default) : 0,
        activa: form.value.activa,
      };
      await mutualesService.update(editingId.value, updatePayload);
      toast.add({
        severity: 'success',
        summary: 'Actualizada',
        detail: 'Obra Social actualizada con éxito',
        life: 3000,
      });
    } else {
      const createPayload: ObraSocialCreate = {
        codigo: form.value.codigo.trim().toUpperCase(),
        sigla: form.value.sigla.trim().toUpperCase(),
        nombre: form.value.nombre.trim(),
        codigo_externo: form.value.codigo_externo?.trim() || null,
        dias_vencimiento: form.value.dias_vencimiento,
        copago_default: form.value.copago_default !== undefined && form.value.copago_default !== null ? Number(form.value.copago_default) : 0,
        activa: form.value.activa,
      };
      await mutualesService.create(createPayload);
      toast.add({
        severity: 'success',
        summary: 'Creada',
        detail: 'Obra Social registrada con éxito',
        life: 3000,
      });
    }
    isDialogVisible.value = false;
    await loadMutuales();
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo guardar la obra social',
      life: 4000,
    });
  } finally {
    isSaving.value = false;
  }
};

const handleToggleActive = async (m: ObraSocial) => {
  try {
    await mutualesService.toggleActive(m.id);
    toast.add({
      severity: 'info',
      summary: m.activa ? 'Desactivada' : 'Activada',
      detail: `${m.sigla} ahora está ${m.activa ? 'inactiva' : 'activa'}.`,
      life: 2500,
    });
    await loadMutuales();
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo cambiar el estado',
      life: 3000,
    });
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Obras Sociales y Mutuales</h2>
        <p class="text-xs text-slate-500">Gestión de convenios, vigencias, días de vencimiento y estado operativo</p>
      </div>

      <Button label="Nueva Obra Social" icon="pi pi-plus" severity="primary" size="small" @click="openNewDialog" />
    </div>

    <!-- Filter Bar -->
    <div
      class="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
      <div class="flex-1 min-w-[260px] max-w-md">
        <span class="p-input-icon-left w-full">
          <i class="pi pi-search text-slate-400 text-xs"></i>
          <InputText v-model="searchInput" placeholder="Buscar por Sigla, Nombre o Código..." class="w-full text-xs" />
        </span>
      </div>

      <div class="flex items-center space-x-2">
        <div class="flex items-center space-x-2 mr-2">
          <Checkbox v-model="filterOnlyActive" binary inputId="filterActive" />
          <label for="filterActive" class="text-xs font-semibold text-slate-600 cursor-pointer">Solo Activas</label>
        </div>
        <Button icon="pi pi-refresh" severity="secondary" rounded text size="small" :loading="isLoading"
          @click="loadMutuales" title="Recargar listado" />
      </div>
    </div>

    <!-- Data Table -->
    <LoadingSpinner v-if="isLoading && mutuales.length === 0" message="Cargando obras sociales..." />

    <div v-else-if="filteredMutuales.length > 0"
      class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <DataTable :value="filteredMutuales" paginator :rows="20" responsiveLayout="scroll" class="p-datatable-sm"
        rowHover>
        <Column field="sigla" header="Sigla" sortable>
          <template #body="{ data }">
            <span class="font-bold text-slate-800">{{ data.sigla }}</span>
          </template>
        </Column>

        <Column field="nombre" header="Nombre / Razón Social" sortable>
          <template #body="{ data }">
            <span class="text-xs text-slate-700 font-medium">{{ data.nombre }}</span>
          </template>
        </Column>

        <Column field="codigo" header="Código" sortable>
          <template #body="{ data }">
            <span class="font-mono text-xs text-slate-500 font-semibold">{{ data.codigo }}</span>
          </template>
        </Column>

        <Column field="codigo_externo" header="Cód. Externo">
          <template #body="{ data }">
            <span class="text-xs text-slate-400 font-mono">{{ data.codigo_externo || '-' }}</span>
          </template>
        </Column>

        <Column field="dias_vencimiento" header="Vencimiento" sortable>
          <template #body="{ data }">
            <span
              class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              <i class="pi pi-calendar text-[10px]"></i> {{ data.dias_vencimiento }} días
            </span>
          </template>
        </Column>

        <Column field="copago_default" header="Copago Default" sortable>
          <template #body="{ data }">
            <span class="font-mono text-xs font-semibold text-emerald-700">
              ${{ Number(data.copago_default || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
            </span>
          </template>
        </Column>

        <Column field="activa" header="Estado" sortable>
          <template #body="{ data }">
            <Tag :value="data.activa ? 'ACTIVA' : 'INACTIVA'" :severity="data.activa ? 'success' : 'secondary'"
              class="text-[10px]" />
          </template>
        </Column>

        <Column header="Acciones" style="width: 120px">
          <template #body="{ data }">
            <div class="flex items-center space-x-1">
              <Button icon="pi pi-pencil" text rounded size="small" severity="info" @click="openEditDialog(data)"
                title="Editar Obra Social" />
              <Button :icon="data.activa ? 'pi pi-ban' : 'pi pi-check'" text rounded size="small"
                :severity="data.activa ? 'danger' : 'success'" @click="handleToggleActive(data)"
                :title="data.activa ? 'Desactivar mutual' : 'Activar mutual'" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <EmptyState v-else title="No se encontraron obras sociales"
      description="No hay registros que coincidan con la búsqueda o no existen mutuales cargadas."
      icon="pi pi-id-card" />

    <!-- Modal: Crear / Editar Obra Social -->
    <Dialog v-model:visible="isDialogVisible" modal
      :header="isEditing ? 'Editar Obra Social' : 'Registrar Nueva Obra Social'" :style="{ width: '520px' }">
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Código Único <span class="text-red-500">*</span>
            </label>
            <InputText v-model="form.codigo" placeholder="Ej: OSDE, PAMI, SM" class="w-full text-xs uppercase font-mono"
              :disabled="isEditing" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Sigla / Acrónimo <span class="text-red-500">*</span>
            </label>
            <InputText v-model="form.sigla" placeholder="Ej: OSDE" class="w-full text-xs uppercase font-bold" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Nombre Completo / Razón Social <span class="text-red-500">*</span>
          </label>
          <InputText v-model="form.nombre" placeholder="Ej: Organización de Servicios Directos Empresarios"
            class="w-full text-xs" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Días de Vencimiento <span class="text-red-500">*</span>
            </label>
            <InputNumber v-model="form.dias_vencimiento" :min="1" :max="365" suffix=" días" class="w-full text-xs" />
            <p class="text-[10px] text-slate-400 mt-0.5">Días de validez desde la prescripción</p>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Copago Predeterminado ($)
            </label>
            <InputNumber v-model="form.copago_default as any" mode="currency" currency="ARS" locale="es-AR" class="w-full text-xs" placeholder="$ 0,00" />
            <p class="text-[10px] text-slate-400 mt-0.5">Valor sugerido al cargar orden</p>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Código Externo (Opcional)
          </label>
          <InputText v-model="form.codigo_externo as any" placeholder="Ej: 1040" class="w-full text-xs" />
        </div>

        <div class="flex items-center space-x-2 pt-2 border-t border-slate-100">
          <Checkbox v-model="form.activa as any" binary inputId="isActiva" />
          <label for="isActiva" class="text-xs font-semibold text-slate-700 cursor-pointer">
            Obra Social Habilitada para Ingreso de Órdenes
          </label>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isDialogVisible = false" />
        <Button :label="isEditing ? 'Guardar Cambios' : 'Registrar Obra Social'" icon="pi pi-check" severity="primary"
          :loading="isSaving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
