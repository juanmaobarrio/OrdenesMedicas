<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ordenesService } from '../../services/ordenes.service';
import { usersService } from '../../services/users.service';
import { mutualesService } from '../../services/mutuales.service';
import { configService } from '../../services/config.service';
import { useAuthStore } from '../../stores/auth.store';
import { EstadoOrden, OrdenMedicaDetail, OrdenMedicaListItem, AdjuntoOrden, ObraSocial, UserDetail, MotivoCancelacion } from '../../types';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dialog from 'primevue/dialog';
import Dropdown from 'primevue/dropdown';
import Textarea from 'primevue/textarea';
import FileUpload from 'primevue/fileupload';
import Checkbox from 'primevue/checkbox';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import Timeline from 'primevue/timeline';
import StatusTag from '../../components/common/StatusTag.vue';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import RegistrarLlamadaModal from '../../components/ordenes/RegistrarLlamadaModal.vue';
import { formatDate, formatDateTime } from '../../utils/date';
import { useToast } from 'primevue/usetoast';

const route = useRoute();
const router = useRouter();
const toast = useToast();
const authStore = useAuthStore();

const ordenId = route.params.id as string;
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
const esInformativa = ref(false);

const isResponderVisible = ref(false);
const selectedSolicitudId = ref<string | null>(null);
const respuestaOperador = ref('');

const isAsignarAuditorVisible = ref(false);
const selectedAuditorId = ref<string | null>(null);

const isLlamadaModalVisible = ref(false);
const isDirectLlamadaVisible = ref(false);
const directLlamadaForm = ref({
  tipo_llamada: 'CONSULTA_PACIENTE' as any,
  resultado: 'EXITOSA' as any,
  observaciones: '',
  completar_aviso_pendiente: true,
});

const opcionesTiposLlamada = [
  { label: '📞 Consulta del Paciente (Entrante)', value: 'CONSULTA_PACIENTE' },
  { label: '📤 Aviso / Seguimiento de Sucursal (Saliente)', value: 'SEGUIMIENTO_SUCURSAL' },
  { label: '⚠️ Aviso de Solicitud de Auditoría', value: 'SOLICITUD_AUDITORIA' },
  { label: '✅ Aviso de Auditoría Finalizada', value: 'AUDITORIA_FINALIZADA' },
  { label: '📝 Otro Motivo de Contacto', value: 'OTRO' },
];

const opcionesResultadosLlamada = [
  { label: 'Contacto Exitoso (EXITOSA)', value: 'EXITOSA' },
  { label: 'No Contesta (NO_CONTESTA)', value: 'NO_CONTESTA' },
  { label: 'Número Erróneo / Inexistente (NUMERO_ERRONEO)', value: 'NUMERO_ERRONEO' },
  { label: 'Reintentar más tarde (REINTENTAR)', value: 'REINTENTAR' },
];

const formatTipoLlamada = (tipo: string) => {
  switch (tipo) {
    case 'CONSULTA_PACIENTE':
      return 'Consulta del Paciente';
    case 'SEGUIMIENTO_SUCURSAL':
      return 'Seguimiento de Sucursal';
    case 'SOLICITUD_AUDITORIA':
      return 'Solicitud de Auditoría';
    case 'AUDITORIA_FINALIZADA':
      return 'Auditoría Finalizada';
    case 'OTRO':
      return 'Otro Contacto';
    default:
      return tipo;
  }
};

const isEditOrdenVisible = ref(false);
const isActionLoading = ref(false);
const activeTab = ref('0');

// Números de Auditoría
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
  abona_apb: false,
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
    abona_apb: Boolean(orden.value.abona_apb),
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
      abona_apb: editForm.value.abona_apb,
      mutual: editForm.value.mutual.trim().toUpperCase() || undefined,
      nro_afiliado: editForm.value.nro_afiliado.trim() || null,
      observaciones_ingreso: editForm.value.observaciones_ingreso.trim() || null,
      debe_orden_medica: editForm.value.debe_orden_medica,
    };

    await ordenesService.update(ordenId, payload as any);
    toast.add({
      severity: 'success',
      summary: 'Orden Actualizada',
      detail: 'Los datos fueron guardados con éxito.',
      life: 3000,
    });
    isEditOrdenVisible.value = false;
    await loadOrden(true);
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

const loadOrden = async (isBackground = false) => {
  if (!isBackground) isLoading.value = true;
  try {
    orden.value = await ordenesService.getById(ordenId);
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
      detail: 'No se pudo cargar la orden médica',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

const loadPreviousOrders = async (pacienteId: string) => {
  isLoadingPrevOrders.value = true;
  try {
    const res = await ordenesService.list({ paciente_id: pacienteId, limit: 50 });
    prevOrders.value = res.items.filter((o) => o.id !== ordenId);
  } catch {
    prevOrders.value = [];
  } finally {
    isLoadingPrevOrders.value = false;
  }
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
    await ordenesService.update(ordenId, { numeros_auditoria: updatedList });
    nuevoNumeroAuditoria.value = '';
    await loadOrden(true);
    toast.add({ severity: 'success', summary: 'Código Agregado', detail: `Código ${num} añadido.`, life: 2500 });
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo guardar el código', life: 3000 });
  } finally {
    isAddingAuditNumber.value = false;
  }
};

const handleRemoveAuditNumber = async (numToRemove: string) => {
  if (!orden.value) return;
  const currentList = orden.value.numeros_auditoria || [];
  const updatedList = currentList.filter((n) => n !== numToRemove);
  try {
    await ordenesService.update(ordenId, { numeros_auditoria: updatedList });
    await loadOrden(true);
    toast.add({ severity: 'info', summary: 'Código Eliminado', detail: `Código ${numToRemove} quitado.`, life: 2500 });
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el código', life: 3000 });
  }
};

const handlePreviewAdjunto = async (adj: AdjuntoOrden) => {
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
      ordenId,
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
    await loadOrden();
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
    await ordenesService.crearSolicitud(
      ordenId,
      motivoSolicitud.value,
      mensajeSolicitud.value,
      esInformativa.value
    );
    toast.add({
      severity: esInformativa.value ? 'info' : 'success',
      summary: esInformativa.value ? 'Información Guardada' : 'Observación Emitida',
      detail: esInformativa.value
        ? 'Se registró la observación de carácter informativo.'
        : 'Se notificó la solicitud de auditoría.',
      life: 3000,
    });
    isSolicitudVisible.value = false;
    motivoSolicitud.value = 'Falta diagnóstico';
    mensajeSolicitud.value = '';
    esInformativa.value = false;
    await loadOrden();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al crear solicitud', life: 4000 });
  } finally {
    isActionLoading.value = false;
  }
};

const openDirectLlamadaModal = () => {
  directLlamadaForm.value = {
    tipo_llamada: 'CONSULTA_PACIENTE',
    resultado: 'EXITOSA',
    observaciones: '',
    completar_aviso_pendiente: true,
  };
  isDirectLlamadaVisible.value = true;
};

const handleSaveDirectLlamada = async () => {
  if (!directLlamadaForm.value.observaciones?.trim()) {
    toast.add({
      severity: 'warn',
      summary: 'Atención',
      detail: 'Ingrese el detalle u observaciones de la conversación',
      life: 3000,
    });
    return;
  }
  isActionLoading.value = true;
  try {
    await ordenesService.registrarLlamada(ordenId, {
      tipo_llamada: directLlamadaForm.value.tipo_llamada,
      resultado: directLlamadaForm.value.resultado,
      observaciones: directLlamadaForm.value.observaciones.trim(),
      completar_aviso_pendiente: directLlamadaForm.value.completar_aviso_pendiente,
    });
    toast.add({
      severity: 'success',
      summary: 'Llamada Registrada',
      detail: directLlamadaForm.value.completar_aviso_pendiente && directLlamadaForm.value.resultado === 'EXITOSA'
        ? 'Se guardó el contacto y se resolvió el aviso pendiente del paciente.'
        : 'Se guardó el contacto en el historial de la orden.',
      life: 3500,
    });
    isDirectLlamadaVisible.value = false;
    await loadOrden();
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo registrar la llamada',
      life: 4000,
    });
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
    await loadOrden();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al responder', life: 4000 });
  } finally {
    isActionLoading.value = false;
  }
};

const handleAsignarAuditor = async () => {
  isActionLoading.value = true;
  try {
    await ordenesService.asignarAuditor(ordenId, selectedAuditorId.value);
    toast.add({ severity: 'success', summary: 'Auditor Asignado', detail: 'Se actualizó el auditor responsable.', life: 3000 });
    isAsignarAuditorVisible.value = false;
    await loadOrden();
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
    await ordenesService.subirAdjunto(ordenId, file);
    toast.add({ severity: 'success', summary: 'Archivo Adjuntado', detail: 'Se subió el archivo correctamente.', life: 3000 });
    await loadOrden();
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
    await loadOrden();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'No se pudo eliminar el archivo', life: 4000 });
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Top Back Navigation -->
    <div class="flex items-center justify-between pb-2 border-b border-slate-200">
      <Button
        icon="pi pi-arrow-left"
        label="Volver al Listado de Órdenes"
        text
        severity="secondary"
        size="small"
        class="text-xs font-semibold text-slate-700 hover:text-blue-700"
        @click="router.push('/ordenes')"
      />
      <span class="text-xs text-slate-400 font-medium">Expediente Completo &bull; Vista Detallada</span>
    </div>

    <LoadingSpinner v-if="isLoading" message="Cargando expediente de la orden médica..." />

    <template v-else-if="orden">
      <!-- Alerta Roja: Paciente Debe Orden Medica Fisica -->
      <div
        v-if="orden.debe_orden_medica"
        class="p-4 bg-red-100 border border-red-300 rounded-xl text-red-900 text-xs flex items-center space-x-3 shadow-sm"
      >
        <i class="pi pi-exclamation-triangle text-red-600 text-2xl flex-shrink-0 animate-pulse"></i>
        <div>
          <span class="font-bold uppercase text-sm block text-red-900">¡ATENCIÓN! EL PACIENTE DEBE LA ORDEN MÉDICA FÍSICA</span>
          <span class="text-xs text-red-800 font-medium">Esta orden fue recibida digitalmente o por correo electrónico. Exigir la entrega de la receta médica física original al momento de la toma de muestra.</span>
        </div>
      </div>

      <!-- Top Bar / Action Card -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center space-x-3">
            <span class="font-mono text-2xl font-bold text-slate-900">{{ orden.nro_orden }}</span>
            <StatusTag :value="orden.estado" />
          </div>
          <p class="text-xs text-slate-500 mt-1">
            Ingresada el {{ orden.created_at.slice(0, 10) }} por {{ orden.created_by_user?.full_name }} &bull; Sede {{ orden.sucursal?.nombre }}
          </p>
        </div>

        <!-- Action Buttons Grid -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- Llamada pendiente button -->
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

          <!-- Auditor Action: Emitir Observacion -->
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

          <!-- Asignar Auditor -->
          <Button
            v-if="authStore.isAdmin"
            icon="pi pi-user-plus"
            label="Asignar Auditor"
            text
            severity="secondary"
            size="small"
            @click="isAsignarAuditorVisible = true"
          />
        </div>
      </div>

      <!-- Main Info & Tabs -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column: Patient & Order Card -->
        <div class="space-y-6">
          <!-- Patient Summary -->
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Ficha del Paciente</h4>
            <div>
              <p class="text-base font-bold text-slate-800">{{ orden.paciente?.nombre_completo }}</p>
              <p class="text-xs text-slate-500">DNI: {{ orden.paciente?.documento }}</p>
            </div>
            <div class="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
              <div class="flex items-center gap-1.5">
                <span class="font-semibold">Obra Social:</span>
                <span class="font-bold text-slate-800">{{ orden.mutual }}</span>
                <span
                  v-if="orden.abona_apb"
                  class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200"
                  title="Abona Acto Profesional Bioquímico"
                >
                  🧪 APB
                </span>
              </div>
              <p><span class="font-semibold">Copago:</span> <span class="text-emerald-700 font-bold">${{ orden.valor_copago }}</span></p>
              <p v-if="Number(orden.valor_estudios_no_autorizados) > 0">
                <span class="font-semibold">No Autorizados:</span> <span class="text-amber-700 font-bold">${{ orden.valor_estudios_no_autorizados }}</span>
              </p>
              <p><span class="font-semibold">Prescripción:</span> {{ formatDate(orden.fecha_prescripcion) }}</p>
              <p><span class="font-semibold">Recetas Físicas:</span> {{ orden.cantidad_ordenes_fisicas }}</p>
              <p v-if="orden.assigned_auditor"><span class="font-semibold">Auditor:</span> {{ orden.assigned_auditor.full_name }}</p>
            </div>
          </div>

          <!-- Contact Details -->
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Datos de Contacto</h4>
            <div class="text-xs space-y-2 text-slate-700">
              <p><i class="pi pi-user mr-1.5 text-slate-400"></i> {{ orden.contacto_nombre || 'No especificado' }}</p>
              <p><i class="pi pi-phone mr-1.5 text-emerald-600"></i> {{ orden.contacto_telefono || orden.contacto_celular || orden.paciente?.telefono || 'Sin teléfono' }}</p>
              <p><i class="pi pi-clock mr-1.5 text-slate-400"></i> {{ orden.contacto_horario || 'Sin horario preferido' }}</p>
              <p><i class="pi pi-envelope mr-1.5 text-slate-400"></i> {{ orden.contacto_email || orden.paciente?.email || 'Sin email' }}</p>
            </div>
          </div>

          <!-- Códigos de Auditoría (Gestor interactivo) -->
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div class="flex items-center justify-between">
              <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Códigos de Auditoría</h4>
              <span class="text-[10px] text-slate-400 font-mono">{{ (orden.numeros_auditoria || []).length }} cargados</span>
            </div>

            <!-- Input para agregar código -->
            <div class="flex items-center space-x-1.5">
              <InputText
                v-model="nuevoNumeroAuditoria"
                placeholder="N° Código..."
                class="w-full text-xs font-mono uppercase"
                @keyup.enter="handleAddAuditNumber"
              />
              <Button
                icon="pi pi-plus"
                size="small"
                severity="primary"
                :loading="isAddingAuditNumber"
                @click="handleAddAuditNumber"
                title="Agregar código"
              />
            </div>

            <!-- Lista de códigos con chips -->
            <div v-if="orden.numeros_auditoria && orden.numeros_auditoria.length > 0" class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="num in orden.numeros_auditoria"
                :key="num"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-50 border border-blue-200 font-mono text-xs font-semibold text-blue-800"
              >
                {{ num }}
                <i
                  class="pi pi-times text-[10px] cursor-pointer text-blue-400 hover:text-red-600 transition"
                  @click="handleRemoveAuditNumber(num)"
                  title="Eliminar este código"
                ></i>
              </span>
            </div>
            <p v-else class="text-[11px] text-slate-400 italic">No hay códigos cargados.</p>
          </div>

          <!-- Observaciones de Ingreso -->
          <div v-if="orden.observaciones_ingreso" class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Observaciones</h4>
            <p class="text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100 italic">
              "{{ orden.observaciones_ingreso }}"
            </p>
          </div>
        </div>

        <!-- Right Column: Tabs (Solicitudes, Adjuntos, Previas, Llamadas, Audit Trail) -->
        <div class="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <Tabs v-model:value="activeTab">
            <TabList>
              <Tab value="0">
                <i class="pi pi-exclamation-circle mr-1"></i> Observaciones ({{ orden.solicitudes?.length || 0 }})
              </Tab>
              <Tab value="1">
                <i class="pi pi-paperclip mr-1"></i> Adjuntos ({{ orden.adjuntos?.length || 0 }})
              </Tab>
              <Tab value="2">
                <i class="pi pi-history mr-1"></i> Auditorías Previas ({{ prevOrders.length }})
              </Tab>
              <Tab value="3">
                <i class="pi pi-phone mr-1"></i> Llamadas ({{ orden.llamadas_registro?.length || 0 }})
              </Tab>
              <Tab value="4">
                <i class="pi pi-list mr-1"></i> Bitácora
              </Tab>
            </TabList>
            <TabPanels>
              <!-- Tab 0: Solicitudes de Auditoría -->
              <TabPanel value="0">
                <div class="p-4 space-y-4">
                  <div v-if="orden.solicitudes.length === 0" class="text-center py-8 text-sm text-slate-400">
                    No hay observaciones de auditoría registradas.
                  </div>
                  <div
                    v-for="sol in orden.solicitudes"
                    :key="sol.id"
                    class="p-4 rounded-xl border space-y-3"
                    :class="{
                      'bg-blue-50/70 border-blue-300 text-blue-900': sol.estado === 'INFORMACION',
                      'bg-amber-50/50 border-amber-200': sol.estado === 'PENDIENTE',
                      'bg-slate-50 border-slate-200': sol.estado !== 'INFORMACION' && sol.estado !== 'PENDIENTE',
                    }"
                  >
                    <div class="flex items-center justify-between">
                      <div>
                        <span
                          class="text-xs font-bold uppercase"
                          :class="sol.estado === 'INFORMACION' ? 'text-blue-950' : 'text-amber-800'"
                        >
                          {{ sol.motivo_solicitud }}
                        </span>
                        <p class="text-xs text-slate-500">Por Dr/a. {{ sol.auditor?.full_name }} &bull; {{ sol.created_at.slice(0, 16).replace('T', ' ') }}</p>
                      </div>
                      <span
                        class="px-2 py-0.5 rounded text-[10px] font-bold uppercase flex items-center gap-1"
                        :class="{
                          'bg-blue-100 text-blue-800 border border-blue-200': sol.estado === 'INFORMACION',
                          'bg-amber-200 text-amber-900': sol.estado === 'PENDIENTE',
                          'bg-emerald-100 text-emerald-800': sol.estado === 'RESPONDIDA' || sol.estado === 'CERRADA',
                        }"
                      >
                        <i v-if="sol.estado === 'INFORMACION'" class="pi pi-info-circle text-[9px]"></i>
                        <i v-else-if="sol.estado === 'PENDIENTE'" class="pi pi-clock text-[9px]"></i>
                        <i v-else class="pi pi-check text-[9px]"></i>
                        {{ sol.estado === 'INFORMACION' ? 'INFORMACIÓN' : sol.estado }}
                      </span>
                    </div>
                    <p class="text-sm text-slate-700 bg-white p-3 rounded border border-slate-200 leading-relaxed">{{ sol.mensaje_auditor }}</p>

                    <!-- Respuesta si existe -->
                    <div v-if="sol.respuesta_operador" class="p-3 bg-emerald-50 rounded border border-emerald-200 space-y-1">
                      <p class="text-[11px] font-bold text-emerald-800 uppercase">Respuesta de Sucursal (por {{ sol.respondido_por?.full_name }})</p>
                      <p class="text-xs text-slate-700">{{ sol.respuesta_operador }}</p>
                    </div>

                    <!-- Boton para responder solo si esta pendiente -->
                    <div v-else-if="sol.estado === 'PENDIENTE'" class="pt-2">
                      <Button
                        label="Responder Observación"
                        icon="pi pi-reply"
                        size="small"
                        severity="primary"
                        @click="selectedSolicitudId = sol.id; isResponderVisible = true"
                      />
                    </div>
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 1: Adjuntos / Fotos con Visor Popup -->
              <TabPanel value="1">
                <div class="p-4 space-y-4">
                  <!-- Upload Area -->
                  <div class="p-4 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 text-center">
                    <FileUpload
                      mode="basic"
                      name="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      :maxFileSize="10000000"
                      chooseLabel="Subir Prescripción o Foto (PDF, PNG, JPG)"
                      customUpload
                      auto
                      @uploader="handleUploadAdjunto"
                    />
                  </div>

                  <!-- Attachments List -->
                  <div v-if="orden.adjuntos.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div
                      v-for="adj in orden.adjuntos"
                      :key="adj.id"
                      class="p-3 rounded-lg border border-slate-200 flex items-center justify-between hover:bg-slate-50 transition"
                    >
                      <div
                        class="flex items-center space-x-2.5 truncate cursor-pointer group"
                        @click="handlePreviewAdjunto(adj)"
                        title="Clic para previsualizar"
                      >
                        <i
                          :class="adj.tipo_mime.includes('pdf') ? 'pi pi-file-pdf text-red-500' : 'pi pi-image text-blue-500'"
                          class="text-2xl"
                        ></i>
                        <div class="truncate">
                          <p class="text-xs font-semibold text-slate-800 group-hover:text-blue-600 truncate">{{ adj.nombre_archivo_original }}</p>
                          <p class="text-[10px] text-slate-400">{{ (adj.tamano_bytes / 1024).toFixed(1) }} KB &bull; Ver archivo</p>
                        </div>
                      </div>
                      <div class="flex items-center space-x-1">
                        <Button
                          icon="pi pi-eye"
                          text
                          rounded
                          size="small"
                          severity="primary"
                          title="Previsualizar en popup"
                          @click="handlePreviewAdjunto(adj)"
                        />
                        <a :href="ordenesService.getDescargarAdjuntoUrl(adj.id)" target="_blank" download>
                          <Button icon="pi pi-download" text rounded size="small" severity="secondary" title="Descargar archivo" />
                        </a>
                        <Button
                          icon="pi pi-trash"
                          text
                          rounded
                          size="small"
                          severity="danger"
                          title="Eliminar archivo adjunto"
                          @click="handleDeleteAdjunto(adj)"
                        />
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-center py-6 text-sm text-slate-400">
                    No se han subido archivos adjuntos todavía.
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 2: Auditorías Previas del Paciente -->
              <TabPanel value="2">
                <div class="p-4 space-y-3">
                  <LoadingSpinner v-if="isLoadingPrevOrders" message="Buscando antecedentes clínicos..." class="py-6" />
                  <div v-else-if="prevOrders.length === 0" class="text-center py-8 text-sm text-slate-400">
                    Este paciente no tiene otras órdenes médicas registradas.
                  </div>
                  <div v-else class="space-y-2">
                    <div
                      v-for="prev in prevOrders"
                      :key="prev.id"
                      class="p-3 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50/40 transition cursor-pointer flex items-center justify-between"
                      @click="router.push(`/ordenes/${prev.id}`)"
                    >
                      <div class="space-y-0.5">
                        <div class="flex items-center space-x-2">
                          <span class="font-mono text-xs font-bold text-slate-800">{{ prev.nro_orden }}</span>
                          <StatusTag :value="prev.estado" />
                        </div>
                        <p class="text-[11px] text-slate-500">
                          Prescripción: {{ formatDate(prev.fecha_prescripcion) }} &bull; Mutual: {{ prev.mutual }} &bull; Copago: ${{ prev.valor_copago }}
                        </p>
                      </div>
                      <Button icon="pi pi-chevron-right" text rounded size="small" severity="secondary" />
                    </div>
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 3: Registro de Llamadas -->
              <TabPanel value="3">
                <div class="p-4 space-y-3">
                  <!-- Header bar para registrar llamada manual -->
                  <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div>
                      <span class="font-bold text-slate-700 text-xs block">Historial de Llamadas y Consultas</span>
                      <span class="text-[10px] text-slate-400">Comunicaciones registradas con el paciente</span>
                    </div>
                    <Button
                      label="+ Registrar Llamada"
                      icon="pi pi-phone"
                      size="small"
                      severity="primary"
                      @click="openDirectLlamadaModal"
                    />
                  </div>

                  <div v-if="orden.llamadas_registro.length === 0" class="text-center py-8 text-sm text-slate-400">
                    No hay registros de llamadas a este paciente.
                  </div>
                  <div
                    v-for="ll in orden.llamadas_registro"
                    :key="ll.id"
                    class="p-3 rounded-lg border border-slate-200 bg-white space-y-1.5 text-xs shadow-sm"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span
                          class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                          :class="{
                            'bg-emerald-100 text-emerald-800 border border-emerald-200': ll.resultado === 'EXITOSA',
                            'bg-amber-100 text-amber-800 border border-amber-200': ll.resultado === 'NO_CONTESTA',
                            'bg-red-100 text-red-800 border border-red-200': ll.resultado === 'NUMERO_ERRONEO',
                            'bg-blue-100 text-blue-800 border border-blue-200': ll.resultado === 'REINTENTAR',
                          }"
                        >
                          {{ ll.resultado }}
                        </span>
                        <span class="font-bold text-slate-700 text-[11px]">
                          {{ formatTipoLlamada(ll.tipo_llamada) }}
                        </span>
                      </div>
                      <span class="text-slate-400 text-[10px]">{{ formatDateTime(ll.created_at) }}</span>
                    </div>
                    <p class="text-slate-500 text-[11px]">Operador: <span class="font-medium text-slate-700">{{ ll.operador?.full_name || 'Sistema' }}</span></p>
                    <p v-if="ll.observaciones" class="italic text-slate-800 bg-slate-50 p-2 rounded border border-slate-100">"{{ ll.observaciones }}"</p>
                  </div>
                </div>
              </TabPanel>

              <!-- Tab 4: Trazabilidad / Audit Trail -->
              <TabPanel value="4">
                <div class="p-4">
                  <Timeline :value="orden.audit_logs">
                    <template #content="{ item }">
                      <div class="mb-4 text-xs space-y-0.5">
                        <p class="font-bold text-slate-800">{{ item.accion }}</p>
                        <p v-if="item.estado_anterior" class="text-slate-500">
                          De <span class="font-semibold">{{ item.estado_anterior }}</span> a <span class="font-semibold text-emerald-700">{{ item.estado_nuevo }}</span>
                        </p>
                        <p class="text-[10px] text-slate-400">
                          Por {{ item.user?.full_name || 'Sistema' }} &bull; {{ formatDateTime(item.created_at) }}
                        </p>
                      </div>
                    </template>
                  </Timeline>
                </div>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </div>
    </template>

    <!-- Modal: Editar Datos de la Orden -->
    <Dialog v-model:visible="isEditOrdenVisible" modal header="Editar Datos de la Orden Médica" :style="{ width: '600px' }">
      <div class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Mutual / Obra Social</label>
            <Dropdown
              v-model="editForm.mutual"
              :options="mutuales"
              optionLabel="sigla"
              optionValue="sigla"
              class="w-full text-xs"
              editable
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Valor Copago ($)</label>
            <InputNumber v-model="editForm.valor_copago" mode="currency" currency="ARS" locale="es-AR" class="w-full text-xs" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Valor Estudios NO Autorizados ($)</label>
          <InputNumber v-model="editForm.valor_estudios_no_autorizados" mode="currency" currency="ARS" locale="es-AR" class="w-full text-xs" />
        </div>

        <div class="pt-2 border-t border-slate-200">
          <h5 class="text-xs font-bold text-slate-600 uppercase mb-2">Datos de Contacto</h5>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Nombre Contacto</label>
              <InputText v-model="editForm.contacto_nombre" class="w-full text-xs" />
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Horario Preferido</label>
              <Dropdown v-model="editForm.contacto_horario" :options="opcionesHorarios" class="w-full text-xs" editable />
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Teléfono Fijo</label>
              <InputText v-model="editForm.contacto_telefono" class="w-full text-xs" />
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Celular / WhatsApp</label>
              <InputText v-model="editForm.contacto_celular" class="w-full text-xs" />
            </div>
          </div>
          <div class="mt-2">
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Correo Electrónico</label>
            <InputText v-model="editForm.contacto_email" class="w-full text-xs" />
          </div>
        </div>

        <div class="pt-2 border-t border-slate-200">
          <label class="block text-xs font-semibold text-slate-700 mb-1">Observaciones de Ingreso</label>
          <Textarea v-model="editForm.observaciones_ingreso" rows="3" class="w-full text-xs" />
        </div>

        <!-- Checkbox APB y Debe Orden Medica Fisica -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="p-3 bg-blue-50 rounded-lg border border-blue-200 flex items-center space-x-2">
            <Checkbox v-model="editForm.abona_apb" binary inputId="editAbonaApbView" />
            <label for="editAbonaApbView" class="text-xs font-bold text-blue-900 cursor-pointer">
              🧪 Abona APB (Acto Profesional Bioquímico)
            </label>
          </div>

          <div class="p-3 bg-red-50 rounded-lg border border-red-200 flex items-center space-x-2">
            <Checkbox v-model="editForm.debe_orden_medica" binary inputId="editDebeOrdenFisicaView" />
            <label for="editDebeOrdenFisicaView" class="text-xs font-bold text-red-900 cursor-pointer">
              ⚠️ Paciente DEBE Orden Médica Física
            </label>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isEditOrdenVisible = false" />
        <Button label="Guardar Cambios" :loading="isActionLoading" @click="handleSaveEditOrden" />
      </template>
    </Dialog>

    <!-- Modal: Popup Viewer para Archivos (PDF y Fotos) -->
    <Dialog
      v-model:visible="isPreviewVisible"
      modal
      :header="previewFile?.nombre_archivo_original || 'Visualizador de Archivo'"
      :style="{ width: '85vw', maxWidth: '1000px' }"
    >
      <div class="min-h-[500px] flex items-center justify-center bg-slate-900 rounded-lg overflow-hidden relative">
        <LoadingSpinner v-if="isLoadingPreview" message="Cargando vista previa..." class="text-white" />
        <template v-else-if="previewUrl">
          <iframe
            v-if="previewFile?.tipo_mime.includes('pdf')"
            :src="previewUrl"
            class="w-full h-[75vh] border-0"
          ></iframe>
          <img
            v-else
            :src="previewUrl"
            :alt="previewFile?.nombre_archivo_original"
            class="max-w-full max-h-[75vh] object-contain mx-auto"
          />
        </template>
        <div v-else class="text-white text-sm">
          No se pudo generar la vista previa.
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <span class="text-xs text-slate-500 font-mono">
            {{ previewFile ? (previewFile.tamano_bytes / 1024).toFixed(1) + ' KB' : '' }}
          </span>
          <div class="space-x-2">
            <a v-if="previewFile" :href="ordenesService.getDescargarAdjuntoUrl(previewFile.id)" target="_blank" download>
              <Button label="Descargar" icon="pi pi-download" size="small" severity="secondary" outlined />
            </a>
            <Button label="Cerrar" icon="pi pi-times" size="small" severity="secondary" @click="isPreviewVisible = false" />
          </div>
        </div>
      </template>
    </Dialog>

    <!-- Modal: Cambiar Estado -->
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

    <!-- Modal: Crear Observación Médica -->
    <Dialog v-model:visible="isSolicitudVisible" modal header="Emitir Observación del Auditor" :style="{ width: '500px' }">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Carácter de la Observación <span class="text-red-500">*</span></label>
          <div class="grid grid-cols-2 gap-2">
            <div
              class="p-2.5 rounded-lg border cursor-pointer transition flex items-start gap-2 text-xs"
              :class="!esInformativa ? 'bg-amber-50 border-amber-400 text-amber-900 shadow-sm ring-1 ring-amber-400' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'"
              @click="esInformativa = false"
            >
              <i class="pi pi-exclamation-triangle text-amber-600 text-base mt-0.5 flex-shrink-0"></i>
              <div>
                <span class="font-bold block text-xs">Solicitud Auditoría</span>
                <span class="text-[10px] text-amber-700 block mt-0.5">Requiere llamada al paciente y pasa orden a Solicitudes</span>
              </div>
            </div>
            <div
              class="p-2.5 rounded-lg border cursor-pointer transition flex items-start gap-2 text-xs"
              :class="esInformativa ? 'bg-blue-50 border-blue-400 text-blue-900 shadow-sm ring-1 ring-blue-400' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'"
              @click="esInformativa = true"
            >
              <i class="pi pi-info-circle text-blue-600 text-base mt-0.5 flex-shrink-0"></i>
              <div>
                <span class="font-bold block text-xs">Solo Información</span>
                <span class="text-[10px] text-blue-700 block mt-0.5">Nota interna azul: no genera llamada ni altera estado</span>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Motivo Principal <span class="text-red-500">*</span></label>
          <Dropdown
            v-model="motivoSolicitud"
            :options="['Falta diagnóstico', 'Firma/Sello ilegible', 'Estudio no coincide con pedido', 'Falta resumen clínico', 'Nota técnica/Informativa', 'Otro']"
            editable
            placeholder="Seleccione o escriba el motivo..."
            class="w-full text-xs"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Mensaje para la Sucursal <span class="text-red-500">*</span></label>
          <Textarea v-model="mensajeSolicitud" rows="4" class="w-full text-xs" placeholder="Detalle qué documentación o corrección es requerida..." />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isSolicitudVisible = false" />
        <Button
          :label="esInformativa ? 'Guardar Información' : 'Emitir Solicitud'"
          :severity="esInformativa ? 'info' : 'warn'"
          :icon="esInformativa ? 'pi pi-info-circle' : 'pi pi-exclamation-triangle'"
          :loading="isActionLoading"
          @click="handleCrearSolicitud"
        />
      </template>
    </Dialog>

    <!-- Modal: Responder Observación -->
    <Dialog v-model:visible="isResponderVisible" modal header="Responder Observación del Auditor" :style="{ width: '500px' }">
      <div class="space-y-4">
        <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Respuesta y Aclaración <span class="text-red-500">*</span></label>
        <Textarea v-model="respuestaOperador" rows="4" class="w-full" placeholder="Indique las correcciones realizadas o adjuntos cargados..." />
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isResponderVisible = false" />
        <Button label="Enviar Respuesta" severity="primary" :loading="isActionLoading" @click="handleResponderSolicitud" />
      </template>
    </Dialog>

    <!-- Modal: Asignar Auditor -->
    <Dialog v-model:visible="isAsignarAuditorVisible" modal header="Asignar Auditor Responsable" :style="{ width: '400px' }">
      <div class="space-y-4">
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

    <!-- Modal: Registrar Llamada -->
    <RegistrarLlamadaModal
      v-if="orden"
      v-model:visible="isLlamadaModalVisible"
      :ordenId="orden.id"
      :nroOrden="orden.nro_orden"
      :pacienteNombre="orden.paciente.nombre_completo"
      :telefono="orden.contacto_telefono || orden.contacto_celular || orden.paciente.telefono"
      :tipoLlamada="orden.estado === 'Solicitudes de auditoria' ? 'SOLICITUD_AUDITORIA' : 'AUDITORIA_FINALIZADA'"
      @success="loadOrden"
    />

    <!-- Modal Registrar Llamada Directa / Manual -->
    <Dialog v-model:visible="isDirectLlamadaVisible" modal header="Registrar Contacto Telefónico / Consulta" :style="{ width: '480px' }">
      <div class="space-y-4 text-xs">
        <!-- Banner si hay un aviso pendiente de auditoría -->
        <div
          v-if="
            orden &&
            ((orden.estado === 'Solicitudes de auditoria' && !orden.llamada_solicitud_completada) ||
             (orden.estado === 'Auditoria Finalizada' && !orden.llamada_finalizada_completada))
          "
          class="p-3 bg-amber-50 rounded-lg border border-amber-300 text-amber-900 space-y-2"
        >
          <div class="flex items-start gap-2">
            <i class="pi pi-bell text-amber-600 text-sm mt-0.5 flex-shrink-0"></i>
            <div>
              <p class="font-bold text-xs">Esta orden tiene un aviso de auditoría pendiente</p>
              <p class="text-[11px] text-amber-800">
                {{ orden.estado === 'Solicitudes de auditoria' ? 'Observación de auditoría pendiente de comunicar.' : 'Resolución de auditoría finalizada pendiente de comunicar.' }}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-2 pt-1 border-t border-amber-200">
            <Checkbox v-model="directLlamadaForm.completar_aviso_pendiente" binary inputId="checkCompletarAvisoView" />
            <label for="checkCompletarAvisoView" class="text-xs font-bold text-amber-950 cursor-pointer">
              Dar por comunicado el aviso y quitar de Llamadas Pendientes
            </label>
          </div>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 uppercase mb-1">Tipo de Contacto <span class="text-red-500">*</span></label>
          <Dropdown
            v-model="directLlamadaForm.tipo_llamada"
            :options="opcionesTiposLlamada"
            optionLabel="label"
            optionValue="value"
            class="w-full text-xs"
          />
        </div>
        <div>
          <label class="block font-semibold text-slate-700 uppercase mb-1">Resultado del Contacto <span class="text-red-500">*</span></label>
          <Dropdown
            v-model="directLlamadaForm.resultado"
            :options="opcionesResultadosLlamada"
            optionLabel="label"
            optionValue="value"
            class="w-full text-xs"
          />
        </div>
        <div>
          <label class="block font-semibold text-slate-700 uppercase mb-1">Detalle / Conversación con el Paciente <span class="text-red-500">*</span></label>
          <Textarea
            v-model="directLlamadaForm.observaciones"
            rows="4"
            class="w-full text-xs"
            placeholder="Describa la consulta recibida o la gestión realizada con el paciente..."
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isDirectLlamadaVisible = false" />
        <Button label="Guardar Llamada" icon="pi pi-check" severity="primary" :loading="isActionLoading" @click="handleSaveDirectLlamada" />
      </template>
    </Dialog>
  </div>
</template>
