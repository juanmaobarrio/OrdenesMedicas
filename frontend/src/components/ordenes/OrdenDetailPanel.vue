<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ordenesService } from '../../services/ordenes.service';
import { usersService } from '../../services/users.service';
import { mutualesService } from '../../services/mutuales.service';
import { configService } from '../../services/config.service';
import { useAuthStore } from '../../stores/auth.store';
import { EstadoOrden, OrdenMedicaDetail, OrdenMedicaListItem, AdjuntoOrden, ObraSocial, UserDetail, MotivoCancelacion } from '../../types';

import Button from 'primevue/button';

import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Chips from 'primevue/chips';
import Dialog from 'primevue/dialog';
import Checkbox from 'primevue/checkbox';

import Dropdown from 'primevue/dropdown';
import Textarea from 'primevue/textarea';
import FileUpload from 'primevue/fileupload';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import Timeline from 'primevue/timeline';
import StatusTag from '../common/StatusTag.vue';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import RegistrarLlamadaModal from './RegistrarLlamadaModal.vue';
import { useToast } from 'primevue/usetoast';

const props = defineProps<{
  ordenId: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updated'): void;
}>();

const toast = useToast();
const authStore = useAuthStore();
const router = useRouter();

const orden = ref<OrdenMedicaDetail | null>(null);
const isLoading = ref(true);
const auditors = ref<UserDetail[]>([]);
const mutuales = ref<ObraSocial[]>([]);
const motivosCancelacion = ref<MotivoCancelacion[]>([]);

const opcionesHorarios = [
  'Todo el día',
  'Por la mañana',
  'Por la tarde',
  'Por la noche',
  'Solo WhatsApp',
  'Solo mail',
];

// Modals
const isCambioEstadoVisible = ref(false);
const selectedNuevoEstado = ref<EstadoOrden>('en Auditoria');
const selectedMotivoCancelacion = ref<string>('');
const motivoEstadoDetalle = ref('');
const observacionResultadoAuditoria = ref('');

const isSolicitudVisible = ref(false);
const motivoSolicitud = ref('Falta diagnóstico');
const mensajeSolicitud = ref('');

const isResponderVisible = ref(false);
const selectedSolicitudId = ref<string | null>(null);
const respuestaOperador = ref('');

const isAsignarAuditorVisible = ref(false);
const selectedAuditorId = ref<string | null>(null);

const isLlamadaModalVisible = ref(false);
const isEditOrdenVisible = ref(false);
const isActionLoading = ref(false);
const activeTab = ref('0');

// Números de Auditoría individuales

const nuevoNumeroAuditoria = ref('');
const isAddingAuditNumber = ref(false);

// Previsualización de Archivos / Popup Viewer
const isPreviewVisible = ref(false);
const previewFile = ref<AdjuntoOrden | null>(null);
const previewUrl = ref<string | null>(null);
const isLoadingPreview = ref(false);

// Auditorías Previas del Paciente
const prevOrders = ref<OrdenMedicaListItem[]>([]);
const isLoadingPrevOrders = ref(false);

const editForm = ref({
  contacto_nombre: '',
  contacto_horario: '',
  contacto_telefono: '',
  contacto_celular: '',
  contacto_email: '',
  numeros_auditoria: [] as string[],
  valor_copago: 0,
  valor_estudios_no_autorizados: 0,
  mutual: '',
  nro_afiliado: '',
  observaciones_ingreso: '',
  debe_orden_medica: false,
});


const handleOpenEditOrden = () => {
  if (!orden.value) return;
  editForm.value = {
    contacto_nombre: orden.value.contacto_nombre || '',
    contacto_horario: orden.value.contacto_horario || '',
    contacto_telefono: orden.value.contacto_telefono || '',
    contacto_celular: orden.value.contacto_celular || '',
    contacto_email: orden.value.contacto_email || '',
    numeros_auditoria: [...(orden.value.numeros_auditoria || [])],
    valor_copago: Number(orden.value.valor_copago) || 0,
    valor_estudios_no_autorizados: Number(orden.value.valor_estudios_no_autorizados) || 0,
    mutual: orden.value.mutual || '',
    nro_afiliado: orden.value.nro_afiliado || orden.value.paciente?.nro_afiliado || '',
    observaciones_ingreso: orden.value.observaciones_ingreso || '',
    debe_orden_medica: Boolean(orden.value.debe_orden_medica),
  };
  isEditOrdenVisible.value = true;
};

const handleSaveEditOrden = async () => {
  isActionLoading.value = true;
  try {
    const payload = {
      contacto_nombre: editForm.value.contacto_nombre.trim() || null,
      contacto_horario: editForm.value.contacto_horario.trim() || null,
      contacto_telefono: editForm.value.contacto_telefono.trim() || null,
      contacto_celular: editForm.value.contacto_celular.trim() || null,
      contacto_email: editForm.value.contacto_email.trim() || null,
      numeros_auditoria: editForm.value.numeros_auditoria,
      valor_copago: editForm.value.valor_copago,
      valor_estudios_no_autorizados: editForm.value.valor_estudios_no_autorizados,
      mutual: editForm.value.mutual.trim().toUpperCase() || undefined,
      nro_afiliado: editForm.value.nro_afiliado.trim() || null,
      observaciones_ingreso: editForm.value.observaciones_ingreso.trim() || null,
      debe_orden_medica: editForm.value.debe_orden_medica,
    };

    await ordenesService.update(props.ordenId, payload as any);
    toast.add({
      severity: 'success',
      summary: 'Orden Actualizada',
      detail: 'Los datos y códigos de auditoría fueron guardados con éxito.',
      life: 3000,
    });
    isEditOrdenVisible.value = false;
    await loadOrden();
    emit('updated');
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo actualizar la orden',
      life: 4000,
    });
  } finally {
    isActionLoading.value = false;
  }
};


const loadOrden = async (isBackgroundRefresh = false) => {
  if (!props.ordenId) return;
  if (!isBackgroundRefresh && !orden.value) {
    isLoading.value = true;
  }
  try {
    orden.value = await ordenesService.getById(props.ordenId);
    if (authStore.isAdmin || authStore.isAuditor) {
      auditors.value = await usersService.listUsers(undefined, undefined);
    }
    if (orden.value.paciente?.id) {
      loadPreviousOrders(orden.value.paciente.id);
    }
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo cargar el expediente de la orden',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => props.ordenId,
  (newId, oldId) => {
    if (newId !== oldId) {
      activeTab.value = '0';
      loadOrden(false);
    }
  }
);

onMounted(async () => {
  const [mutRes, motRes] = await Promise.all([
    mutualesService.list(),
    configService.listMotivosCancelacion(true),
  ]);
  mutuales.value = mutRes;
  motivosCancelacion.value = motRes;
  loadOrden();
});


const handleCambiarEstado = async () => {
  let motivoFinal: string | undefined = undefined;

  if (selectedNuevoEstado.value === 'Cancelada' || selectedNuevoEstado.value === 'Dar de baja') {
    const motivoBase = selectedMotivoCancelacion.value.trim();
    const detalle = motivoEstadoDetalle.value.trim();
    if (!motivoBase && !detalle) {
      toast.add({
        severity: 'warn',
        summary: 'Atención',
        detail: 'Debe seleccionar o indicar el motivo de cancelación / baja',
        life: 3000,
      });
      return;
    }
    motivoFinal = motivoBase ? (detalle ? `${motivoBase} - ${detalle}` : motivoBase) : detalle;
  }

  if (selectedNuevoEstado.value === 'Auditoria Finalizada') {
    if (!observacionResultadoAuditoria.value.trim()) {
      toast.add({
        severity: 'warn',
        summary: 'Atención',
        detail: 'Debe ingresar el resultado/observación de la auditoría para avisar al paciente',
        life: 3500,
      });
      return;
    }
  }

  isActionLoading.value = true;
  try {
    await ordenesService.cambiarEstado(
      props.ordenId,
      selectedNuevoEstado.value,
      motivoFinal,
      null,
      selectedNuevoEstado.value === 'Auditoria Finalizada' ? observacionResultadoAuditoria.value.trim() : null
    );
    toast.add({
      severity: 'success',
      summary: 'Estado Actualizado',
      detail: `La orden pasó a estado ${selectedNuevoEstado.value}`,
      life: 3000,
    });
    isCambioEstadoVisible.value = false;
    selectedMotivoCancelacion.value = '';
    motivoEstadoDetalle.value = '';
    observacionResultadoAuditoria.value = '';
    await loadOrden(true);
    emit('updated');

  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'Error al cambiar estado',
      life: 4000,
    });
  } finally {
    isActionLoading.value = false;
  }
};

const handleCrearSolicitud = async () => {
  if (!motivoSolicitud.value.trim() || !mensajeSolicitud.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Complete el motivo y detalle de la observación', life: 3000 });
    return;
  }
  isActionLoading.value = true;
  try {
    await ordenesService.crearSolicitud(props.ordenId, motivoSolicitud.value, mensajeSolicitud.value);
    toast.add({ severity: 'success', summary: 'Observación Emitida', detail: 'Se notificó la solicitud de auditoría.', life: 3000 });
    isSolicitudVisible.value = false;
    motivoSolicitud.value = 'Falta diagnóstico';
    mensajeSolicitud.value = '';
    await loadOrden(true);
    emit('updated');

  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al crear solicitud', life: 4000 });
  } finally {
    isActionLoading.value = false;
  }
};

const handleResponderSolicitud = async () => {
  if (!selectedSolicitudId.value || !respuestaOperador.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Ingrese la respuesta para el auditor', life: 3000 });
    return;
  }
  isActionLoading.value = true;
  try {
    await ordenesService.responderSolicitud(selectedSolicitudId.value, respuestaOperador.value);
    toast.add({ severity: 'success', summary: 'Respuesta Enviada', detail: 'La orden pasó a estado Actualizada.', life: 3000 });
    isResponderVisible.value = false;
    respuestaOperador.value = '';
    selectedSolicitudId.value = null;
    await loadOrden(true);
    emit('updated');

  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al responder', life: 4000 });
  } finally {
    isActionLoading.value = false;
  }
};

const handleAsignarAuditor = async () => {
  isActionLoading.value = true;
  try {
    await ordenesService.asignarAuditor(props.ordenId, selectedAuditorId.value);
    toast.add({ severity: 'success', summary: 'Auditor Asignado', detail: 'Se actualizó el auditor responsable.', life: 3000 });
    isAsignarAuditorVisible.value = false;
    await loadOrden(true);
    emit('updated');

  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al asignar', life: 4000 });
  } finally {
    isActionLoading.value = false;
  }
};

const handleUploadAdjunto = async (event: any) => {
  const file = event.files[0];
  if (!file) return;
  try {
    await ordenesService.subirAdjunto(props.ordenId, file);
    toast.add({ severity: 'success', summary: 'Archivo Adjuntado', detail: 'Se subió el archivo correctamente.', life: 3000 });
    await loadOrden(true);
    emit('updated');

  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al subir archivo', life: 4000 });
  }
};

const handleDeleteAdjunto = async (adjunto: AdjuntoOrden) => {
  if (!confirm(`¿Está seguro de eliminar el archivo adjunto "${adjunto.nombre_archivo_original}"?`)) {
    return;
  }
  try {
    await ordenesService.eliminarAdjunto(adjunto.id);
    toast.add({ severity: 'success', summary: 'Archivo Eliminado', detail: 'El archivo adjunto fue eliminado con éxito.', life: 3000 });
    await loadOrden(true);
    emit('updated');
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'No se pudo eliminar el archivo', life: 4000 });
  }
};

const handleLlamadaSuccess = async () => {
  await loadOrden(true);
  emit('updated');
};

const handleAddAuditNumber = async () => {
  const num = nuevoNumeroAuditoria.value.trim().toUpperCase();
  if (!num || !orden.value) return;

  const currentList = orden.value.numeros_auditoria || [];
  if (currentList.includes(num)) {
    toast.add({ severity: 'warn', summary: 'Código Duplicado', detail: 'Este código ya está en la lista', life: 3000 });
    return;
  }

  isAddingAuditNumber.value = true;
  try {
    const updatedList = [...currentList, num];
    await ordenesService.update(props.ordenId, {
      numeros_auditoria: updatedList,
    });
    toast.add({ severity: 'success', summary: 'Número de Auditoría Agregado', detail: `Código ${num} incorporado.`, life: 3000 });
    nuevoNumeroAuditoria.value = '';
    await loadOrden(true);
    emit('updated');
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'No se pudo agregar el código', life: 4000 });
  } finally {
    isAddingAuditNumber.value = false;
  }
};

const handleDeleteAuditNumber = async (numToDelete: string) => {
  if (!orden.value) return;
  const updatedList = (orden.value.numeros_auditoria || []).filter((n) => n !== numToDelete);
  try {
    await ordenesService.update(props.ordenId, {
      numeros_auditoria: updatedList,
    });
    toast.add({ severity: 'info', summary: 'Código Eliminado', detail: `Se removió ${numToDelete}.`, life: 3000 });
    await loadOrden(true);
    emit('updated');
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el código', life: 4000 });
  }
};


const handleOpenPreview = async (adj: AdjuntoOrden) => {
  previewFile.value = adj;
  isPreviewVisible.value = true;
  isLoadingPreview.value = true;
  try {
    const blob = await ordenesService.getAdjuntoBlob(adj.id);
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value);
    }
    previewUrl.value = URL.createObjectURL(blob);
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cargar la vista previa', life: 3000 });
  } finally {
    isLoadingPreview.value = false;
  }
};

const loadPreviousOrders = async (pacienteId: string) => {
  isLoadingPrevOrders.value = true;
  try {
    const res = await ordenesService.list({ paciente_id: pacienteId, limit: 50 });
    prevOrders.value = res.items.filter((o) => o.id !== props.ordenId);
  } catch {
    prevOrders.value = [];
  } finally {
    isLoadingPrevOrders.value = false;
  }
};

</script>

<template>
  <div class="h-full flex flex-col bg-white rounded-xl border border-slate-200 shadow-md overflow-hidden animate-fadeIn">
    <LoadingSpinner v-if="isLoading" message="Cargando expediente..." class="py-12" />

    <template v-else-if="orden">
      <!-- Panel Header -->
      <div class="p-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
        <div class="flex items-center space-x-3 truncate">
          <span class="font-mono text-lg font-bold text-blue-400">{{ orden.nro_orden }}</span>
          <StatusTag :value="orden.estado" />
        </div>

        <div class="flex items-center space-x-1.5">
          <Button
            icon="pi pi-window-maximize"
            label="Pantalla Completa"
            text
            size="small"
            class="text-blue-300 hover:text-white hover:bg-slate-800 text-xs py-1 px-2.5 rounded-lg transition"
            @click="router.push(`/ordenes/${orden.id}`)"
            title="Abrir expediente en pantalla completa"
          />
          <Button
            icon="pi pi-times"
            text
            rounded
            severity="secondary"
            class="text-slate-300 hover:text-white hover:bg-slate-800"
            @click="emit('close')"
            title="Cerrar vista de detalle"
          />
        </div>
      </div>

      <!-- Action Bar -->
      <div class="p-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center gap-2">
        <!-- Botón Llamada Pendiente -->
        <Button
          v-if="
            (orden.estado === 'Solicitudes de auditoria' && !orden.llamada_solicitud_completada) ||
            (orden.estado === 'Auditoria Finalizada' && !orden.llamada_finalizada_completada)
          "
          label="Avisar a Paciente"
          icon="pi pi-phone"
          severity="danger"
          size="small"
          @click="isLlamadaModalVisible = true"
        />

        <!-- Auditor Action: Emitir Observación -->
        <Button
          v-if="authStore.isAdmin || authStore.isAuditor"
          label="Observación del Auditor"
          icon="pi pi-exclamation-triangle"
          severity="warn"
          size="small"
          @click="isSolicitudVisible = true"
        />

        <!-- Cambiar Estado -->
        <Button
          label="Cambiar Estado"
          icon="pi pi-sync"
          severity="secondary"
          size="small"
          @click="isCambioEstadoVisible = true"
        />

        <!-- Editar Datos -->
        <Button
          label="Editar Datos"
          icon="pi pi-pencil"
          severity="info"
          outlined
          size="small"
          @click="handleOpenEditOrden"
        />


        <!-- Asignar Auditor (Admin) -->
        <Button
          v-if="authStore.isAdmin"
          icon="pi pi-user-plus"
          label="Auditor"
          text
          severity="secondary"
          size="small"
          @click="isAsignarAuditorVisible = true"
        />
      </div>

      <!-- Scrollable Body Content -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Alerta Roja: Paciente Debe Orden Fisica -->
        <div
          v-if="orden.debe_orden_medica"
          class="p-3 bg-red-100 border border-red-300 rounded-xl text-red-900 text-xs flex items-center space-x-2.5 shadow-sm"
        >
          <i class="pi pi-exclamation-triangle text-red-600 text-lg flex-shrink-0 animate-pulse"></i>
          <div>
            <span class="font-bold uppercase block text-[11px] text-red-900">¡ATENCIÓN! EL PACIENTE DEBE LA ORDEN MÉDICA FÍSICA</span>
            <span class="text-[10px] text-red-700 font-medium">Recibida por mail/digital. Exigir la receta médica física original al momento de la toma de muestra.</span>
          </div>
        </div>

        <!-- Patient & Order Details Card -->
        <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 grid grid-cols-2 gap-3 text-xs">
          <div>
            <p class="text-[10px] font-bold text-slate-400 uppercase">Paciente</p>
            <p class="font-bold text-slate-800 text-sm truncate">{{ orden.paciente?.nombre_completo }}</p>
            <p class="text-slate-500">DNI: {{ orden.paciente?.documento }}</p>
            <p v-if="orden.nro_afiliado || orden.paciente?.nro_afiliado" class="text-slate-500 text-[11px]">
              Afiliado: <span class="font-medium text-slate-700">{{ orden.nro_afiliado || orden.paciente?.nro_afiliado }}</span>
            </p>
          </div>
          <div>
            <p class="text-[10px] font-bold text-slate-400 uppercase">Mutual & Valores</p>
            <p class="font-bold text-slate-800 text-sm truncate">{{ orden.mutual }}</p>
            <div class="mt-0.5 space-y-0.5">
              <p class="text-slate-900 font-bold text-xs">
                Total a abonar: ${{ (Number(orden.valor_copago || 0) + Number(orden.valor_estudios_no_autorizados || 0)).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
              </p>
              <div class="flex items-center gap-1.5 text-[11px] text-slate-500">
                <span class="text-blue-700 font-medium">${{ Number(orden.valor_copago || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }} copago</span>
                <span v-if="Number(orden.valor_estudios_no_autorizados) > 0" class="text-red-600 font-medium">
                  &bull; ${{ Number(orden.valor_estudios_no_autorizados).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }} no aut.
                </span>
              </div>
            </div>
          </div>


          <div class="border-t border-slate-200 pt-2">
            <p class="text-slate-500"><span class="font-semibold">Prescripción:</span> {{ orden.fecha_prescripcion }}</p>
            <p class="text-slate-500"><span class="font-semibold">Recetas:</span> {{ orden.cantidad_ordenes_fisicas }}</p>
          </div>
          <div class="border-t border-slate-200 pt-2">
            <p class="text-slate-500"><span class="font-semibold">Sucursal:</span> {{ orden.sucursal?.nombre }}</p>
            <p class="text-slate-500"><span class="font-semibold">Auditor:</span> {{ orden.assigned_auditor?.full_name || 'Sin asignar' }}</p>
          </div>
        </div>

        <!-- Contact & Phone Strip -->
        <div class="p-2.5 bg-blue-50 rounded-lg border border-blue-200 flex items-center justify-between text-xs">
          <div class="flex items-center space-x-2 text-blue-900">
            <i class="pi pi-phone text-blue-600"></i>
            <span class="font-medium">
              {{ orden.contacto_telefono || orden.contacto_celular || orden.paciente?.telefono || 'Sin teléfono' }}
            </span>
            <span v-if="orden.contacto_horario" class="text-slate-500 text-[11px]">({{ orden.contacto_horario }})</span>
          </div>
          <span v-if="orden.contacto_nombre" class="text-slate-600 text-[11px] font-semibold truncate">
            Contacto: {{ orden.contacto_nombre }}
          </span>
        </div>


        <!-- Observaciones de Ingreso / Notas Iniciales -->
        <div v-if="orden.observaciones_ingreso" class="p-2.5 bg-amber-50/70 rounded-lg border border-amber-200 text-xs space-y-1">
          <p class="text-[10px] font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1">
            <i class="pi pi-info-circle text-amber-600"></i> Observaciones de Ingreso
          </p>
          <p class="text-slate-700 italic">"{{ orden.observaciones_ingreso }}"</p>
        </div>

        <!-- Multiple Audit Codes -->
        <div v-if="orden.numeros_auditoria && orden.numeros_auditoria.length > 0" class="flex flex-wrap items-center gap-1.5 p-2.5 bg-slate-50 rounded-lg border border-slate-200">
          <span class="text-[11px] font-bold text-slate-500 uppercase">Números de Auditoría:</span>
          <span class="font-mono text-xs font-bold text-slate-800">
            {{ orden.numeros_auditoria.join(', ') }}
          </span>
        </div>

        <!-- Tabs Section -->
        <div class="border border-slate-200 rounded-lg overflow-hidden">
          <Tabs v-model:value="activeTab">
            <TabList>
              <Tab value="0" class="text-xs">Observaciones ({{ orden.solicitudes.length }})</Tab>
              <Tab value="1" class="text-xs">Adjuntos ({{ orden.adjuntos.length }})</Tab>
              <Tab value="2" class="text-xs">Llamadas ({{ orden.llamadas_registro.length }})</Tab>
              <Tab value="3" class="text-xs font-semibold text-blue-800">Códigos Auditoría ({{ orden.numeros_auditoria?.length || 0 }})</Tab>
              <Tab value="4" class="text-xs">Bitácora</Tab>
              <Tab value="5" class="text-xs font-semibold text-slate-800">Auditorías Previas ({{ prevOrders.length }})</Tab>
            </TabList>
            <TabPanels>
              <!-- Tab 0: Observaciones -->
              <TabPanel value="0">
                <div class="space-y-3 p-1">
                  <div v-if="orden.solicitudes.length === 0" class="text-center py-6 text-xs text-slate-400">
                    No hay solicitudes u observaciones de auditoría.
                  </div>
                  <div
                    v-for="sol in orden.solicitudes"
                    :key="sol.id"
                    class="p-3 rounded-lg border border-slate-200 space-y-2 text-xs"
                    :class="sol.estado === 'PENDIENTE' ? 'bg-amber-50/60 border-amber-300' : 'bg-slate-50'"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-amber-900 uppercase">{{ sol.motivo_solicitud }}</span>
                      <span
                        class="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase"
                        :class="sol.estado === 'PENDIENTE' ? 'bg-amber-200 text-amber-900' : 'bg-emerald-100 text-emerald-800'"
                      >
                        {{ sol.estado }}
                      </span>
                    </div>
                    <p class="text-slate-700 bg-white p-2 rounded border border-slate-200">{{ sol.mensaje_auditor }}</p>

                    <!-- Respuesta -->
                    <div v-if="sol.respuesta_operador" class="p-2 bg-emerald-50 rounded border border-emerald-200">
                      <p class="font-bold text-emerald-800 text-[10px] uppercase">Respuesta de Sucursal</p>
                      <p class="text-slate-700 mt-0.5">{{ sol.respuesta_operador }}</p>
                    </div>

                    <!-- Botón Responder -->
                    <div v-else-if="sol.estado === 'PENDIENTE'" class="pt-1">
                      <Button
                        label="Responder Observación"
                        icon="pi pi-reply"
                        size="small"
                        severity="primary"
                        class="text-xs"
                        @click="selectedSolicitudId = sol.id; isResponderVisible = true"
                      />
                    </div>
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 1: Adjuntos -->
              <TabPanel value="1">
                <div class="space-y-3 p-1">
                  <div class="p-3 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50 text-center">
                    <FileUpload
                      mode="basic"
                      name="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      :maxFileSize="10000000"
                      chooseLabel="Subir Foto / Receta (PDF, PNG, JPG)"
                      customUpload
                      auto
                      @uploader="handleUploadAdjunto"
                    />
                  </div>

                  <div v-if="orden.adjuntos.length > 0" class="space-y-2">
                    <div
                      v-for="adj in orden.adjuntos"
                      :key="adj.id"
                      class="p-2.5 rounded-lg border border-slate-200 flex items-center justify-between text-xs hover:bg-slate-50 transition"
                    >
                      <div class="flex items-center space-x-2 truncate cursor-pointer" @click="handleOpenPreview(adj)">
                        <i :class="adj.tipo_mime.includes('pdf') ? 'pi pi-file-pdf text-red-500' : 'pi pi-image text-blue-500'" class="text-lg"></i>
                        <div class="truncate">
                          <span class="font-semibold text-slate-800 hover:text-emerald-700 truncate block">{{ adj.nombre_archivo_original }}</span>
                          <span class="text-[10px] text-slate-400">{{ (adj.tamano_bytes / 1024).toFixed(1) }} KB</span>
                        </div>
                      </div>
                      <div class="flex items-center space-x-1">
                        <Button icon="pi pi-eye" text rounded severity="primary" size="small" title="Ver en pantalla (Popup)" @click="handleOpenPreview(adj)" />
                        <a :href="ordenesService.getDescargarAdjuntoUrl(adj.id)" target="_blank">
                          <Button icon="pi pi-download" text rounded severity="secondary" size="small" title="Descargar" />
                        </a>
                        <Button
                          icon="pi pi-trash"
                          text
                          rounded
                          severity="danger"
                          size="small"
                          title="Eliminar archivo adjunto"
                          @click="handleDeleteAdjunto(adj)"
                        />
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-center py-4 text-xs text-slate-400">
                    No hay archivos adjuntos.
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 2: Llamadas -->
              <TabPanel value="2">
                <div class="space-y-2 p-1">
                  <div v-if="orden.llamadas_registro.length === 0" class="text-center py-6 text-xs text-slate-400">
                    No hay registros de llamadas.
                  </div>
                  <div
                    v-for="ll in orden.llamadas_registro"
                    :key="ll.id"
                    class="p-2.5 rounded border border-slate-200 bg-slate-50 text-xs space-y-1"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-slate-800">{{ ll.resultado }}</span>
                      <span class="text-slate-400 text-[10px]">{{ ll.created_at.slice(0, 16).replace('T', ' ') }}</span>
                    </div>
                    <p class="text-slate-500">Operador: {{ ll.operador?.full_name }}</p>
                    <p v-if="ll.observaciones" class="italic text-slate-700">"{{ ll.observaciones }}"</p>
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 3: Números de Auditoría (Individuales con Add / Delete) -->
              <TabPanel value="3">
                <div class="p-3 space-y-4 text-xs">
                  <!-- Form para cargar 1 número -->
                  <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                    <label class="block font-bold text-slate-700 uppercase text-[11px]">
                      Cargar Número de Autorización / Auditoría
                    </label>
                    <div class="flex gap-2">
                      <InputText
                        v-model="nuevoNumeroAuditoria"
                        placeholder="Ej: AUT-9901"
                        class="flex-1 text-xs uppercase"
                        @keyup.enter="handleAddAuditNumber"
                      />
                      <Button
                        label="Agregar Número"
                        icon="pi pi-plus"
                        size="small"
                        severity="success"
                        :loading="isAddingAuditNumber"
                        @click="handleAddAuditNumber"
                      />
                    </div>
                    <p class="text-[10px] text-slate-500">
                      * Cada número se guardará de inmediato en la base de datos y pasará la orden a <strong>en Auditoria</strong> si estaba en Ingreso.
                    </p>
                  </div>

                  <!-- Lista de Números Cargados -->
                  <div>
                    <h5 class="font-bold text-slate-700 uppercase text-[11px] mb-2">
                      Códigos Autorizados Actuales ({{ orden.numeros_auditoria?.length || 0 }})
                    </h5>
                    <div v-if="orden.numeros_auditoria && orden.numeros_auditoria.length > 0" class="space-y-1.5">
                      <div
                        v-for="code in orden.numeros_auditoria"
                        :key="code"
                        class="p-2 rounded bg-white border border-slate-200 flex items-center justify-between shadow-sm"
                      >
                        <div class="flex items-center space-x-2">
                          <i class="pi pi-check text-emerald-600 text-xs"></i>
                          <span class="font-mono text-xs font-bold text-slate-800">{{ code }}</span>
                        </div>
                        <Button
                          icon="pi pi-trash"
                          text
                          rounded
                          severity="danger"
                          size="small"
                          title="Eliminar este código"
                          @click="handleDeleteAuditNumber(code)"
                        />
                      </div>
                    </div>
                    <div v-else class="text-center py-6 text-slate-400 italic">
                      No hay números de auditoría cargados para esta orden.
                    </div>
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 4: Audit Trail -->
              <TabPanel value="4">
                <div class="p-1">
                  <Timeline :value="orden.audit_logs">
                    <template #content="{ item }">
                      <div class="mb-3 text-xs">
                        <p class="font-bold text-slate-800">{{ item.accion }}</p>
                        <p v-if="item.estado_anterior" class="text-slate-500 text-[11px]">
                          {{ item.estado_anterior }} ➔ <span class="font-semibold text-emerald-700">{{ item.estado_nuevo }}</span>
                        </p>
                        <p class="text-[10px] text-slate-400">
                          {{ item.user?.full_name || 'Sistema' }} &bull; {{ item.created_at.slice(0, 16).replace('T', ' ') }}
                        </p>
                      </div>
                    </template>
                  </Timeline>
                </div>
              </TabPanel>

              <!-- Tab 5: Auditorías Previas del Paciente -->
              <TabPanel value="5">
                <div class="p-2 space-y-2">
                  <div v-if="prevOrders.length > 0" class="space-y-2">
                    <div
                      v-for="po in prevOrders"
                      :key="po.id"
                      class="p-3 bg-white rounded-lg border border-slate-200 shadow-sm flex items-center justify-between text-xs hover:border-emerald-300 transition"
                    >
                      <div class="space-y-0.5">
                        <div class="flex items-center space-x-2">
                          <span class="font-mono font-bold text-slate-900">{{ po.nro_orden }}</span>
                          <StatusTag :value="po.estado" />
                        </div>
                        <p class="text-slate-500">Prescripción: {{ po.fecha_prescripcion }} &bull; Mutual: {{ po.mutual }} &bull; Copago: ${{ po.valor_copago }}</p>
                        <p v-if="po.numeros_auditoria && po.numeros_auditoria.length > 0" class="text-[10px] text-slate-600 font-mono">
                          Códigos: {{ po.numeros_auditoria.join(', ') }}
                        </p>
                      </div>
                      <Button
                        label="Ver Orden"
                        icon="pi pi-external-link"
                        text
                        size="small"
                        severity="primary"
                        @click="$emit('close'); $router.push(`/ordenes?selected=${po.id}`)"
                      />
                    </div>
                  </div>
                  <div v-else class="text-center py-8 text-xs text-slate-400 italic">
                    Este paciente no registra otras órdenes médicas anteriores en el sistema.
                  </div>
                </div>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>

      </div>
    </template>

    <!-- Modals -->
    <!-- Modal Cambiar Estado -->
    <Dialog v-model:visible="isCambioEstadoVisible" modal header="Cambiar Estado de la Orden" :style="{ width: '480px' }">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nuevo Estado</label>
          <Dropdown
            v-model="selectedNuevoEstado"
            :options="['Ingreso', 'en Auditoria', 'Solicitudes de auditoria', 'Actualizada', 'Auditoria Finalizada', 'Dar de baja', 'Cancelada', 'Cerrada']"
            class="w-full text-xs"
          />
        </div>

        <!-- Si pasa a Cancelada o Dar de baja -->
        <div v-if="selectedNuevoEstado === 'Cancelada' || selectedNuevoEstado === 'Dar de baja'" class="space-y-3 bg-red-50/60 p-3 rounded-lg border border-red-200">
          <div>
            <label class="block text-xs font-bold text-red-900 uppercase mb-1">
              Motivo Normalizado <span class="text-red-600">*</span>
            </label>
            <Dropdown
              v-model="selectedMotivoCancelacion"
              :options="motivosCancelacion"
              optionLabel="nombre"
              optionValue="nombre"
              placeholder="Seleccione motivo de cancelación..."
              class="w-full text-xs"
              editable
            />
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-700 mb-1">Detalle o aclaración adicional</label>
            <Textarea v-model="motivoEstadoDetalle" rows="2" class="w-full text-xs" placeholder="Detalle particular de la anulación..." />
          </div>
        </div>

        <!-- Si pasa a Auditoria Finalizada -->
        <div v-if="selectedNuevoEstado === 'Auditoria Finalizada'" class="space-y-3 bg-blue-50/60 p-3 rounded-lg border border-blue-200">
          <div class="flex items-start gap-2 text-blue-900 text-xs">
            <i class="pi pi-info-circle text-blue-600 text-sm mt-0.5"></i>
            <p>La orden pasará a <strong>Llamadas Pendientes</strong> para notificar al paciente el resultado y convocarlo a la toma de muestra.</p>
          </div>
          <div>
            <label class="block text-xs font-bold text-blue-900 uppercase mb-1">
              Resultado / Observación de la Auditoría <span class="text-red-500">*</span>
            </label>
            <Textarea
              v-model="observacionResultadoAuditoria"
              rows="3"
              class="w-full text-xs"
              placeholder="Ej: Aprobada 100%. Se autorizan todas las prácticas solicitadas..."
            />
          </div>
        </div>

        <!-- Si pasa a Cerrada -->
        <div v-if="selectedNuevoEstado === 'Cerrada'" class="p-3 bg-emerald-50 rounded-lg border border-emerald-200 text-xs text-emerald-900 flex items-center gap-2">
          <i class="pi pi-check-circle text-emerald-600 text-base"></i>
          <p><strong>Cierre exitoso:</strong> El paciente ya asistió al laboratorio y se completaron los estudios médicos.</p>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isCambioEstadoVisible = false" />
        <Button label="Guardar Cambio" severity="primary" :loading="isActionLoading" @click="handleCambiarEstado" />
      </template>
    </Dialog>

    <!-- Modal Crear Observacion -->
    <Dialog v-model:visible="isSolicitudVisible" modal header="Emitir Observación del Auditor" :style="{ width: '480px' }">
      <div class="space-y-3">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Motivo Principal <span class="text-red-500">*</span></label>
          <Dropdown
            v-model="motivoSolicitud"
            :options="['Falta diagnóstico', 'Firma/Sello ilegible', 'Estudio no coincide con pedido', 'Falta resumen clínico', 'Otro']"
            editable
            placeholder="Seleccione o escriba..."
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Mensaje para Sucursal <span class="text-red-500">*</span></label>
          <Textarea v-model="mensajeSolicitud" rows="4" class="w-full" placeholder="Detalle lo solicitado..." />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isSolicitudVisible = false" />
        <Button label="Emitir" severity="warn" :loading="isActionLoading" @click="handleCrearSolicitud" />
      </template>
    </Dialog>

    <!-- Modal Responder Observacion -->
    <Dialog v-model:visible="isResponderVisible" modal header="Responder Observación del Auditor" :style="{ width: '480px' }">
      <div class="space-y-3">
        <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Respuesta y Aclaración <span class="text-red-500">*</span></label>
        <Textarea v-model="respuestaOperador" rows="4" class="w-full" placeholder="Indique las correcciones..." />
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isResponderVisible = false" />
        <Button label="Enviar" severity="primary" :loading="isActionLoading" @click="handleResponderSolicitud" />
      </template>
    </Dialog>

    <!-- Modal Asignar Auditor -->
    <Dialog v-model:visible="isAsignarAuditorVisible" modal header="Asignar Auditor" :style="{ width: '380px' }">
      <div class="space-y-3">
        <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Auditor Médico</label>
        <Dropdown
          v-model="selectedAuditorId"
          :options="auditors"
          optionLabel="full_name"
          optionValue="id"
          placeholder="Seleccionar auditor"
          class="w-full"
        />
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isAsignarAuditorVisible = false" />
        <Button label="Asignar" :loading="isActionLoading" @click="handleAsignarAuditor" />
      </template>
    </Dialog>

    <!-- Modal Editar Datos de la Orden -->
    <Dialog v-model:visible="isEditOrdenVisible" modal header="Editar Datos de la Orden" :style="{ width: '560px' }">
      <div class="space-y-4">
        <!-- Códigos de Auditoría -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Códigos de Auditoría (Escriba y presione Enter / Borre con X)
          </label>
          <Chips v-model="editForm.numeros_auditoria" placeholder="Ej: AUT-101, AUT-102..." class="w-full" />
          <p class="text-[11px] text-slate-500 mt-1">
            * Nota: Al agregar un código de auditoría, la orden pasará automáticamente a estado <strong>en Auditoria</strong>.
          </p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Copago a Abonar ($)</label>
            <InputNumber v-model="editForm.valor_copago" mode="currency" currency="ARS" locale="es-AR" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Estudios No Autorizados ($)</label>
            <InputNumber v-model="editForm.valor_estudios_no_autorizados" mode="currency" currency="ARS" locale="es-AR" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Mutual / Cobertura</label>
            <Dropdown
              v-model="editForm.mutual"
              :options="mutuales"
              optionLabel="display_name"
              optionValue="sigla"
              placeholder="Seleccionar mutual..."
              filter
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">N° Afiliado / Credencial</label>
            <InputText v-model="editForm.nro_afiliado" placeholder="Ej: 12345678/01" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombre de Contacto</label>
            <InputText v-model="editForm.contacto_nombre" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Horario Preferido</label>
            <Dropdown
              v-model="editForm.contacto_horario"
              :options="opcionesHorarios"
              placeholder="Seleccionar horario"
              class="w-full"
            />
          </div>
        </div>


        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Teléfono</label>
            <InputText v-model="editForm.contacto_telefono" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Celular / WhatsApp</label>
            <InputText v-model="editForm.contacto_celular" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Correo Electrónico</label>
            <InputText v-model="editForm.contacto_email" type="email" class="w-full" />
          </div>
        </div>


        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Observaciones</label>
          <Textarea v-model="editForm.observaciones_ingreso" rows="2" class="w-full text-xs" />
        </div>

        <!-- Checkbox Debe Orden Medica Fisica -->
        <div class="p-2.5 bg-red-50 rounded-lg border border-red-200 flex items-center space-x-2">
          <Checkbox v-model="editForm.debe_orden_medica" binary inputId="editDebeOrdenFisicaPanel" />
          <label for="editDebeOrdenFisicaPanel" class="text-xs font-bold text-red-900 cursor-pointer">
            ⚠️ Paciente DEBE la Orden Médica Física (Recibida por mail / digital)
          </label>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isEditOrdenVisible = false" />
        <Button label="Guardar Cambios" icon="pi pi-check" :loading="isActionLoading" @click="handleSaveEditOrden" />
      </template>
    </Dialog>

    <!-- Modal Registrar Llamada -->

    <!-- Modal Previsualización de Archivo / Popup Viewer -->
    <Dialog
      v-model:visible="isPreviewVisible"
      modal
      :header="previewFile ? `Visualizador de Documento - ${previewFile.nombre_archivo_original}` : 'Visualizador de Documento'"
      :style="{ width: '85vw', maxWidth: '1000px' }"
      :contentStyle="{ height: '80vh', padding: '0' }"
      dismissableMask
    >
      <div class="h-full w-full flex items-center justify-center bg-slate-900 text-white relative">
        <LoadingSpinner v-if="isLoadingPreview" message="Cargando documento..." />

        <!-- Visor PDF -->
        <iframe
          v-else-if="previewFile && previewUrl && (previewFile.tipo_mime.includes('pdf') || previewFile.nombre_archivo_original.toLowerCase().endsWith('.pdf'))"
          :src="previewUrl"
          class="w-full h-full border-0 bg-white"
        />

        <!-- Visor Imagen -->
        <div
          v-else-if="previewFile && previewUrl"
          class="w-full h-full p-4 flex items-center justify-center overflow-auto"
        >
          <img
            :src="previewUrl"
            :alt="previewFile.nombre_archivo_original"
            class="max-w-full max-h-full object-contain rounded shadow-lg"
          />
        </div>

        <div v-else class="p-8 text-center text-sm text-slate-400">
          No se pudo generar la vista previa del archivo.
        </div>
      </div>
    </Dialog>

    <RegistrarLlamadaModal
      v-if="orden"

      v-model:visible="isLlamadaModalVisible"
      :ordenId="orden.id"
      :nroOrden="orden.nro_orden"
      :pacienteNombre="orden.paciente.nombre_completo"
      :telefono="orden.contacto_telefono || orden.contacto_celular || orden.paciente.telefono"
      :tipoLlamada="orden.estado === 'Solicitudes de auditoria' ? 'SOLICITUD_AUDITORIA' : 'AUDITORIA_FINALIZADA'"
      @success="handleLlamadaSuccess"
    />
  </div>
</template>
