<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import { useToast } from 'primevue/usetoast';
import { ordenesService } from '../../services/ordenes.service';

const props = defineProps<{
  visible: boolean;
  ordenId?: string | null;
  initialData?: {
    paciente_nombre?: string;
    nro_orden?: string;
    mutual?: string;
    fecha?: string;
    sucursal_nombre?: string;
    contacto_telefono?: string;
    indicaciones_html?: string;
    indicaciones_texto?: string;
  } | null;
}>();

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
}>();

const toast = useToast();
const isLoading = ref(false);
const incluirDefault = ref(true);
const htmlContent = ref('');
const iframeRef = ref<HTMLIFrameElement | null>(null);

const cachedData = ref<{
  paciente_nombre: string;
  nro_orden: string;
  mutual: string;
  fecha: string;
  sucursal_nombre: string;
  contacto_telefono: string;
  indicaciones_html: string;
  indicacion_default: string;
  template_html: string;
} | null>(null);

const loadData = async () => {
  isLoading.value = true;
  try {
    if (props.ordenId) {
      const res = await ordenesService.getOrdenImprimirIndicacionesData(props.ordenId);
      cachedData.value = {
        paciente_nombre: res.paciente_nombre,
        nro_orden: res.nro_orden,
        mutual: res.mutual,
        fecha: res.fecha,
        sucursal_nombre: res.sucursal_nombre,
        contacto_telefono: res.contacto_telefono,
        indicaciones_html: res.indicaciones_html,
        indicacion_default: res.indicacion_default,
        template_html: res.template_html,
      };
      renderHtml();
    } else if (props.initialData) {
      const res = await ordenesService.previewImprimirIndicaciones({
        paciente_nombre: props.initialData.paciente_nombre,
        nro_orden: props.initialData.nro_orden,
        mutual: props.initialData.mutual,
        fecha: props.initialData.fecha,
        contacto_telefono: props.initialData.contacto_telefono,
        indicaciones_html: props.initialData.indicaciones_html || props.initialData.indicaciones_texto,
        incluir_default: incluirDefault.value,
      });
      htmlContent.value = res.html_ensamblado;
      updateIframe();
    }
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error cargando plantilla de impresión',
      detail: err?.response?.data?.detail || 'No se pudo generar la vista previa',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

const renderHtml = () => {
  if (!cachedData.value) return;
  const data = cachedData.value;
  let tpl = data.template_html;

  const defaultHtml = incluirDefault.value ? data.indicacion_default : '';

  const replacements: Record<string, string> = {
    '{{paciente_nombre}}': data.paciente_nombre || 'Paciente',
    '{{fecha}}': data.fecha || '',
    '{{sucursal_nombre}}': data.sucursal_nombre || 'Sede Central',
    '{{contacto_telefono}}': data.contacto_telefono || '',
    '{{nro_orden}}': data.nro_orden || 'S/N',
    '{{mutual}}': data.mutual || 'Particular',
    '{{indicaciones}}': data.indicaciones_html || '<p><em>No se registraron indicaciones adicionales.</em></p>',
    '{{indicacion_default}}': defaultHtml,
  };

  for (const [key, val] of Object.entries(replacements)) {
    tpl = tpl.split(key).join(val);
  }

  htmlContent.value = tpl;
  updateIframe();
};

const updateIframe = () => {
  nextTick(() => {
    if (!iframeRef.value) return;
    const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow?.document;
    if (doc) {
      doc.open();
      doc.write(htmlContent.value);
      doc.close();
    }
  });
};

watch(
  () => props.visible,
  (val) => {
    if (val) {
      incluirDefault.value = true;
      loadData();
    } else {
      htmlContent.value = '';
      cachedData.value = null;
    }
  }
);

watch(incluirDefault, () => {
  if (cachedData.value) {
    renderHtml();
  } else if (props.initialData) {
    loadData();
  }
});

const handlePrint = () => {
  if (!iframeRef.value) return;
  try {
    const win = iframeRef.value.contentWindow;
    if (win) {
      win.focus();
      win.print();
    }
  } catch {
    // Fallback: abrir en ventana emergente e imprimir
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(htmlContent.value);
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
    }
  }
};

const handleOpenNewTab = () => {
  const newWin = window.open('', '_blank');
  if (newWin) {
    newWin.document.write(htmlContent.value);
    newWin.document.close();
  }
};
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :style="{ width: '880px', maxWidth: '96vw' }"
    :header="`Vista Previa de Impresión de Indicaciones`"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-3">
      <!-- Barra de Opciones Superior -->
      <div class="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
        <div class="flex items-center gap-2">
          <Checkbox v-model="incluirDefault" inputId="chkDefault" binary />
          <label for="chkDefault" class="font-medium text-slate-700 cursor-pointer select-none">
            Incluir requisitos generales y horarios de recepción
          </label>
        </div>

        <div class="flex items-center gap-2">
          <Button
            label="Abrir en pestaña nueva"
            icon="pi pi-external-link"
            size="small"
            text
            severity="secondary"
            class="text-xs"
            @click="handleOpenNewTab"
            title="Abre el documento en una pestaña limpia"
          />
        </div>
      </div>

      <!-- Visor con Iframe A4 -->
      <div class="relative bg-slate-200 rounded-lg border border-slate-300 p-2 sm:p-4 overflow-hidden flex justify-center">
        <div v-if="isLoading" class="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
          <div class="flex items-center gap-2 text-sm text-slate-600 font-medium">
            <i class="pi pi-spin pi-spinner text-blue-600 text-lg"></i>
            Generando documento para impresión...
          </div>
        </div>

        <iframe
          ref="iframeRef"
          class="w-full h-[520px] bg-white rounded shadow-md border border-slate-300"
          title="Vista Previa de Indicaciones"
        ></iframe>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <span class="text-xs text-slate-400">
          💡 En el diálogo de impresión puede seleccionar su impresora o elegir "Guardar como PDF".
        </span>

        <div class="flex items-center gap-2">
          <Button label="Cerrar" text severity="secondary" size="small" @click="emit('update:visible', false)" />
          <Button
            label="Imprimir / Guardar PDF"
            icon="pi pi-print"
            severity="primary"
            size="small"
            :loading="isLoading"
            @click="handlePrint"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
