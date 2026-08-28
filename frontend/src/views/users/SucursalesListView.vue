<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { usersService } from '../../services/users.service';
import { Sucursal, SucursalCreate } from '../../types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const sucursales = ref<Sucursal[]>([]);
const isLoading = ref(false);
const isDialogVisible = ref(false);
const isSaving = ref(false);

const form = ref<SucursalCreate>({
  nombre: '',
  codigo: '',
  activa: true,
});

const loadSucursales = async () => {
  isLoading.value = true;
  try {
    sucursales.value = await usersService.listSucursales();
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar las sucursales', life: 3000 });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadSucursales();
});

const handleOpenCreate = () => {
  form.value = {
    nombre: '',
    codigo: '',
    activa: true,
  };
  isDialogVisible.value = true;
};

const handleSave = async () => {
  if (!form.value.nombre.trim() || !form.value.codigo.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Complete el nombre y código de la sucursal', life: 3000 });
    return;
  }

  isSaving.value = true;
  try {
    await usersService.createSucursal(form.value);
    toast.add({ severity: 'success', summary: 'Sucursal Creada', detail: 'Nueva sede incorporada al sistema', life: 3000 });
    isDialogVisible.value = false;
    await loadSucursales();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al crear sucursal', life: 4000 });
  } finally {
    isSaving.value = false;
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Sedes y Sucursales</h2>
        <p class="text-sm text-slate-500">Gestión de centros médicos, clínicas y bocas de atención</p>
      </div>
      <Button label="Nueva Sucursal" icon="pi pi-plus" severity="primary" @click="handleOpenCreate" />
    </div>

    <!-- Table -->
    <LoadingSpinner v-if="isLoading" message="Cargando sucursales..." />

    <div v-else class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <DataTable :value="sucursales" responsiveLayout="scroll" stripedRows class="p-datatable-sm">
        <Column field="codigo" header="Código" sortable class="font-mono text-xs font-bold text-slate-800" />
        <Column field="nombre" header="Nombre de Sede" sortable class="font-semibold text-slate-800" />
        <Column header="Estado">
          <template #body="{ data }">
            <Tag :value="data.activa ? 'Activa' : 'Inactiva'" :severity="data.activa ? 'success' : 'danger'" class="text-xs" />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Dialog Create Sucursal -->
    <Dialog v-model:visible="isDialogVisible" modal header="Registrar Sucursal" :style="{ width: '400px' }">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombre de la Sede <span class="text-red-500">*</span></label>
          <InputText v-model="form.nombre" placeholder="Ej: Sede Norte" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Código Único <span class="text-red-500">*</span></label>
          <InputText v-model="form.codigo" placeholder="Ej: NORTE" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isDialogVisible = false" />
        <Button label="Guardar Sucursal" icon="pi pi-check" :loading="isSaving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
