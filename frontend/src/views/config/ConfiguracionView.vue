<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { configService } from '../../services/config.service';
import {
  EstadoOrdenConfig,
  EstadoOrdenConfigCreate,
  EstadoOrdenConfigUpdate,
  IndicacionEstudio,
  IndicacionEstudioCreate,
  MotivoCancelacion,
  MotivoCancelacionCreate,
  MotivoCancelacionUpdate,
  PlantillaEmail,
  PlantillaEmailCreate,
  SystemFeaturesConfig,
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
import ToggleSwitch from 'primevue/toggleswitch';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import { formatDateTime } from '../../utils/date';
import { useToast } from 'primevue/usetoast';
import { useFeaturesStore } from '../../stores/features.store';

const toast = useToast();
const featuresStore = useFeaturesStore();
const isUpdatingFeature = ref<string | null>(null);

const handleToggleFeature = async (featureKey: keyof SystemFeaturesConfig, newValue: boolean) => {
  isUpdatingFeature.value = featureKey;
  try {
    await featuresStore.updateFeatures({ [featureKey]: newValue });
    toast.add({
      severity: newValue ? 'success' : 'warn',
      summary: newValue ? 'Funcionalidad Activada' : 'Funcionalidad Desactivada',
      detail: `El parámetro se actualizó en el sistema.`,
      life: 3000,
    });
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo actualizar la funcionalidad',
      life: 4000,
    });
  } finally {
    isUpdatingFeature.value = null;
  }
};

const motivos = ref<MotivoCancelacion[]>([]);
const estados = ref<EstadoOrdenConfig[]>([]);
const indicaciones = ref<IndicacionEstudio[]>([]);
const isLoadingMotivos = ref(true);
const isLoadingEstados = ref(true);
const isLoadingIndicaciones = ref(true);

// Automatización y Plantillas de Mail
const envioAutoMail = ref(false);
const minutosGraciaMail = ref(120);
const zeptomailConfigurado = ref(false);
const remitenteEmail = ref('');
const remitenteNombre = ref('');
const isLoadingMailConfig = ref(false);
const isSavingMailConfig = ref(false);

const plantillas = ref<PlantillaEmail[]>([]);
const isLoadingPlantillas = ref(false);
const isPlantillaDialogVisible = ref(false);
const isEditingPlantilla = ref(false);
const isSavingPlantilla = ref(false);
const editingPlantillaId = ref<string | null>(null);

const plantillaForm = ref<PlantillaEmailCreate>({
  codigo: '',
  nombre: '',
  asunto: '',
  cuerpo_html: '',
  es_default: false,
  activa: true,
});

const loadPlantillas = async () => {
  isLoadingPlantillas.value = true;
  try {
    plantillas.value = await configService.listPlantillasEmail(false);
  } catch (err: any) {
    console.warn('Error cargando plantillas:', err);
  } finally {
    isLoadingPlantillas.value = false;
  }
};

const openNewPlantillaDialog = () => {
  isEditingPlantilla.value = false;
  editingPlantillaId.value = null;
  plantillaForm.value = {
    codigo: '',
    nombre: '',
    asunto: 'Resolución de Auditoría Médica - Orden N° {{nro_orden}}',
    cuerpo_html: '',
    es_default: plantillas.value.length === 0,
    activa: true,
  };
  isPlantillaDialogVisible.value = true;
};

const isHelpVariablesVisible = ref(false);
const isLoadingBaseHtml = ref(false);

const handleCargarHtmlBase = async () => {
  isLoadingBaseHtml.value = true;
  try {
    const baseHtml = await configService.getCodigoBasePlantilla();
    plantillaForm.value.cuerpo_html = baseHtml;
    toast.add({ severity: 'info', summary: 'Código Cargado', detail: 'Se cargó la estructura HTML base predeterminada', life: 2500 });
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cargar el código base', life: 3000 });
  } finally {
    isLoadingBaseHtml.value = false;
  }
};

const openEditPlantillaDialog = async (tpl: PlantillaEmail) => {
  isEditingPlantilla.value = true;
  editingPlantillaId.value = tpl.id;

  let htmlContent = tpl.cuerpo_html || '';
  if (!htmlContent.trim()) {
    try {
      htmlContent = await configService.getCodigoBasePlantilla();
    } catch {
      htmlContent = '';
    }
  }

  plantillaForm.value = {
    codigo: tpl.codigo,
    nombre: tpl.nombre,
    asunto: tpl.asunto,
    cuerpo_html: htmlContent,
    es_default: tpl.es_default,
    activa: tpl.activa,
  };
  isPlantillaDialogVisible.value = true;
};

const handleSavePlantilla = async () => {
  if (!plantillaForm.value.nombre.trim() || !plantillaForm.value.asunto.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Nombre y Asunto son obligatorios', life: 3000 });
    return;
  }
  if (!isEditingPlantilla.value && !plantillaForm.value.codigo.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'El código único es obligatorio', life: 3000 });
    return;
  }

  isSavingPlantilla.value = true;
  try {
    if (isEditingPlantilla.value && editingPlantillaId.value) {
      await configService.updatePlantillaEmail(editingPlantillaId.value, {
        nombre: plantillaForm.value.nombre.trim(),
        asunto: plantillaForm.value.asunto.trim(),
        cuerpo_html: plantillaForm.value.cuerpo_html,
        es_default: plantillaForm.value.es_default,
        activa: plantillaForm.value.activa,
      });
      toast.add({ severity: 'success', summary: 'Plantilla Actualizada', detail: 'Cambios guardados con éxito', life: 3000 });
    } else {
      await configService.createPlantillaEmail({
        codigo: plantillaForm.value.codigo.trim().toUpperCase(),
        nombre: plantillaForm.value.nombre.trim(),
        asunto: plantillaForm.value.asunto.trim(),
        cuerpo_html: plantillaForm.value.cuerpo_html,
        es_default: plantillaForm.value.es_default,
        activa: plantillaForm.value.activa,
      });
      toast.add({ severity: 'success', summary: 'Plantilla Creada', detail: 'Nueva plantilla registrada', life: 3000 });
    }
    isPlantillaDialogVisible.value = false;
    await loadPlantillas();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al guardar plantilla', life: 4000 });
  } finally {
    isSavingPlantilla.value = false;
  }
};

const handleDeletePlantilla = async (tpl: PlantillaEmail) => {
  if (tpl.es_default) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'No se puede eliminar la plantilla predeterminada', life: 3000 });
    return;
  }
  try {
    await configService.deletePlantillaEmail(tpl.id);
    toast.add({ severity: 'info', summary: 'Eliminada', detail: `Plantilla '${tpl.nombre}' eliminada.`, life: 2500 });
    await loadPlantillas();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'No se pudo eliminar la plantilla', life: 3500 });
  }
};

const loadMailConfig = async () => {
  isLoadingMailConfig.value = true;
  try {
    const res = await configService.getMailAutomatizacion();
    envioAutoMail.value = res.envio_automatico;
    minutosGraciaMail.value = res.minutos_gracia;
    zeptomailConfigurado.value = res.zeptomail_configurado;
    remitenteEmail.value = res.remitente_email;
    remitenteNombre.value = res.remitente_nombre;
  } catch (err: any) {
    console.warn('Error cargando config de correo:', err);
  } finally {
    isLoadingMailConfig.value = false;
  }
};

const handleSaveMailConfig = async () => {
  isSavingMailConfig.value = true;
  try {
    const res = await configService.updateMailAutomatizacion({
      envio_automatico: envioAutoMail.value,
      minutos_gracia: minutosGraciaMail.value,
    });
    envioAutoMail.value = res.envio_automatico;
    minutosGraciaMail.value = res.minutos_gracia;
    toast.add({
      severity: 'success',
      summary: 'Parámetros Actualizados',
      detail: `Envío automático: ${envioAutoMail.value ? 'ACTIVADO' : 'DESACTIVADO (Manual)'} con ${minutosGraciaMail.value} min de gracia.`,
      life: 3500,
    });
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo guardar la configuración de correo',
      life: 4000,
    });
  } finally {
    isSavingMailConfig.value = false;
  }
};

// Indicaciones
const loadIndicaciones = async () => {
  isLoadingIndicaciones.value = true;
  try {
    indicaciones.value = await configService.listIndicaciones(false);
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar las indicaciones', life: 3000 });
  } finally {
    isLoadingIndicaciones.value = false;
  }
};

const isIndicacionDialogVisible = ref(false);
const isEditingIndicacion = ref(false);
const isSavingIndicacion = ref(false);
const editingIndicacionId = ref<string | null>(null);

const indicacionForm = ref<IndicacionEstudioCreate>({
  codigo: '',
  titulo: '',
  instrucciones: '',
  categoria: 'Sangre',
  color: 'info',
  orden_secuencia: 1,
  activa: true,
});

const openNewIndicacionDialog = () => {
  isEditingIndicacion.value = false;
  editingIndicacionId.value = null;
  indicacionForm.value = {
    codigo: '',
    titulo: '',
    instrucciones: '',
    categoria: 'Sangre',
    color: 'info',
    orden_secuencia: indicaciones.value.length + 1,
    activa: true,
  };
  isIndicacionDialogVisible.value = true;
};

const openEditIndicacionDialog = (ind: IndicacionEstudio) => {
  isEditingIndicacion.value = true;
  editingIndicacionId.value = ind.id;
  indicacionForm.value = {
    codigo: ind.codigo,
    titulo: ind.titulo,
    instrucciones: ind.instrucciones,
    categoria: ind.categoria || '',
    color: ind.color,
    orden_secuencia: ind.orden_secuencia,
    activa: ind.activa,
  };
  isIndicacionDialogVisible.value = true;
};

const handleSaveIndicacion = async () => {
  if (!indicacionForm.value.titulo.trim() || !indicacionForm.value.instrucciones.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Título e Instrucciones son obligatorios', life: 3000 });
    return;
  }
  if (!isEditingIndicacion.value && !indicacionForm.value.codigo.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'El código único es obligatorio', life: 3000 });
    return;
  }

  isSavingIndicacion.value = true;
  try {
    if (isEditingIndicacion.value && editingIndicacionId.value) {
      await configService.updateIndicacion(editingIndicacionId.value, {
        titulo: indicacionForm.value.titulo.trim(),
        instrucciones: indicacionForm.value.instrucciones.trim(),
        categoria: indicacionForm.value.categoria?.trim() || null,
        color: indicacionForm.value.color,
        orden_secuencia: indicacionForm.value.orden_secuencia,
        activa: indicacionForm.value.activa,
      });
      toast.add({ severity: 'success', summary: 'Actualizada', detail: 'Indicación clínica modificada con éxito', life: 3000 });
    } else {
      await configService.createIndicacion({
        codigo: indicacionForm.value.codigo.trim().toUpperCase(),
        titulo: indicacionForm.value.titulo.trim(),
        instrucciones: indicacionForm.value.instrucciones.trim(),
        categoria: indicacionForm.value.categoria?.trim() || null,
        color: indicacionForm.value.color,
        orden_secuencia: indicacionForm.value.orden_secuencia,
        activa: indicacionForm.value.activa,
      });
      toast.add({ severity: 'success', summary: 'Creada', detail: 'Nueva indicación de preparación registrada', life: 3000 });
    }
    isIndicacionDialogVisible.value = false;
    await loadIndicaciones();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al guardar indicación', life: 4000 });
  } finally {
    isSavingIndicacion.value = false;
  }
};

const handleToggleActiveIndicacion = async (ind: IndicacionEstudio) => {
  try {
    await configService.updateIndicacion(ind.id, { activa: !ind.activa });
    toast.add({
      severity: 'info',
      summary: ind.activa ? 'Desactivada' : 'Activada',
      detail: `Indicación '${ind.titulo}' ahora está ${ind.activa ? 'inactiva' : 'activa'}.`,
      life: 2500,
    });
    await loadIndicaciones();
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cambiar estado de indicación', life: 3000 });
  }
};

// APB Configuration
const valorApb = ref(0);
const apbUpdatedAt = ref<string | null>(null);
const isLoadingApb = ref(false);
const isSavingApb = ref(false);

const loadApb = async () => {
  isLoadingApb.value = true;
  try {
    const res = await configService.getValorApb();
    valorApb.value = Number(res.valor_apb) || 0;
    apbUpdatedAt.value = res.updated_at || null;
  } catch (err: any) {
    console.warn('Error cargando APB:', err);
  } finally {
    isLoadingApb.value = false;
  }
};

const handleSaveApb = async () => {
  isSavingApb.value = true;
  try {
    const res = await configService.updateValorApb(valorApb.value);
    valorApb.value = Number(res.valor_apb) || 0;
    apbUpdatedAt.value = res.updated_at || null;
    toast.add({
      severity: 'success',
      summary: 'Actualizado',
      detail: `Valor base de APB fijado en $ ${valorApb.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`,
      life: 3500,
    });
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo actualizar el valor de APB',
      life: 4000,
    });
  } finally {
    isSavingApb.value = false;
  }
};

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
  featuresStore.fetchFeatures(true);
  loadMotivos();
  loadEstados();
  loadApb();
  loadIndicaciones();
  loadMailConfig();
  loadPlantillas();
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
          <Tab value="3">
            <i class="pi pi-shield mr-1.5 text-emerald-600"></i> Acto Profesional Bioquímico (APB)
          </Tab>
          <Tab value="4">
            <i class="pi pi-book mr-1.5 text-amber-600"></i> Indicaciones de Estudios
          </Tab>
          <Tab value="5">
            <i class="pi pi-envelope mr-1.5 text-cyan-600"></i> Automatización y Correos
          </Tab>
          <Tab value="6">
            <i class="pi pi-sliders-h mr-1.5 text-violet-600"></i> Funcionalidades (Feature Flags)
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

          <!-- Tab 3: Acto Profesional Bioquimico (APB) -->
          <TabPanel value="3">
            <div class="p-6 max-w-2xl space-y-6">
              <div class="bg-gradient-to-r from-blue-50 to-indigo-50/80 p-5 rounded-2xl border border-blue-200 shadow-sm">
                <div class="flex items-start gap-4">
                  <div class="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center text-2xl shadow-sm shrink-0">
                    🧪
                  </div>
                  <div>
                    <h3 class="text-base font-bold text-blue-950">Acto Profesional Bioquímico (APB)</h3>
                    <p class="text-xs text-blue-800/80 mt-1 leading-relaxed">
                      Este monto es el valor de referencia fijo a nivel laboratorio. Al registrar una orden con <strong>"Abona APB"</strong>, el sistema calcula automáticamente lo que debe abonar el paciente deduciendo el porcentaje de cobertura configurado en su mutual.
                    </p>
                  </div>
                </div>
              </div>

              <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <div>
                  <label class="block text-xs font-bold text-slate-700 uppercase mb-1.5">
                    Valor Base de Referencia Vigente ($)
                  </label>
                  <InputNumber
                    v-model="valorApb"
                    mode="currency"
                    currency="ARS"
                    locale="es-AR"
                    class="w-full"
                    inputClass="font-bold text-lg text-blue-900"
                    :min="0"
                  />
                  <p v-if="apbUpdatedAt" class="text-xs text-slate-500 mt-1.5">
                    Última actualización: <span class="font-medium text-slate-700">{{ formatDateTime(apbUpdatedAt) }}</span>
                  </p>
                </div>

                <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span class="text-xs text-slate-500">Los cambios se aplican de inmediato para nuevas órdenes.</span>
                  <Button
                    label="Guardar Nuevo Valor APB"
                    icon="pi pi-check"
                    severity="primary"
                    :loading="isSavingApb"
                    @click="handleSaveApb"
                  />
                </div>
              </div>
            </div>
          </TabPanel>

          <!-- Tab 4: Indicaciones de Estudios -->
          <TabPanel value="4">
            <div class="p-4 space-y-4">
              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div>
                  <h4 class="text-sm font-bold text-slate-800">Catálogo de Indicaciones Preescritas para Estudios</h4>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Configure las indicaciones y preparaciones que los operadores y auditores podrán seleccionar en forma de <strong>chips</strong> en cualquier orden médica y enviar por correo al paciente.
                  </p>
                </div>
                <Button label="Nueva Indicación" icon="pi pi-plus" severity="primary" size="small" class="text-xs" @click="openNewIndicacionDialog" />
              </div>

              <LoadingSpinner v-if="isLoadingIndicaciones" message="Cargando catálogo de indicaciones..." />

              <DataTable v-else :value="indicaciones" stripedRows responsiveLayout="scroll" class="p-datatable-sm" rowHover>
                <Column field="titulo" header="Indicación (Nombre en Chip)" sortable style="width: 240px">
                  <template #body="{ data }">
                    <div class="flex items-center space-x-2">
                      <Tag :value="data.titulo" :severity="(data.color as any) || 'info'" class="text-xs font-bold" />
                      <span v-if="data.categoria" class="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-medium">
                        {{ data.categoria }}
                      </span>
                    </div>
                  </template>
                </Column>

                <Column field="codigo" header="Código" sortable style="width: 170px">
                  <template #body="{ data }">
                    <span class="font-mono text-xs text-slate-500 font-semibold">{{ data.codigo }}</span>
                  </template>
                </Column>

                <Column field="instrucciones" header="Instrucciones al Paciente">
                  <template #body="{ data }">
                    <p class="text-xs text-slate-600 line-clamp-2 leading-relaxed">{{ data.instrucciones }}</p>
                  </template>
                </Column>

                <Column field="activa" header="Estado" sortable style="width: 110px">
                  <template #body="{ data }">
                    <Tag :value="data.activa ? 'ACTIVA' : 'INACTIVA'" :severity="data.activa ? 'success' : 'secondary'" class="text-[10px]" />
                  </template>
                </Column>

                <Column header="Acciones" style="width: 110px">
                  <template #body="{ data }">
                    <div class="flex items-center space-x-1">
                      <Button icon="pi pi-pencil" text rounded size="small" severity="info" title="Editar indicación" @click="openEditIndicacionDialog(data)" />
                      <Button
                        :icon="data.activa ? 'pi pi-ban' : 'pi pi-check'"
                        text
                        rounded
                        size="small"
                        :severity="data.activa ? 'danger' : 'success'"
                        :title="data.activa ? 'Desactivar' : 'Activar'"
                        @click="handleToggleActiveIndicacion(data)"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>

          <!-- Tab 5: Automatización y Correos ZeptoMail -->
          <TabPanel value="5">
            <div class="p-6 max-w-2xl space-y-6">
              <div class="bg-gradient-to-r from-cyan-50 to-blue-50/80 p-5 rounded-2xl border border-cyan-200 shadow-sm">
                <div class="flex items-start gap-4">
                  <div class="w-12 h-12 rounded-xl bg-cyan-600 text-white flex items-center justify-center text-2xl shadow-sm shrink-0">
                    ✉
                  </div>
                  <div>
                    <h3 class="text-base font-bold text-cyan-950">Despacho de Correos de Resolución Médica (ZeptoMail)</h3>
                    <p class="text-xs text-cyan-900/80 mt-1 leading-relaxed">
                      Al finalizar una auditoría, se genera el correo con el desglose económico y las indicaciones de preparación.
                      Usted puede mantener el <strong>modo manual</strong> (el usuario revisa, edita y hace clic en Enviar) o <strong>activar el modo automático</strong> para que el sistema lo despache tras una ventana de espera programada con opción a frenado.
                    </p>
                  </div>
                </div>
              </div>

              <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-5">
                <!-- Chip de Estado de Automatización -->
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl border" :class="envioAutoMail ? 'bg-emerald-50/70 border-emerald-300' : 'bg-slate-50 border-slate-200'">
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-bold text-slate-800">Modo de Envío de Correos:</span>
                      <Tag :value="envioAutoMail ? 'AUTOMÁTICO ACTIVADO' : 'MANUAL (Revisión antes de enviar)'" :severity="envioAutoMail ? 'success' : 'warn'" class="text-xs font-bold" />
                    </div>
                    <p class="text-xs text-slate-500 mt-1">
                      {{ envioAutoMail ? 'Las órdenes finalizadas se programarán para enviarse automáticamente tras el tiempo de gracia indicado.' : 'El envío queda 100% bajo control del operador. Cada correo se revisa y envía manualmente con el botón en el expediente.' }}
                    </p>
                  </div>
                  <Button
                    :label="envioAutoMail ? 'Cambiar a Modo Manual' : 'Activar Envío Automático'"
                    :icon="envioAutoMail ? 'pi pi-pause' : 'pi pi-bolt'"
                    :severity="envioAutoMail ? 'warn' : 'primary'"
                    size="small"
                    class="text-xs shrink-0"
                    @click="envioAutoMail = !envioAutoMail"
                  />
                </div>

                <!-- Tiempo de Gracia -->
                <div v-if="envioAutoMail" class="p-4 rounded-xl bg-blue-50/50 border border-blue-200 space-y-2 animate-fadeIn">
                  <label class="block text-xs font-bold text-blue-950 uppercase">
                    Ventana de Espera / Gracia antes del Envío Automático (Minutos)
                  </label>
                  <div class="flex items-center gap-3">
                    <InputNumber v-model="minutosGraciaMail" :min="1" :max="1440" class="w-36" inputClass="font-bold text-sm text-center" />
                    <span class="text-xs text-blue-800">
                      (Equivale a <strong>{{ (minutosGraciaMail / 60).toFixed(1) }} horas</strong> para revisar o cancelar el envío antes de que salga).
                    </span>
                  </div>
                </div>

                <!-- Estado del Conector ZeptoMail -->
                <div class="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 space-y-1.5">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-700">Estado de API ZeptoMail:</span>
                    <Tag :value="zeptomailConfigurado ? 'Conectado / Activo' : 'Modo Simulación (Sin Token .env)'" :severity="zeptomailConfigurado ? 'success' : 'secondary'" class="text-[10px]" />
                  </div>
                  <div class="text-[11px] text-slate-500">
                    Remitente: <strong>{{ remitenteNombre }}</strong> &lt;{{ remitenteEmail }}&gt;
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span class="text-xs text-slate-500">La configuración aplica de inmediato en el servidor FastAPI.</span>
                  <Button
                    label="Guardar Configuración de Correo"
                    icon="pi pi-check"
                    severity="primary"
                    :loading="isSavingMailConfig"
                    @click="handleSaveMailConfig"
                  />
                </div>
              </div>

              <!-- Sección Gestor de Plantillas de Correo HTML -->
              <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div>
                    <h4 class="text-sm font-bold text-slate-800">Plantillas de Correo Disponibles</h4>
                    <p class="text-xs text-slate-500">
                      Cree o edite plantillas con variables como <code class="bg-slate-100 text-blue-700 px-1 py-0.5 rounded font-mono">&#123;&#123;paciente_nombre&#125;&#125;</code>, <code class="bg-slate-100 text-blue-700 px-1 py-0.5 rounded font-mono">&#123;&#123;estudios_autorizados&#125;&#125;</code>, <code class="bg-slate-100 text-blue-700 px-1 py-0.5 rounded font-mono">&#123;&#123;estudios_no_autorizados&#125;&#125;</code>, <code class="bg-slate-100 text-blue-700 px-1 py-0.5 rounded font-mono">&#123;&#123;total_abonar&#125;&#125;</code>, <code class="bg-slate-100 text-blue-700 px-1 py-0.5 rounded font-mono">&#123;&#123;indicaciones&#125;&#125;</code>.
                    </p>
                  </div>
                  <Button label="Nueva Plantilla" icon="pi pi-plus" severity="primary" size="small" class="text-xs shrink-0" @click="openNewPlantillaDialog" />
                </div>

                <LoadingSpinner v-if="isLoadingPlantillas" message="Cargando plantillas..." />

                <div v-else class="space-y-2">
                  <div
                    v-for="tpl in plantillas"
                    :key="tpl.id"
                    class="p-3 rounded-lg border border-slate-200 bg-slate-50/60 flex items-center justify-between text-xs hover:border-slate-300 transition"
                  >
                    <div class="min-w-0 pr-3">
                      <div class="flex items-center gap-2">
                        <span class="font-bold text-slate-900 text-xs">{{ tpl.nombre }}</span>
                        <Tag v-if="tpl.es_default" value="PREDETERMINADA" severity="success" class="text-[9px]" />
                        <span class="font-mono text-[10px] text-slate-400">({{ tpl.codigo }})</span>
                      </div>
                      <p class="text-slate-500 text-[11px] truncate mt-0.5">Asunto: {{ tpl.asunto }}</p>
                    </div>

                    <div class="flex items-center gap-1 shrink-0">
                      <Button icon="pi pi-pencil" text rounded size="small" severity="info" title="Editar plantilla" @click="openEditPlantillaDialog(tpl)" />
                      <Button
                        v-if="!tpl.es_default"
                        icon="pi pi-trash"
                        text
                        rounded
                        size="small"
                        severity="danger"
                        title="Eliminar plantilla"
                        @click="handleDeletePlantilla(tpl)"
                      />
                    </div>
                  </div>

                  <p v-if="plantillas.length === 0" class="text-center py-4 text-xs text-slate-400 italic">
                    No hay plantillas personalizadas. Se utiliza el diseño corporativo estándar.
                  </p>
                </div>
              </div>
            </div>
          </TabPanel>

          <!-- Tab 6: Funcionalidades (Feature Flags) -->
          <TabPanel value="6">
            <div class="p-4 space-y-5">
              <div class="bg-gradient-to-r from-violet-50 to-indigo-50 p-4 rounded-xl border border-violet-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="pi pi-sliders-h text-violet-600"></i>
                    <span>Control de Funcionalidades del Sistema (Feature Flags)</span>
                  </h4>
                  <p class="text-xs text-slate-600 mt-1">
                    Activa o desactiva módulos y campos operativos según las necesidades de tu laboratorio o etapa de despliegue.
                    Los cambios tienen impacto inmediato en la interfaz y en los formularios.
                  </p>
                </div>
                <Button
                  icon="pi pi-refresh"
                  label="Actualizar"
                  severity="secondary"
                  outlined
                  size="small"
                  :loading="featuresStore.isLoading"
                  @click="featuresStore.fetchFeatures(true)"
                />
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- 1. Módulo de Correo Electrónico -->
                <div class="p-4 rounded-xl border transition bg-white shadow-sm flex flex-col justify-between"
                  :class="featuresStore.isMailEnabled ? 'border-cyan-300 ring-1 ring-cyan-200' : 'border-slate-200 opacity-90'">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2.5">
                        <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white shadow-sm"
                          :class="featuresStore.isMailEnabled ? 'bg-cyan-600' : 'bg-slate-400'">
                          <i class="pi pi-envelope text-base"></i>
                        </div>
                        <div>
                          <h5 class="text-sm font-bold text-slate-800">Notificaciones por Correo Electrónico</h5>
                          <span class="text-[10px] font-mono font-semibold" :class="featuresStore.isMailEnabled ? 'text-cyan-600' : 'text-slate-400'">
                            modulo_mail
                          </span>
                        </div>
                      </div>
                      <ToggleSwitch
                        :modelValue="featuresStore.features.modulo_mail"
                        :disabled="isUpdatingFeature === 'modulo_mail'"
                        @update:modelValue="handleToggleFeature('modulo_mail', $event)"
                      />
                    </div>
                    <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                      Habilita el botón de notificación y envío de correos con ZeptoMail, previsualización de resoluciones de auditoría y despachos programados a los pacientes.
                    </p>
                  </div>
                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400">Estado actual:</span>
                    <Tag :severity="featuresStore.isMailEnabled ? 'success' : 'secondary'"
                      :value="featuresStore.isMailEnabled ? 'Módulo Activo' : 'Módulo Inactivo'" />
                  </div>
                </div>

                <!-- 2. Calculadora de Presupuesto de Estudios -->
                <div class="p-4 rounded-xl border transition bg-white shadow-sm flex flex-col justify-between"
                  :class="featuresStore.isCalculadoraEnabled ? 'border-violet-300 ring-1 ring-violet-200' : 'border-slate-200 opacity-90'">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2.5">
                        <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white shadow-sm"
                          :class="featuresStore.isCalculadoraEnabled ? 'bg-violet-600' : 'bg-slate-400'">
                          <i class="pi pi-calculator text-base"></i>
                        </div>
                        <div>
                          <h5 class="text-sm font-bold text-slate-800">Calculadora de Presupuestos</h5>
                          <span class="text-[10px] font-mono font-semibold" :class="featuresStore.isCalculadoraEnabled ? 'text-violet-600' : 'text-slate-400'">
                            calculadora_estudios
                          </span>
                        </div>
                      </div>
                      <ToggleSwitch
                        :modelValue="featuresStore.features.calculadora_estudios"
                        :disabled="isUpdatingFeature === 'calculadora_estudios'"
                        @update:modelValue="handleToggleFeature('calculadora_estudios', $event)"
                      />
                    </div>
                    <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                      Muestra el botón con el ícono de calculadora en la orden médica para simular cotizaciones dinámicas (tildar/destildar estudios no autorizados) durante consultas telefónicas.
                    </p>
                  </div>
                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400">Estado actual:</span>
                    <Tag :severity="featuresStore.isCalculadoraEnabled ? 'success' : 'secondary'"
                      :value="featuresStore.isCalculadoraEnabled ? 'Módulo Activo' : 'Módulo Inactivo'" />
                  </div>
                </div>

                <!-- 3. Prácticas Autorizadas y No Autorizadas -->
                <div class="p-4 rounded-xl border transition bg-white shadow-sm flex flex-col justify-between"
                  :class="featuresStore.isEstudiosAutorizacionEnabled ? 'border-emerald-300 ring-1 ring-emerald-200' : 'border-slate-200 opacity-90'">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2.5">
                        <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white shadow-sm"
                          :class="featuresStore.isEstudiosAutorizacionEnabled ? 'bg-emerald-600' : 'bg-slate-400'">
                          <i class="pi pi-check-circle text-base"></i>
                        </div>
                        <div>
                          <h5 class="text-sm font-bold text-slate-800">Prácticas Autorizadas / No Autorizadas</h5>
                          <span class="text-[10px] font-mono font-semibold" :class="featuresStore.isEstudiosAutorizacionEnabled ? 'text-emerald-600' : 'text-slate-400'">
                            estudios_autorizacion
                          </span>
                        </div>
                      </div>
                      <ToggleSwitch
                        :modelValue="featuresStore.features.estudios_autorizacion"
                        :disabled="isUpdatingFeature === 'estudios_autorizacion'"
                        @update:modelValue="handleToggleFeature('estudios_autorizacion', $event)"
                      />
                    </div>
                    <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                      Habilita los campos de auditoría médica para listar qué análisis fueron autorizados por la obra social, cuáles fueron rechazados y el valor de estudios no autorizados.
                    </p>
                  </div>
                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400">Estado actual:</span>
                    <Tag :severity="featuresStore.isEstudiosAutorizacionEnabled ? 'success' : 'secondary'"
                      :value="featuresStore.isEstudiosAutorizacionEnabled ? 'Módulo Activo' : 'Módulo Inactivo'" />
                  </div>
                </div>

                <!-- 4. Indicaciones Clínicas de Preparación -->
                <div class="p-4 rounded-xl border transition bg-white shadow-sm flex flex-col justify-between"
                  :class="featuresStore.isIndicacionesEnabled ? 'border-amber-300 ring-1 ring-amber-200' : 'border-slate-200 opacity-90'">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2.5">
                        <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white shadow-sm"
                          :class="featuresStore.isIndicacionesEnabled ? 'bg-amber-600' : 'bg-slate-400'">
                          <i class="pi pi-book text-base"></i>
                        </div>
                        <div>
                          <h5 class="text-sm font-bold text-slate-800">Indicaciones Clínicas de Preparación</h5>
                          <span class="text-[10px] font-mono font-semibold" :class="featuresStore.isIndicacionesEnabled ? 'text-amber-600' : 'text-slate-400'">
                            indicaciones_estudios
                          </span>
                        </div>
                      </div>
                      <ToggleSwitch
                        :modelValue="featuresStore.features.indicaciones_estudios"
                        :disabled="isUpdatingFeature === 'indicaciones_estudios'"
                        @update:modelValue="handleToggleFeature('indicaciones_estudios', $event)"
                      />
                    </div>
                    <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                      Habilita el selector de chips con instrucciones previas para el paciente (horas de ayuno, recolección de orina, suspensión de medicación) en la orden médica.
                    </p>
                  </div>
                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400">Estado actual:</span>
                    <Tag :severity="featuresStore.isIndicacionesEnabled ? 'success' : 'secondary'"
                      :value="featuresStore.isIndicacionesEnabled ? 'Módulo Activo' : 'Módulo Inactivo'" />
                  </div>
                </div>

                <!-- 5. Asignación de Auditor Médico -->
                <div class="p-4 rounded-xl border transition bg-white shadow-sm flex flex-col justify-between"
                  :class="featuresStore.isAsignarAuditorEnabled ? 'border-blue-300 ring-1 ring-blue-200' : 'border-slate-200 opacity-90'">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2.5">
                        <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white shadow-sm"
                          :class="featuresStore.isAsignarAuditorEnabled ? 'bg-blue-600' : 'bg-slate-400'">
                          <i class="pi pi-user-plus text-base"></i>
                        </div>
                        <div>
                          <h5 class="text-sm font-bold text-slate-800">Asignación de Auditor a la Orden</h5>
                          <span class="text-[10px] font-mono font-semibold" :class="featuresStore.isAsignarAuditorEnabled ? 'text-blue-600' : 'text-slate-400'">
                            asignar_auditor
                          </span>
                        </div>
                      </div>
                      <ToggleSwitch
                        :modelValue="featuresStore.features.asignar_auditor"
                        :disabled="isUpdatingFeature === 'asignar_auditor'"
                        @update:modelValue="handleToggleFeature('asignar_auditor', $event)"
                      />
                    </div>
                    <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                      Permite vincular y reasignar un usuario auditor médico responsable específico a cada orden médica, habilitando además los filtros por auditor asignado.
                    </p>
                  </div>
                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400">Estado actual:</span>
                    <Tag :severity="featuresStore.isAsignarAuditorEnabled ? 'success' : 'secondary'"
                      :value="featuresStore.isAsignarAuditorEnabled ? 'Módulo Activo' : 'Módulo Inactivo'" />
                  </div>
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

    <!-- Modal: Crear / Editar Indicación de Estudio -->
    <Dialog
      v-model:visible="isIndicacionDialogVisible"
      modal
      :header="isEditingIndicacion ? 'Editar Indicación de Estudio' : 'Nueva Indicación de Estudio'"
      :style="{ width: '540px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Código Único <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="indicacionForm.codigo"
              placeholder="Ej: AYUNO_8HS, ORINA_24HS"
              class="w-full text-xs uppercase font-mono"
              :disabled="isEditingIndicacion"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Nombre en Chip <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="indicacionForm.titulo"
              placeholder="Ej: Ayuno de 8 a 12 hs"
              class="w-full text-xs font-bold"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Categoría</label>
            <InputText
              v-model="indicacionForm.categoria as any"
              placeholder="Ej: Sangre, Orina, Medicación"
              class="w-full text-xs"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Color del Chip</label>
            <Dropdown
              v-model="indicacionForm.color"
              :options="opcionesColores"
              optionLabel="label"
              optionValue="value"
              class="w-full text-xs"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Instrucciones al Paciente <span class="text-red-500">*</span>
          </label>
          <Textarea
            v-model="indicacionForm.instrucciones"
            rows="4"
            placeholder="Detalle claro de cómo debe prepararse el paciente (ayuno, recolección, frascos, etc.)..."
            class="w-full text-xs leading-relaxed"
          />
        </div>

        <div class="flex items-center space-x-2 pt-2 border-t border-slate-100">
          <Checkbox v-model="indicacionForm.activa as any" binary inputId="isIndActiva" />
          <label for="isIndActiva" class="text-xs font-semibold text-slate-700 cursor-pointer">
            Indicación Activa y Visible en el Selector de Órdenes
          </label>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isIndicacionDialogVisible = false" />
        <Button
          :label="isEditingIndicacion ? 'Guardar Cambios' : 'Registrar Indicación'"
          icon="pi pi-check"
          severity="primary"
          :loading="isSavingIndicacion"
          @click="handleSaveIndicacion"
        />
      </template>
    </Dialog>

    <!-- Modal: Crear / Editar Plantilla de Correo -->
    <Dialog
      v-model:visible="isPlantillaDialogVisible"
      modal
      :header="isEditingPlantilla ? 'Editar Plantilla de Correo' : 'Nueva Plantilla de Correo'"
      :style="{ width: '680px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Código Único <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="plantillaForm.codigo"
              placeholder="Ej: DEFAULT, NOTIFICACION_NO_AUTORIZADOS"
              class="w-full text-xs uppercase font-mono"
              :disabled="isEditingPlantilla"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Nombre Visible <span class="text-red-500">*</span>
            </label>
            <InputText
              v-model="plantillaForm.nombre"
              placeholder="Ej: Plantilla con No Autorizados"
              class="w-full text-xs font-bold"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Asunto del Correo <span class="text-red-500">*</span>
          </label>
          <InputText
            v-model="plantillaForm.asunto"
            placeholder="Ej: Resolución de Auditoría Médica - Orden N° {{nro_orden}}"
            class="w-full text-xs font-semibold"
          />
        </div>

        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="block text-xs font-semibold text-slate-700 uppercase">
              Cuerpo HTML / Mensaje Personalizado
            </label>
            <div class="flex items-center gap-1.5">
              <Button
                label="Variables Disponibles (Ayuda)"
                icon="pi pi-question-circle"
                text
                size="small"
                severity="info"
                class="text-[11px] py-0.5 px-1.5 font-bold"
                @click="isHelpVariablesVisible = true"
              />
              <Button
                label="Cargar HTML Base"
                icon="pi pi-download"
                text
                size="small"
                severity="secondary"
                :loading="isLoadingBaseHtml"
                class="text-[11px] py-0.5 px-1.5"
                @click="handleCargarHtmlBase"
                title="Carga la plantilla HTML completa predeterminada"
              />
            </div>
          </div>
          <Textarea
            v-model="plantillaForm.cuerpo_html"
            rows="10"
            placeholder="Ingrese el código HTML o texto con variables..."
            class="w-full text-xs font-mono leading-relaxed bg-slate-900 text-slate-100 p-2.5 rounded-lg border border-slate-700"
          />
        </div>

        <div class="flex items-center gap-4 pt-2 border-t border-slate-100">
          <div class="flex items-center space-x-2">
            <Checkbox v-model="plantillaForm.es_default" binary inputId="isTplDefault" />
            <label for="isTplDefault" class="text-xs font-semibold text-slate-700 cursor-pointer">
              Plantilla Predeterminada
            </label>
          </div>
          <div class="flex items-center space-x-2">
            <Checkbox v-model="plantillaForm.activa" binary inputId="isTplActiva" />
            <label for="isTplActiva" class="text-xs font-semibold text-slate-700 cursor-pointer">
              Plantilla Activa
            </label>
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isPlantillaDialogVisible = false" />
        <Button
          :label="isEditingPlantilla ? 'Guardar Cambios' : 'Registrar Plantilla'"
          icon="pi pi-check"
          severity="primary"
          :loading="isSavingPlantilla"
          @click="handleSavePlantilla"
        />
      </template>
    </Dialog>

    <!-- Modal: Popup Ayuda Memoria de Variables -->
    <Dialog
      v-model:visible="isHelpVariablesVisible"
      modal
      header="Ayuda Memoria: Variables Disponibles en Plantillas"
      :style="{ width: '560px' }"
    >
      <div class="space-y-3 text-xs">
        <p class="text-slate-600">
          Puede insertar cualquiera de estos marcadores en el asunto o en el cuerpo HTML de la plantilla. Al momento del envío, el sistema reemplazará automáticamente cada variable con los datos de la orden:
        </p>

        <div class="space-y-2 border border-slate-200 rounded-lg p-3 bg-slate-50 max-h-[380px] overflow-y-auto">
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-blue-700 font-bold font-mono">&#123;&#123;paciente_nombre&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Nombre y apellido del paciente o persona de contacto.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-blue-700 font-bold font-mono">&#123;&#123;nro_orden&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Identificador de orden (ej: ORD-2026-000001).</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-blue-700 font-bold font-mono">&#123;&#123;mutual&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Nombre o sigla de la Obra Social / Prepaga aplicada.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-blue-700 font-bold font-mono">&#123;&#123;estudios_autorizados&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Listado de estudios autorizados por auditoría separados por coma.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-red-700 font-bold font-mono">&#123;&#123;estudios_no_autorizados&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Listado de estudios no autorizados / rechazados separados por coma.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-blue-700 font-bold font-mono">&#123;&#123;observacion_resultado&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Texto o dictamen médico comunicado al finalizar la auditoría.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-emerald-700 font-bold font-mono">&#123;&#123;total_abonar&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Monto total final a abonar (Copago + No autorizados + APB) formateado con moneda.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-slate-700 font-bold font-mono">&#123;&#123;copago&#125;&#125;</code>, <code class="text-slate-700 font-bold font-mono">&#123;&#123;estudios_no_autorizados_valor&#125;&#125;</code>, <code class="text-slate-700 font-bold font-mono">&#123;&#123;valor_apb&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Desglose monetario individual de cada concepto.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-amber-700 font-bold font-mono">&#123;&#123;indicaciones&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Texto consolidado de indicaciones de preparación clínica seleccionadas.</p>
          </div>
          <div class="p-2 bg-white rounded border border-slate-200">
            <code class="text-slate-700 font-bold font-mono">&#123;&#123;sucursal_nombre&#125;&#125;</code>
            <p class="text-[11px] text-slate-500 mt-0.5">Nombre de la sede o sucursal donde se emitió la orden médica.</p>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Entendido" severity="primary" size="small" @click="isHelpVariablesVisible = false" />
      </template>
    </Dialog>
  </div>
</template>
