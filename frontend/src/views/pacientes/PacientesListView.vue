<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { pacientesService } from '../../services/pacientes.service';
import { Paciente, PacienteCreate } from '../../types/pacientes';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import EmptyState from '../../components/common/EmptyState.vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const pacientes = ref<Paciente[]>([]);
const totalRecords = ref(0);
const isLoading = ref(false);
const search = ref('');
const skip = ref(0);
const limit = ref(20);

// Modal state
const isDialogVisible = ref(false);
const isEditing = ref(false);
const editingId = ref<string | null>(null);
const isSaving = ref(false);

const form = ref<PacienteCreate>({
  documento: '',
  nombres: '',
  apellidos: '',
  fecha_nacimiento: null,
  obra_social: '',
  nro_afiliado: '',
  telefono: '',
  email: '',
  is_active: true,
});

const loadPacientes = async () => {
  isLoading.value = true;
  try {
    const res = await pacientesService.list({
      skip: skip.value,
      limit: limit.value,
      search: search.value.trim() || undefined,
    });
    pacientes.value = res.items;
    totalRecords.value = res.total;
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los pacientes', life: 3000 });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadPacientes();
});

const handleSearch = () => {
  skip.value = 0;
  loadPacientes();
};

const handleOpenCreate = () => {
  isEditing.value = false;
  editingId.value = null;
  form.value = {
    documento: '',
    nombres: '',
    apellidos: '',
    fecha_nacimiento: null,
    obra_social: '',
    nro_afiliado: '',
    telefono: '',
    email: '',
    is_active: true,
  };
  isDialogVisible.value = true;
};

const handleOpenEdit = (paciente: Paciente) => {
  isEditing.value = true;
  editingId.value = paciente.id;
  form.value = {
    documento: paciente.documento,
    nombres: paciente.nombres,
    apellidos: paciente.apellidos,
    fecha_nacimiento: paciente.fecha_nacimiento,
    obra_social: paciente.obra_social || '',
    nro_afiliado: paciente.nro_afiliado || '',
    telefono: paciente.telefono || '',
    email: paciente.email || '',
    is_active: paciente.is_active,
  };
  isDialogVisible.value = true;
};

const handleSave = async () => {
  if (!form.value.documento.trim() || !form.value.nombres.trim() || !form.value.apellidos.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Documento, Nombres y Apellidos son obligatorios', life: 3000 });
    return;
  }

  isSaving.value = true;
  try {
    if (isEditing.value && editingId.value) {
      await pacientesService.update(editingId.value, form.value);
      toast.add({ severity: 'success', summary: 'Paciente Actualizado', detail: 'Datos guardados con éxito', life: 3000 });
    } else {
      await pacientesService.create(form.value);
      toast.add({ severity: 'success', summary: 'Paciente Registrado', detail: 'Nuevo paciente incorporado', life: 3000 });
    }
    isDialogVisible.value = false;
    await loadPacientes();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al guardar paciente', life: 4000 });
  } finally {
    isSaving.value = false;
  }
};

const onPageChange = (event: any) => {
  skip.value = event.first;
  limit.value = event.rows;
  loadPacientes();
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Padrón de Pacientes</h2>
        <p class="text-sm text-slate-500">Gestión centralizada de afiliados y datos de contacto clínico</p>
      </div>
      <Button label="Registrar Paciente" icon="pi pi-user-plus" severity="primary" @click="handleOpenCreate" />
    </div>

    <!-- Search Bar -->
    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
      <div class="flex-1">
        <span class="p-input-icon-left w-full">
          <i class="pi pi-search text-slate-400"></i>
          <InputText
            v-model="search"
            placeholder="Buscar por DNI o Apellidos / Nombres..."
            class="w-full text-sm"
            @keyup.enter="handleSearch"
          />
        </span>
      </div>
      <Button icon="pi pi-search" label="Buscar" size="small" @click="handleSearch" />
    </div>

    <!-- Table -->
    <LoadingSpinner v-if="isLoading" message="Cargando padrón de pacientes..." />

    <div v-else-if="pacientes.length > 0" class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <DataTable
        :value="pacientes"
        lazy
        paginator
        :rows="limit"
        :totalRecords="totalRecords"
        :first="skip"
        @page="onPageChange"
        responsiveLayout="scroll"
        stripedRows
        class="p-datatable-sm"
      >
        <Column field="documento" header="Documento / DNI" sortable class="font-mono text-xs font-bold text-slate-800" />
        <Column field="nombre_completo" header="Nombre Completo" sortable class="font-semibold text-slate-800 text-sm" />
        <Column field="obra_social" header="Mutual / Cobertura" sortable />
        <Column field="nro_afiliado" header="N° Afiliado" />
        <Column field="telefono" header="Teléfono" />
        <Column field="email" header="Email" />
        <Column header="Acción" alignFrozen="right" frozen>
          <template #body="{ data }">
            <Button icon="pi pi-pencil" text rounded severity="secondary" size="small" @click="handleOpenEdit(data)" title="Editar" />
          </template>
        </Column>
      </DataTable>
    </div>

    <EmptyState
      v-else
      title="No se encontraron pacientes"
      description="Prueba con otro término de búsqueda o registra un nuevo paciente en el sistema."
      icon="pi pi-users"
    >
      <template #action>
        <Button label="Registrar Paciente" icon="pi pi-user-plus" class="mt-4" size="small" @click="handleOpenCreate" />
      </template>
    </EmptyState>

    <!-- Dialog Create / Edit -->
    <Dialog
      v-model:visible="isDialogVisible"
      modal
      :header="isEditing ? 'Editar Ficha de Paciente' : 'Registrar Nuevo Paciente'"
      :style="{ width: '550px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">DNI / Documento <span class="text-red-500">*</span></label>
            <InputText v-model="form.documento" placeholder="Sin puntos" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Fecha de Nacimiento</label>
            <InputText v-model="form.fecha_nacimiento as any" type="date" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Apellidos <span class="text-red-500">*</span></label>
            <InputText v-model="form.apellidos" placeholder="PÉREZ" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombres <span class="text-red-500">*</span></label>
            <InputText v-model="form.nombres" placeholder="Juan Carlos" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Obra Social / Cobertura</label>
            <InputText v-model="form.obra_social as any" placeholder="OSDE, PAMI, etc." class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">N° Afiliado</label>
            <InputText v-model="form.nro_afiliado as any" placeholder="Número credencial" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Teléfono</label>
            <InputText v-model="form.telefono as any" placeholder="11-4567-8900" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Email</label>
            <InputText v-model="form.email as any" type="email" placeholder="paciente@correo.com" class="w-full" />
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isDialogVisible = false" />
        <Button label="Guardar Paciente" icon="pi pi-check" :loading="isSaving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
