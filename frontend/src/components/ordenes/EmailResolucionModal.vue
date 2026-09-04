<script setup lang="ts">
import { ref, watch } from 'vue';
import { ordenesService } from '../../services/ordenes.service';
import { PreviewEmailResolucion, OrdenMedicaDetail } from '../../types/ordenes';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import Textarea from 'primevue/textarea';
import Tag from 'primevue/tag';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import { formatDateTime } from '../../utils/date';
import { useToast } from 'primevue/usetoast';

const props = defineProps<{
  visible: boolean;
  orden: OrdenMedicaDetail;
}>();

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void;
  (e: 'sent', orden: OrdenMedicaDetail): void;
}>();

const toast = useToast();

const previewData = ref<PreviewEmailResolucion | null>(null);
const isLoading = ref(true);
const isSending = ref(false);
const isEditing = ref(false);

const emailDestinatario = ref('');
const emailAsunto = ref('');
const emailCuerpoHtml = ref('');
const selectedPlantillaId = ref<string | null>(null);
const activeView = ref<'visual' | 'codigo'>('visual');

const loadPreview = async (plantillaId?: string) => {
  if (!props.orden?.id) return;
  isLoading.value = true;
  isEditing.value = false;
  try {
    const res = await ordenesService.previewEmail(props.orden.id);
    previewData.value = res;
    emailDestinatario.value = res.destinatario_email;
    emailAsunto.value = res.asunto;
    emailCuerpoHtml.value = res.cuerpo_html;
    if (plantillaId) {
      selectedPlantillaId.value = plantillaId;
    } else if (res.plantilla_id) {
      selectedPlantillaId.value = res.plantilla_id;
    }
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo generar la vista previa del correo',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

const handleSelectPlantilla = (tplId: string) => {
  if (!previewData.value?.plantillas_disponibles) return;
  const tpl = previewData.value.plantillas_disponibles.find((t) => t.id === tplId);
  if (!tpl) return;
  selectedPlantillaId.value = tpl.id;
  emailAsunto.value = tpl.asunto.replace('{{nro_orden}}', props.orden.nro_orden);
  // Re-renderizar si la plantilla tiene custom HTML
  if (tpl.cuerpo_html && tpl.cuerpo_html.trim()) {
    let html = tpl.cuerpo_html;
    const autStr = (props.orden.estudios_autorizados || []).join(', ') || 'Todas las prácticas de la prescripción médica';
    const noAutStr = (props.orden.estudios_no_autorizados || []).join(', ') || 'Ninguno (100% autorizado)';
    const copago = Number(props.orden.valor_copago || 0);
    const noAut = Number(props.orden.valor_estudios_no_autorizados || 0);
    const apb = Number(props.orden.valor_apb || 0);
    const total = copago + noAut + apb;

    html = html.replace(/{{paciente_nombre}}/g, props.orden.contacto_nombre || props.orden.paciente?.nombre_completo || 'Paciente');
    html = html.replace(/{{nro_orden}}/g, props.orden.nro_orden);
    html = html.replace(/{{mutual}}/g, props.orden.mutual || '');
    html = html.replace(/{{observacion_resultado}}/g, props.orden.observacion_resultado_auditoria || 'Auditoría médica aprobada.');
    html = html.replace(/{{copago}}/g, `$ ${copago.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`);
    html = html.replace(/{{estudios_no_autorizados_valor}}/g, `$ ${noAut.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`);
    html = html.replace(/{{valor_apb}}/g, `$ ${apb.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`);
    html = html.replace(/{{total_abonar}}/g, `$ ${total.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`);
    html = html.replace(/{{estudios_autorizados}}/g, autStr);
    html = html.replace(/{{estudios_no_autorizados}}/g, noAutStr);
    html = html.replace(/{{indicaciones}}/g, props.orden.indicaciones_texto || '');
    html = html.replace(/{{sucursal_nombre}}/g, props.orden.sucursal?.nombre || 'Sede Central');
    emailCuerpoHtml.value = html;
  } else {
    // Restaurar el cuerpo original predeterminado
    if (previewData.value?.cuerpo_html) {
      emailCuerpoHtml.value = previewData.value.cuerpo_html;
    }
  }
};

watch(
  () => props.visible,
  (val) => {
    if (val) {
      loadPreview();
    }
  }
);

const handleSend = async () => {
  if (!emailDestinatario.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe ingresar una dirección de correo de destino', life: 3000 });
    return;
  }

  isSending.value = true;
  try {
    const updatedOrden = await ordenesService.enviarEmail(props.orden.id, {
      destinatario_email: emailDestinatario.value.trim(),
      asunto: emailAsunto.value.trim(),
      cuerpo_html: emailCuerpoHtml.value,
      plantilla_id: selectedPlantillaId.value,
    });

    toast.add({
      severity: 'success',
      summary: 'Correo Despachado',
      detail: `Resolución e indicaciones enviadas a ${emailDestinatario.value}`,
      life: 4000,
    });

    emit('sent', updatedOrden);
    emit('update:visible', false);
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error al Enviar',
      detail: err.response?.data?.detail || 'Ocurrió un error al despachar el correo',
      life: 4500,
    });
  } finally {
    isSending.value = false;
  }
};
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="Correo de Notificación y Resolución Médica (ZeptoMail)"
    :style="{ width: '740px', maxWidth: '96vw' }"
    @update:visible="emit('update:visible', $event)"
  >
    <LoadingSpinner v-if="isLoading" message="Armando correo y formateando resolución..." class="py-12" />

    <div v-else-if="previewData" class="space-y-4">
      <!-- Badge de Estado de Envío -->
      <div
        class="p-3 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs"
        :class="orden.mail_enviado ? 'bg-emerald-50 border-emerald-300 text-emerald-950' : 'bg-blue-50 border-blue-200 text-blue-950'"
      >
        <div class="flex items-center gap-2">
          <i :class="orden.mail_enviado ? 'pi pi-check-circle text-emerald-600 text-lg' : 'pi pi-envelope text-blue-600 text-lg'"></i>
          <div>
            <span class="font-bold block">
              {{ orden.mail_enviado ? '✅ Correo ya enviado previamente' : 'Listo para despachar' }}
            </span>
            <span v-if="orden.mail_enviado_fecha" class="text-[11px] text-slate-500">
              Despachado el {{ formatDateTime(orden.mail_enviado_fecha) }} a <strong>{{ orden.mail_destinatario }}</strong>
            </span>
            <span v-else class="text-[11px] text-slate-500">
              Revise los datos, edite el asunto o cuerpo si es necesario y presione Enviar.
            </span>
          </div>
        </div>
        <Tag
          :value="orden.mail_enviado ? 'ENVIADO' : 'PENDIENTE DE ENVÍO'"
          :severity="orden.mail_enviado ? 'success' : 'warn'"
          class="text-[10px] shrink-0"
        />
      </div>

      <!-- Alerta si no tiene email -->
      <div v-if="!emailDestinatario" class="p-2.5 bg-amber-50 rounded-lg border border-amber-300 text-xs text-amber-900 flex items-center gap-2">
        <i class="pi pi-exclamation-triangle text-amber-600"></i>
        <span>Esta orden médica no cuenta con correo registrado. Ingréselo en el campo de abajo para poder enviar el correo.</span>
      </div>

      <!-- Selector de Plantilla y Destinatario -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div class="sm:col-span-1">
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Plantilla</label>
          <Dropdown
            v-model="selectedPlantillaId"
            :options="previewData.plantillas_disponibles || []"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Seleccionar plantilla..."
            class="w-full text-xs"
            @change="handleSelectPlantilla($event.value)"
          />
        </div>
        <div class="sm:col-span-1">
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Destinatario <span
              class="text-red-500">*</span></label>
          <InputText v-model="emailDestinatario" type="email" placeholder="paciente@correo.com"
            class="w-full text-xs" />
        </div>
        <div class="sm:col-span-2">
          <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Asunto</label>
          <InputText v-model="emailAsunto" class="w-full text-xs font-semibold" />
        </div>
      </div>

      <!-- Barra de herramientas de previsualización -->
      <div class="flex items-center justify-between pt-2 border-t border-slate-200">
        <span class="text-xs font-bold text-slate-700 uppercase">Vista Previa del Mensaje</span>
        <div class="flex items-center space-x-1">
          <Button
            label="Visual"
            size="small"
            :severity="activeView === 'visual' ? 'primary' : 'secondary'"
            :outlined="activeView !== 'visual'"
            class="text-xs py-0.5 px-2"
            @click="activeView = 'visual'"
          />
          <Button
            label="Código / Editar HTML"
            size="small"
            :severity="activeView === 'codigo' ? 'primary' : 'secondary'"
            :outlined="activeView !== 'codigo'"
            class="text-xs py-0.5 px-2"
            @click="activeView = 'codigo'"
          />
        </div>
      </div>

      <!-- Visor HTML o Editor -->
      <div class="border border-slate-200 rounded-xl overflow-hidden bg-slate-100 max-h-[420px] overflow-y-auto">
        <iframe
          v-if="activeView === 'visual'"
          :srcdoc="emailCuerpoHtml"
          class="w-full h-[400px] bg-white border-0"
          sandbox="allow-same-origin"
        ></iframe>

        <div v-else class="p-2 bg-slate-900 text-slate-100 font-mono text-xs">
          <Textarea
            v-model="emailCuerpoHtml"
            rows="16"
            class="w-full text-xs font-mono bg-slate-950 text-slate-100 border border-slate-700 rounded p-2"
          />
        </div>
      </div>

      <!-- Nota al pie informativa -->
      <p class="text-[11px] text-slate-400 italic">
        * El envío del correo electrónico no da por cumplida la llamada directa al paciente. La orden médica continuará en la bandeja de Llamadas Pendientes hasta que se registre el contacto telefónico formal.
      </p>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <Button label="Cerrar" text severity="secondary" @click="emit('update:visible', false)" />

        <div class="flex items-center gap-2">
          <Button
            v-if="orden.mail_enviado"
            label="Reenviar Correo"
            icon="pi pi-send"
            severity="secondary"
            size="small"
            :loading="isSending"
            @click="handleSend"
          />
          <Button
            v-else
            label="Enviar Correo al Paciente"
            icon="pi pi-send"
            severity="primary"
            :loading="isSending"
            :disabled="!emailDestinatario"
            @click="handleSend"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
