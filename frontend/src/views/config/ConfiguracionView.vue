<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { configService } from '../../services/config.service';
import {
  EstadoOrdenConfig,
  EstadoOrdenConfigCreate,
  EstadoOrdenConfigUpdate,
  MotivoCancelacion,
  MotivoCancelacionCreate,
  MotivoCancelacionUpdate,
  TipoEstadoOrden,
} from '../../types/ordenes';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import Dropdown from 'primevue/dropdown';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Checkbox from 'primevue/checkbox';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const motivos = ref<MotivoCancelacion[]>([]);
const estados = ref<EstadoOrdenConfig[]>([]);
const isLoadingMotivos = ref(true);
const isLoadingEstados = ref(true);

// Modal Motivo
const isDialogVisible = ref(false);
const isEditing = ref(false);
const isSaving = ref(false);
const editingId = ref<string | null>(null);

const form = ref<MotivoCancelacionCreate>({
  codigo: '',
  nombre: '',
  descripcion: '',
  activo: true,
});

// Modal Estado
const isEstadoDialogVisible = ref(false);
const isEditingEstado = ref(false);
const isSavingEstado = ref(false);
const editingEstadoId = ref<number | null>(null);

const estadoForm = ref<{
  codigo: string;
  nombre: string;
  descripcion: string;
  tipo: TipoEstadoOrden;
  requiere_motivo: boolean;
  color_badge: string;
  icono: string;
  activo: boolean;
  orden_secuencia: number;
}>({
  codigo: '',
  nombre: '',
  descripcion: '',
  tipo: 'PROCESO',
  requiere_motivo: false,
  color_badge: 'info',
  icono: 'pi pi-tag',
  activo: true,
  orden_secuencia: 10,
});

const opcionesColores = [
  { label: 'Información (Azul)', value: 'info' },
  { label: 'Advertencia (Ámbar)', value: 'warn' },
  { label: 'Alerta / Peligro (Rojo)', value: 'danger' },
  { label: 'Éxito (Verde)', value: 'success' },
  { label: 'Secundario (Gris)', value: 'secondary' },
  { label: 'Contraste (Negro)', value: 'contrast' },
];

const opcionesTiposEstado = [
  { label: 'En Proceso Activo', value: 'PROCESO' },
  { label: 'Finalización / Terminal', value: 'FINALIZACION' },
];

const loadMotivos = async () => {
  isLoadingMotivos.value = true;
  try {
    motivos.value = await configService.listMotivosCancelacion(false);
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los motivos', life: 3000 });
  } finally {
    isLoadingMotivos.value = false;
  }
};

const loadEstados = async () => {
  isLoadingEstados.value = true;
  try {
    estados.value = await configService.listEstados(false);
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los estados', life: 3000 });
  } finally {
    isLoadingEstados.value = false;
  }
};

onMounted(() => {
  loadMotivos();
  loadEstados();
});

const openNewDialog = () => {
  isEditing.value = false;
  editingId.value = null;
  form.value = {
    codigo: '',
    nombre: '',
    descripcion: '',
    activo: true,
  };
  isDialogVisible.value = true;
};

const openEditDialog = (m: MotivoCancelacion) => {
  isEditing.value = true;
  editingId.value = m.id;
  form.value = {
    codigo: m.codigo,
    nombre: m.nombre,
    descripcion: m.descripcion || '',
    activo: m.activo,
  };
  isDialogVisible.value = true;
};

const handleSave = async () => {
  if (!form.value.codigo.trim() || !form.value.nombre.trim()) {
    toast.add({
      severity: 'warn',
      summary: 'Atención',
      detail: 'Código y Nombre son obligatorios',
      life: 3000,
    });
    return;
  }

  isSaving.value = true;
  try {
    if (isEditing.value && editingId.value) {
      const updatePayload: MotivoCancelacionUpdate = {
        nombre: form.value.nombre.trim(),
        descripcion: form.value.descripcion?.trim() || null,
        activo: form.value.activo,
      };
      await configService.updateMotivoCancelacion(editingId.value, updatePayload);
      toast.add({ severity: 'success', summary: 'Actualizado', detail: 'Motivo modificado con éxito', life: 3000 });
    } else {
      const createPayload: MotivoCancelacionCreate = {
        codigo: form.value.codigo.trim().toUpperCase(),
        nombre: form.value.nombre.trim(),
        descripcion: form.value.descripcion?.trim() || null,
        activo: form.value.activo,
      };
      await configService.createMotivoCancelacion(createPayload);
      toast.add({ severity: 'success', summary: 'Creado', detail: 'Motivo de cancelación registrado', life: 3000 });
    }
    isDialogVisible.value = false;
    await loadMotivos();
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'Error al guardar motivo',
      life: 4000,
    });
  } finally {
    isSaving.value = false;
  }
};

const handleToggleActive = async (m: MotivoCancelacion) => {
  try {
    await configService.toggleActiveMotivoCancelacion(m.id);
    toast.add({
      severity: 'info',
      summary: m.activo ? 'Desactivado' : 'Activado',
      detail: `${m.nombre} ahora está ${m.activo ? 'inactivo' : 'activo'}.`,
      life: 2500,
    });
    await loadMotivos();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cambiar estado', life: 3000 });
  }
};

// Acciones Estados
const openNewEstadoDialog = () => {
  isEditingEstado.value = false;
  editingEstadoId.value = null;
  estadoForm.value = {
    codigo: '',
    nombre: '',
    descripcion: '',
    tipo: 'PROCESO',
    requiere_motivo: false,
    color_badge: 'info',
    icono: 'pi pi-tag',
    activo: true,
    orden_secuencia: estados.value.length + 1,
  };
  isEstadoDialogVisible.value = true;
};

const openEditEstadoDialog = (e: EstadoOrdenConfig) => {
  isEditingEstado.value = true;
  editingEstadoId.value = e.id;
  estadoForm.value = {
    codigo: e.codigo,
    nombre: e.nombre,
    descripcion: e.descripcion || '',
    tipo: e.tipo,
    requiere_motivo: e.requiere_motivo,
    color_badge: e.color_badge,
    icono: e.icono || '',
    activo: e.activo,
    orden_secuencia: e.orden_secuencia,
  };
  isEstadoDialogVisible.value = true;
};

const handleSaveEstado = async () => {
  if (!estadoForm.value.nombre.trim() || (!isEditingEstado.value && !estadoForm.value.codigo.trim())) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Código y Nombre del estado son obligatorios', life: 3000 });
    return;
  }

  isSavingEstado.value = true;
  try {
    if (isEditingEstado.value && editingEstadoId.value) {
      const updatePayload: EstadoOrdenConfigUpdate = {
        nombre: estadoForm.value.nombre.trim(),
        descripcion: estadoForm.value.descripcion?.trim() || null,
        tipo: estadoForm.value.tipo,
        requiere_motivo: estadoForm.value.requiere_motivo,
        color_badge: estadoForm.value.color_badge,
        icono: estadoForm.value.icono?.trim() || null,
        activo: estadoForm.value.activo,
        orden_secuencia: estadoForm.value.orden_secuencia,
      };
      await configService.updateEstado(editingEstadoId.value, updatePayload);
      toast.add({ severity: 'success', summary: 'Estado Actualizado', detail: 'Configuración guardada con éxito', life: 3000 });
    } else {
      const createPayload: EstadoOrdenConfigCreate = {
        codigo: estadoForm.value.codigo.trim().toUpperCase(),
        nombre: estadoForm.value.nombre.trim(),
        descripcion: estadoForm.value.descripcion?.trim() || null,
        tipo: estadoForm.value.tipo,
        requiere_motivo: estadoForm.value.requiere_motivo,
        color_badge: estadoForm.value.color_badge,
        icono: estadoForm.value.icono?.trim() || null,
        activo: estadoForm.value.activo,
        orden_secuencia: estadoForm.value.orden_secuencia,
      };
      await configService.createEstado(createPayload);
      toast.add({ severity: 'success', summary: 'Estado Creado', detail: 'Nuevo estado de orden registrado', life: 3000 });
    }
    isEstadoDialogVisible.value = false;
    await loadEstados();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al guardar estado', life: 4000 });
  } finally {
    isSavingEstado.value = false;
  }
};

const handleToggleActiveEstado = async (e: EstadoOrdenConfig) => {
  try {
    await configService.toggleActiveEstado(e.id);
    toast.add({
      severity: 'info',
      summary: e.activo ? 'Desactivado' : 'Activado',
      detail: `Estado '${e.nombre}' ahora está ${e.activo ? 'inactivo' : 'activo'}.`,
      life: 2500,
    });
    await loadEstados();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cambiar estado', life: 3000 });
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <i class="pi pi-cog text-blue-600"></i>
          <span>Configuración del Sistema</span>
        </h2>
        <p class="text-xs text-slate-500">Parámetros generales, catálogo de motivos de cancelación y reglas de auditoría
        </p>
      </div>
    </div>

    <!-- Main Tabs -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <Tabs value="0">
        <TabList>
          <Tab value="0">
            <i class="pi pi-ban mr-1.5 text-red-500"></i> Motivos de Cancelación
          </Tab>
          <Tab value="1">
            <i class="pi pi-list mr-1.5 text-blue-600"></i> Estados del Sistema (con ID para API/n8n)
          </Tab>
          <Tab value="2">
            <i class="pi pi-sliders-h mr-1.5 text-indigo-500"></i> Ciclo de Vida y Reglas
          </Tab>
        </TabList>

        <TabPanels>
          <!-- Tab 0: Motivos de Cancelacion -->
          <TabPanel value="0">
            <div class="p-4 space-y-4">
              <div
                class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div>
                  <h4 class="text-sm font-bold text-slate-800">Catálogo de Motivos de Cancelación</h4>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Motivos normalizados y únicos requeridos al cancelar o anular una orden médica para fines
                    estadísticos.
                  </p>
                </div>
                <Button label="Nuevo Motivo" icon="pi pi-plus" severity="primary" size="small" class="text-xs"
                  @click="openNewDialog" />
              </div>

              <LoadingSpinner v-if="isLoadingMotivos" message="Cargando motivos..." />

              <DataTable v-else :value="motivos" stripedRows responsiveLayout="scroll" class="p-datatable-sm">
                <Column field="nombre" header="Motivo de Cancelación" sortable>
                  <template #body="{ data }">
                    <span class="font-bold text-slate-800 text-xs">{{ data.nombre }}</span>
                  </template>
                </Column>

                <Column field="codigo" header="Código" sortable style="width: 180px">
                  <template #body="{ data }">
                    <span class="font-mono text-xs text-slate-500">{{ data.codigo }}</span>
                  </template>
                </Column>

                <Column field="descripcion" header="Descripción / Explicación">
                  <template #body="{ data }">
                    <span class="text-xs text-slate-600">{{ data.descripcion || '-' }}</span>
                  </template>
                </Column>

                <Column field="activo" header="Estado" sortable style="width: 120px">
                  <template #body="{ data }">
                    <Tag :value="data.activo ? 'ACTIVO' : 'INACTIVO'" :severity="data.activo ? 'success' : 'secondary'"
                      class="text-[10px]" />
                  </template>
                </Column>

                <Column header="Acciones" style="width: 110px">
                  <template #body="{ data }">
                    <div class="flex items-center space-x-1">
                      <Button icon="pi pi-pencil" text rounded size="small" severity="info" title="Editar motivo"
                        @click="openEditDialog(data)" />
                      <Button :icon="data.activo ? 'pi pi-ban' : 'pi pi-check'" text rounded size="small"
                        :severity="data.activo ? 'danger' : 'success'" :title="data.activo ? 'Desactivar' : 'Activar'"
                        @click="handleToggleActive(data)" />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>

          <!-- Tab 1: Estados del Sistema con ID -->
          <TabPanel value="1">
            <div class="p-4 space-y-4">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div>
                  <h4 class="text-sm font-bold text-slate-800">Catálogo de Estados de Órdenes (con ID Numérico)</h4>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Utilice el <strong>ID numérico</strong> en scripts o nodos de <strong>n8n</strong> (<code class="bg-blue-50 text-blue-700 px-1 py-0.5 rounded font-mono">POST /ordenes/{id}/estado { "estado_id": ID }</code>) para cambiar estados fácilmente.
                  </p>
                </div>
                <Button label="Nuevo Estado" icon="pi pi-plus" severity="primary" size="small" class="text-xs" @click="openNewEstadoDialog" />
              </div>

              <LoadingSpinner v-if="isLoadingEstados" message="Cargando estados..." />

              <DataTable v-else :value="estados" stripedRows responsiveLayout="scroll" class="p-datatable-sm" rowHover>
                <Column field="id" header="ID (API)" sortable style="width: 100px">
                  <template #body="{ data }">
                    <span class="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-blue-600 text-white font-mono font-bold text-xs shadow-sm">
                      {{ data.id }}
                    </span>
                  </template>
                </Column>

                <Column field="nombre" header="Nombre del Estado" sortable style="width: 200px">
                  <template #body="{ data }">
                    <div class="flex items-center space-x-2">
                      <Tag :value="data.nombre" :severity="(data.color_badge as any) || 'info'" class="text-xs font-bold" />
                      <span v-if="data.es_sistema" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">Base</span>
                    </div>
                  </template>
                </Column>

                <Column field="codigo" header="Código" sortable style="width: 170px">
                  <template #body="{ data }">
                    <span class="font-mono text-xs text-slate-500 font-semibold">{{ data.codigo }}</span>
                  </template>
                </Column>

                <Column field="tipo" header="Tipo de Estado" sortable style="width: 150px">
                  <template #body="{ data }">
                    <span
                      class="px-2 py-0.5 rounded text-xs font-bold"
                      :class="data.tipo === 'FINALIZACION' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'"
                    >
                      {{ data.tipo === 'FINALIZACION' ? '🏁 Finalización' : '⚙️ En Proceso' }}
                    </span>
                  </template>
                </Column>

                <Column field="descripcion" header="Descripción">
                  <template #body="{ data }">
                    <span class="text-xs text-slate-600">{{ data.descripcion || '-' }}</span>
                  </template>
                </Column>

                <Column field="activo" header="Estado" sortable style="width: 100px">
                  <template #body="{ data }">
                    <Tag :value="data.activo ? 'ACTIVO' : 'INACTIVO'" :severity="data.activo ? 'success' : 'secondary'" class="text-[10px]" />
                  </template>
                </Column>

                <Column header="Acciones" style="width: 90px">
                  <template #body="{ data }">
                    <div class="flex items-center space-x-1">
                      <Button icon="pi pi-pencil" text rounded size="small" severity="info" title="Editar estado" @click="openEditEstadoDialog(data)" />
                      <Button
                        :icon="data.activo ? 'pi pi-ban' : 'pi pi-check'"
                        text
                        rounded
                        size="small"
                        :severity="data.activo ? 'danger' : 'success'"
                        :title="data.activo ? 'Desactivar' : 'Activar'"
                        @click="handleToggleActiveEstado(data)"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>

          <!-- Tab 2: Reglas de Estados -->
          <TabPanel value="2">
            <div class="p-6 space-y-4">
              <h4 class="text-sm font-bold text-slate-800">Ciclo de Vida de las Órdenes Médicas</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                  <p class="font-bold text-blue-800 text-sm">Estados en Proceso (Activos)</p>
                  <ul class="space-y-1.5 text-slate-600">
                    <li><strong class="text-slate-800">Ingreso:</strong> Orden médica registrada en sede esperando
                      revisión de
                      auditoría.</li>
                    <li><strong class="text-slate-800">en Auditoria:</strong> Auditor médico asignado o evaluando
                      documentación
                      clínica.</li>
                    <li><strong class="text-slate-800">Solicitudes de auditoria:</strong> Observación emitida por
                      auditor; entra a
                      llamadas pendientes.</li>
                    <li><strong class="text-slate-800">Actualizada:</strong> Sucursal adjuntó documentación faltante o
                      respondió
                      requerimiento.</li>
                    <li><strong class="text-slate-800">Auditoria Finalizada:</strong> Auditor aprobó trámite; entra a
                      llamadas
                      pendientes para que el paciente asista al laboratorio.</li>
                  </ul>
                </div>

                <div class="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                  <p class="font-bold text-emerald-800 text-sm">Estados Terminales / Cierre</p>
                  <ul class="space-y-1.5 text-slate-600">
                    <li><strong class="text-emerald-700">Cerrada:</strong> Resolución exitosa. El paciente asistió y se
                      realizó la
                      extracción/estudio.</li>
                    <li><strong class="text-red-700">Cancelada:</strong> Proceso cancelado. Requiere seleccionar
                      obligatoriamente
                      un motivo de cancelación.</li>
                    <li><strong class="text-amber-700">Dar de baja:</strong> Baja administrativa / anulación previa a
                      ejecución.
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>

    <!-- Modal: Crear / Editar Motivo -->
    <Dialog v-model:visible="isDialogVisible" modal
      :header="isEditing ? 'Editar Motivo de Cancelación' : 'Nuevo Motivo de Cancelación'" :style="{ width: '480px' }">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Código Único <span class="text-red-500">*</span>
          </label>
          <InputText v-model="form.codigo" placeholder="Ej: ORDEN_VENCIDA, NO_CUMPLE_CONDICIONES"
            class="w-full text-xs uppercase font-mono" :disabled="isEditing" />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Nombre del Motivo <span class="text-red-500">*</span>
          </label>
          <InputText v-model="form.nombre" placeholder="Ej: Orden Vencida" class="w-full text-xs font-bold" />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Descripción / Detalle</label>
          <Textarea v-model="form.descripcion as any" rows="3" placeholder="Explicación del criterio de cancelación..."
            class="w-full text-xs" />
        </div>

        <div class="flex items-center space-x-2 pt-2 border-t border-slate-100">
          <Checkbox v-model="form.activo as any" binary inputId="isMotivoActivo" />
          <label for="isMotivoActivo" class="text-xs font-semibold text-slate-700 cursor-pointer">
            Motivo Activo y Disponible en el Selector
          </label>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isDialogVisible = false" />
        <Button :label="isEditing ? 'Guardar Cambios' : 'Registrar Motivo'" icon="pi pi-check" severity="primary"
          :loading="isSaving" @click="handleSave" />
      </template>
    </Dialog>

    <!-- Modal: Crear / Editar Estado de Orden -->
    <Dialog
      v-model:visible="isEstadoDialogVisible"
      modal
      :header="isEditingEstado ? `Editar Estado (ID: ${editingEstadoId})` : 'Crear Nuevo Estado de Orden'"
      :style="{ width: '520px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Código Único <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="estadoForm.codigo"
              placeholder="Ej: EN_VALIDACION_MUTUAL"
              class="w-full text-xs uppercase font-mono"
              :disabled="isEditingEstado"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Nombre del Estado <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="estadoForm.nombre"
              placeholder="Ej: En Validación con Mutual"
              class="w-full text-xs font-bold"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Clasificación / Tipo <span class="text-red-500">*</span>
            </label>
            <Dropdown
              v-model="estadoForm.tipo"
              :options="opcionesTiposEstado"
              optionLabel="label"
              optionValue="value"
              class="w-full text-xs"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Color del Badge
            </label>
            <Dropdown
              v-model="estadoForm.color_badge"
              :options="opcionesColores"
              optionLabel="label"
              optionValue="value"
              class="w-full text-xs"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Descripción</label>
          <Textarea
            v-model="estadoForm.descripcion"
            rows="2"
            placeholder="Alcance operativo o significado del estado..."
            class="w-full text-xs"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Ícono PrimeIcons</label>
            <InputText
              v-model="estadoForm.icono"
              placeholder="Ej: pi pi-clock"
              class="w-full text-xs font-mono"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Orden / Secuencia</label>
            <InputNumber
              v-model="estadoForm.orden_secuencia"
              class="w-full text-xs"
              :min="1"
              :max="100"
            />
          </div>
        </div>

        <div class="space-y-2 pt-2 border-t border-slate-100">
          <div class="flex items-center space-x-2">
            <Checkbox v-model="estadoForm.requiere_motivo" binary inputId="isReqMotivo" />
            <label for="isReqMotivo" class="text-xs font-semibold text-slate-700 cursor-pointer">
              Exigir motivo obligatorio al pasar a este estado
            </label>
          </div>
          <div class="flex items-center space-x-2">
            <Checkbox v-model="estadoForm.activo" binary inputId="isEstActivo" />
            <label for="isEstActivo" class="text-xs font-semibold text-slate-700 cursor-pointer">
              Estado Activo y Disponible en el Sistema
            </label>
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isEstadoDialogVisible = false" />
        <Button
          :label="isEditingEstado ? 'Guardar Cambios' : 'Registrar Estado'"
          icon="pi pi-check"
          severity="primary"
          :loading="isSavingEstado"
          @click="handleSaveEstado"
        />
      </template>
    </Dialog>
  </div>
</template>
