<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { pacientesService } from '../../services/pacientes.service';
import { ordenesService } from '../../services/ordenes.service';
import { usersService } from '../../services/users.service';
import { mutualesService } from '../../services/mutuales.service';
import { useAuthStore } from '../../stores/auth.store';
import { ObraSocial, PacienteSearchResult, Sucursal } from '../../types';

import AutoComplete from 'primevue/autocomplete';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Calendar from 'primevue/calendar';
import Chips from 'primevue/chips';
import Dropdown from 'primevue/dropdown';
import Textarea from 'primevue/textarea';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import { useToast } from 'primevue/usetoast';
import { PacienteCreate } from '../../types/pacientes';
import { OrdenMedicaListItem } from '../../types/ordenes';
import StatusTag from '../../components/common/StatusTag.vue';




const router = useRouter();
const toast = useToast();
const authStore = useAuthStore();

const isSubmitting = ref(false);
const sucursales = ref<Sucursal[]>([]);
const mutuales = ref<ObraSocial[]>([]);

const opcionesHorarios = [
  'Todo el día',
  'Por la mañana',
  'Por la tarde',
  'Por la noche',
  'Solo WhatsApp',
  'Solo mail',
];


// Patient search state
const selectedPaciente = ref<PacienteSearchResult | null>(null);
const patientSuggestions = ref<PacienteSearchResult[]>([]);
const pacienteOrdenesAbiertas = ref<OrdenMedicaListItem[]>([]);
const isLoadingAlertas = ref(false);

const checkPacienteOrdenesAbiertas = async (pacienteId: string) => {
  isLoadingAlertas.value = true;
  try {
    const res = await ordenesService.list({ paciente_id: pacienteId, limit: 100 });
    const cerradas = ['Cerrada ok', 'Cerrada', 'Cancelada'];
    pacienteOrdenesAbiertas.value = res.items.filter((o) => !cerradas.includes(o.estado));
  } catch {
    pacienteOrdenesAbiertas.value = [];
  } finally {
    isLoadingAlertas.value = false;
  }
};


// Form fields
const form = ref({
  sucursal_id: authStore.user?.sucursal_id || '',
  fecha_prescripcion: new Date(),
  cantidad_ordenes_fisicas: 1,
  mutual: '',
  nro_afiliado: '',
  valor_copago: 0,
  valor_estudios_no_autorizados: 0,
  abona_apb: false,
  fecha_vencimiento: null as Date | null,
  numeros_auditoria: [] as string[],
  debe_orden_medica: false,
  contacto_nombre: '',
  contacto_horario: '',
  contacto_telefono: '',
  contacto_celular: '',
  contacto_email: '',
  observaciones_ingreso: '',
});

// Inline Create Patient State
const isCreatePatientVisible = ref(false);
const isSavingPatient = ref(false);
const newPatientForm = ref<PacienteCreate>({
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

const openCreatePatientModal = (queryText = '') => {
  newPatientForm.value = {
    documento: /^\d+$/.test(queryText.trim()) ? queryText.trim() : '',
    nombres: '',
    apellidos: !/^\d+$/.test(queryText.trim()) ? queryText.trim().toUpperCase() : '',
    fecha_nacimiento: null,
    obra_social: form.value.mutual || '',
    nro_afiliado: '',
    telefono: '',
    email: '',
    is_active: true,
  };
  isCreatePatientVisible.value = true;
};

const handleSaveInlinePatient = async () => {
  if (
    !newPatientForm.value.documento.trim() ||
    !newPatientForm.value.nombres.trim() ||
    !newPatientForm.value.apellidos.trim() ||
    !newPatientForm.value.fecha_nacimiento
  ) {
    toast.add({
      severity: 'warn',
      summary: 'Atención',
      detail: 'Documento, Nombres, Apellidos y Fecha de Nacimiento son obligatorios',
      life: 3500,
    });
    return;
  }

  isSavingPatient.value = true;
  try {
    const payload = {
      ...newPatientForm.value,
      documento: newPatientForm.value.documento.trim(),
      nombres: newPatientForm.value.nombres.trim(),
      apellidos: newPatientForm.value.apellidos.trim(),
      fecha_nacimiento: newPatientForm.value.fecha_nacimiento || null,
      email: newPatientForm.value.email?.trim() || null,
      telefono: newPatientForm.value.telefono?.trim() || null,
      nro_afiliado: newPatientForm.value.nro_afiliado?.trim() || null,
      obra_social: newPatientForm.value.obra_social?.trim() || null,
    };
    const created = await pacientesService.create(payload as any);
    toast.add({ severity: 'success', summary: 'Paciente Registrado', detail: 'Paciente creado y seleccionado con éxito', life: 3000 });

    selectedPaciente.value = {
      id: created.id,
      documento: created.documento,
      nombre_completo: created.nombre_completo,
      obra_social: created.obra_social,
      nro_afiliado: created.nro_afiliado,
      telefono: created.telefono,
    };

    // Auto-completar datos de contacto y cobertura
    form.value.contacto_nombre = created.nombre_completo;
    form.value.contacto_telefono = created.telefono || '';
    form.value.contacto_celular = created.telefono || '';
    form.value.contacto_email = created.email || '';
    if (created.obra_social) {
      form.value.mutual = created.obra_social;
    }
    if (created.nro_afiliado) {
      form.value.nro_afiliado = created.nro_afiliado;
    }

    await checkPacienteOrdenesAbiertas(created.id);
    handleMutualChange(form.value.mutual);
    isCreatePatientVisible.value = false;

  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Error al crear paciente', life: 4000 });
  } finally {
    isSavingPatient.value = false;
  }
};


onMounted(async () => {
  const [sucRes, mutRes] = await Promise.all([
    usersService.listSucursales(),
    mutualesService.list(),
  ]);
  sucursales.value = sucRes;
  mutuales.value = mutRes;

  if (!form.value.sucursal_id && sucursales.value.length > 0) {
    form.value.sucursal_id = sucursales.value[0].id;
  }
});

const handleMutualChange = (mutualSigla?: string) => {
  const sig = mutualSigla || form.value.mutual;
  if (!sig) return;
  const mut = mutuales.value.find(
    (m) =>
      m.sigla?.toUpperCase() === sig.trim().toUpperCase() ||
      m.codigo?.toUpperCase() === sig.trim().toUpperCase()
  );
  if (mut) {
    // 1. Días de vencimiento
    if (form.value.fecha_prescripcion) {
      const baseDate = new Date(form.value.fecha_prescripcion);
      const dias = mut.dias_vencimiento || 30;
      form.value.fecha_vencimiento = new Date(
        baseDate.getTime() + dias * 24 * 60 * 60 * 1000
      );
    }
    // 2. Copago por defecto sugerido
    if (mut.copago_default !== undefined && mut.copago_default !== null) {
      form.value.valor_copago = Number(mut.copago_default);
    }
  }
};


const searchPatients = async (event: { query: string }) => {
  if (event.query.trim().length >= 2) {
    patientSuggestions.value = await pacientesService.search(event.query.trim());
  }
};

const handleSelectPatient = async (e: any) => {
  const p: PacienteSearchResult = e.value;
  if (p && p.id) {
    try {
      const fullPaciente = await pacientesService.getById(p.id);
      form.value.contacto_nombre = fullPaciente.nombre_completo;
      form.value.contacto_telefono = fullPaciente.telefono || '';
      form.value.contacto_celular = fullPaciente.telefono || '';
      form.value.contacto_email = fullPaciente.email || '';
      if (fullPaciente.obra_social) {
        form.value.mutual = fullPaciente.obra_social;
        handleMutualChange(fullPaciente.obra_social);
      }
      if (fullPaciente.nro_afiliado) {
        form.value.nro_afiliado = fullPaciente.nro_afiliado;
      }
    } catch {
      form.value.contacto_nombre = p.nombre_completo;
      form.value.contacto_telefono = p.telefono || '';
      form.value.contacto_celular = p.telefono || '';
      if (p.obra_social) {
        form.value.mutual = p.obra_social;
        handleMutualChange(p.obra_social);
      }
      if (p.nro_afiliado) {
        form.value.nro_afiliado = p.nro_afiliado;
      }
    }
    await checkPacienteOrdenesAbiertas(p.id);
  }
};



const handleSubmit = async () => {
  if (!selectedPaciente.value?.id) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe seleccionar un paciente registrado', life: 3000 });
    return;
  }

  if (!form.value.fecha_prescripcion) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'La fecha de prescripción médica es obligatoria', life: 3000 });
    return;
  }

  if (!form.value.mutual?.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe indicar la mutual u obra social', life: 3000 });
    return;
  }

  if (!form.value.nro_afiliado?.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'El número de credencial / afiliado es obligatorio', life: 3000 });
    return;
  }

  if (!form.value.cantidad_ordenes_fisicas || form.value.cantidad_ordenes_fisicas < 1) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'La cantidad de recetas físicas debe ser mayor a 0', life: 3000 });
    return;
  }

  if (!form.value.contacto_nombre?.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'El nombre de contacto es obligatorio', life: 3000 });
    return;
  }

  const tel = form.value.contacto_telefono?.trim();
  const cel = form.value.contacto_celular?.trim();
  if (!tel && !cel) {
    toast.add({
      severity: 'warn',
      summary: 'Atención',
      detail: 'Debe ingresar al menos un número de contacto (Teléfono fijo o Celular / WhatsApp)',
      life: 3500,
    });
    return;
  }

  if (!form.value.contacto_horario?.trim()) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe seleccionar el horario preferido de contacto', life: 3000 });
    return;
  }

  if (!form.value.sucursal_id) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe seleccionar la sucursal emisora', life: 3000 });
    return;
  }

  isSubmitting.value = true;
  try {
    const formattedDate = (d: Date) => d.toISOString().slice(0, 10);

    const payload = {
      paciente_id: selectedPaciente.value.id,
      sucursal_id: form.value.sucursal_id,
      fecha_prescripcion: formattedDate(form.value.fecha_prescripcion),
      cantidad_ordenes_fisicas: form.value.cantidad_ordenes_fisicas,
      mutual: form.value.mutual.trim().toUpperCase(),
      nro_afiliado: form.value.nro_afiliado.trim(),
      valor_copago: form.value.valor_copago,
      valor_estudios_no_autorizados: form.value.valor_estudios_no_autorizados,
      abona_apb: form.value.abona_apb,
      fecha_vencimiento: form.value.fecha_vencimiento ? formattedDate(form.value.fecha_vencimiento) : null,
      debe_orden_medica: form.value.debe_orden_medica,

      numeros_auditoria: form.value.numeros_auditoria,
      contacto_nombre: form.value.contacto_nombre.trim(),
      contacto_horario: form.value.contacto_horario.trim(),
      contacto_telefono: form.value.contacto_telefono?.trim() || null,
      contacto_celular: form.value.contacto_celular?.trim() || null,
      contacto_email: form.value.contacto_email?.trim() || null,
      observaciones_ingreso: form.value.observaciones_ingreso?.trim() || null,
    };

    const newOrder = await ordenesService.create(payload as any);
    toast.add({
      severity: 'success',
      summary: 'Orden Creada',
      detail: `Se registró la orden ${newOrder.nro_orden} con éxito.`,
      life: 4000,
    });
    router.push(`/ordenes/${newOrder.id}`);
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo crear la orden médica',
      life: 4000,
    });
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Registrar Nueva Orden Médica</h2>
        <p class="text-sm text-slate-500">Ingrese los datos clínicos, prescripción y contacto del paciente</p>
      </div>
      <router-link to="/ordenes">
        <Button label="Volver a la Lista" icon="pi pi-arrow-left" text severity="secondary" />
      </router-link>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- 1. Paciente Selector Card -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 class="text-base font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
          <i class="pi pi-user text-blue-600"></i>
          <span>1. Selección del Paciente</span>
        </h3>


        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="block text-xs font-semibold text-slate-700 uppercase">
              Buscar Paciente por DNI o Nombre <span class="text-red-500">*</span>
            </label>
            <Button
              label="+ Nuevo Paciente"
              icon="pi pi-user-plus"
              text
              size="small"
              severity="primary"
              class="text-xs p-0"
              @click="openCreatePatientModal()"
            />
          </div>
          <div class="flex gap-2">
            <AutoComplete
              v-model="selectedPaciente"
              :suggestions="patientSuggestions"
              @complete="searchPatients"
              @item-select="handleSelectPatient"
              optionLabel="nombre_completo"
              placeholder="Escriba DNI o Apellido/Nombre..."
              class="w-full flex-1"
              inputClass="w-full"
            >
              <template #option="{ option }">
                <div class="py-1">
                  <p class="text-sm font-semibold text-slate-800">{{ option.nombre_completo }}</p>
                  <p class="text-xs text-slate-500">DNI: {{ option.documento }} &bull; Obra Social: {{ option.obra_social || 'S/D' }}</p>
                </div>
              </template>
            </AutoComplete>
            <Button
              icon="pi pi-plus"
              severity="secondary"
              outlined
              title="Registrar nuevo paciente"
              @click="openCreatePatientModal()"
            />
          </div>
        </div>


        <div v-if="selectedPaciente?.id" class="p-3 bg-blue-50 rounded-lg border border-blue-200 flex items-center justify-between">
          <div>
            <p class="text-xs font-bold text-blue-800 uppercase">Paciente Seleccionado</p>
            <p class="text-sm font-semibold text-slate-800">{{ selectedPaciente.nombre_completo }} (DNI: {{ selectedPaciente.documento }})</p>
          </div>
          <Button icon="pi pi-times" severity="danger" text rounded size="small" @click="selectedPaciente = null; pacienteOrdenesAbiertas = []" />
        </div>


        <!-- Alerta de Auditorías / Órdenes Abiertas No Cerradas -->
        <div v-if="pacienteOrdenesAbiertas.length > 0" class="p-4 bg-amber-50 rounded-xl border-2 border-amber-300 shadow-sm space-y-2">
          <div class="flex items-start gap-3">
            <i class="pi pi-exclamation-triangle text-amber-600 text-xl mt-0.5"></i>
            <div class="flex-1 text-xs">
              <p class="font-bold text-amber-900 text-sm">
                Aviso: El paciente registra {{ pacienteOrdenesAbiertas.length }} orden(es) en proceso no cerrada(s)
              </p>
              <p class="text-amber-800 mt-1">
                Este paciente ya posee órdenes activas en el sistema. Puede continuar cargando esta nueva orden si corresponde:
              </p>
              <div class="flex flex-wrap gap-2 mt-2.5">
                <span
                  v-for="o in pacienteOrdenesAbiertas"
                  :key="o.id"
                  class="px-2.5 py-1 bg-white rounded-lg border border-amber-300 font-mono text-xs font-bold text-slate-800 flex items-center gap-2 shadow-sm"
                >
                  <span>{{ o.nro_orden }}</span>
                  <StatusTag :value="o.estado" />
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>


      <!-- 2. Datos de la Orden Médica -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 class="text-base font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
          <i class="pi pi-file text-blue-600"></i>
          <span>2. Prescripción y Datos Médicos</span>
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Fecha Prescripcion -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Fecha de Prescripción <span class="text-red-500">*</span>
            </label>
            <Calendar v-model="form.fecha_prescripcion" dateFormat="yy-mm-dd" showIcon class="w-full" @date-select="handleMutualChange(form.mutual)" />
          </div>

          <!-- Mutual Dropdown -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Mutual / Obra Social <span class="text-red-500">*</span>
            </label>
            <Dropdown
              v-model="form.mutual"
              :options="mutuales"
              optionLabel="display_name"
              optionValue="sigla"
              placeholder="Seleccionar mutual..."
              filter
              class="w-full"
              @change="handleMutualChange(form.mutual)"
            />
          </div>

          <!-- Nro Afiliado -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              N° Afiliado / Credencial <span class="text-red-500">*</span>
            </label>
            <InputText v-model="form.nro_afiliado" placeholder="Ej: 12345678/01" class="w-full" />
          </div>

          <!-- Copago -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Valor Copago a Abonar ($)
            </label>
            <InputNumber v-model="form.valor_copago" mode="currency" currency="ARS" locale="es-AR" class="w-full" />
          </div>

          <!-- Valor Estudios No Autorizados -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Estudios No Autorizados ($)
            </label>
            <InputNumber v-model="form.valor_estudios_no_autorizados" mode="currency" currency="ARS" locale="es-AR" class="w-full" />
          </div>


          <!-- Cantidad Cupones -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Cantidad de Recetas Físicas <span class="text-red-500">*</span>
            </label>
            <InputNumber v-model="form.cantidad_ordenes_fisicas" :min="1" :max="50" showButtons class="w-full" />
          </div>

          <!-- Fecha Vencimiento -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Fecha de Vencimiento
            </label>
            <Calendar v-model="form.fecha_vencimiento" dateFormat="yy-mm-dd" showIcon class="w-full" />
          </div>

          <!-- Sucursal -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Sucursal Emisora <span class="text-red-500">*</span>
            </label>
            <Dropdown
              v-model="form.sucursal_id"
              :options="sucursales"
              optionLabel="nombre"
              optionValue="id"
              placeholder="Seleccionar sede"
              class="w-full"
            />
          </div>
        </div>

        <!-- Numeros de auditoria -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Números / Códigos de Auditoría (Presione Enter para agregar múltiples)
          </label>
          <Chips v-model="form.numeros_auditoria" placeholder="Ej: AUT-1029, AUT-1030..." class="w-full" />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <!-- Checkbox: Acto Profesional Bioquímico (APB) -->
          <div class="p-3.5 bg-blue-50/70 rounded-xl border border-blue-200 flex items-start space-x-3">
            <Checkbox v-model="form.abona_apb" binary inputId="abonaApb" />
            <div>
              <label for="abonaApb" class="text-xs font-bold text-blue-900 cursor-pointer block">
                🧪 Abona APB (Acto Profesional Bioquímico)
              </label>
              <p class="text-[11px] text-blue-700 mt-0.5">
                Marque si el paciente debe abonar el Acto Profesional Bioquímico según el convenio mutual.
              </p>
            </div>
          </div>

          <!-- Checkbox: Paciente Debe Orden Medica Fisica -->
          <div class="p-3.5 bg-red-50/80 rounded-xl border border-red-200 flex items-start space-x-3">
            <Checkbox v-model="form.debe_orden_medica" binary inputId="debeOrdenFisica" />
            <div>
              <label for="debeOrdenFisica" class="text-xs font-bold text-red-900 cursor-pointer block">
                ⚠️ Paciente DEBE la Orden Médica Física
              </label>
              <p class="text-[11px] text-red-700 mt-0.5">
                Alerta roja para exigir la receta física original el día de la atención.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Datos de Contacto y Seguimiento -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 class="text-base font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
          <i class="pi pi-phone text-blue-600"></i>
          <span>3. Datos de Contacto para Notificaciones</span>
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Nombre de Contacto <span class="text-red-500">*</span>
            </label>
            <InputText v-model="form.contacto_nombre" placeholder="Nombre de quien retira o familiar" class="w-full" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Teléfono Fijo <span class="text-slate-400 font-normal text-[10px]">(o Celular)</span>
            </label>
            <InputText v-model="form.contacto_telefono" placeholder="Ej: 11-4455-6677" class="w-full" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Celular / WhatsApp <span class="text-slate-400 font-normal text-[10px]">(o Fijo)</span>
            </label>
            <InputText v-model="form.contacto_celular" placeholder="Ej: 11-9876-5432" class="w-full" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Horario Preferido <span class="text-red-500">*</span>
            </label>
            <Dropdown
              v-model="form.contacto_horario"
              :options="opcionesHorarios"
              placeholder="Seleccionar horario"
              class="w-full"
            />
          </div>


          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Correo Electrónico</label>
            <InputText v-model="form.contacto_email" type="email" placeholder="paciente@correo.com" class="w-full" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Observaciones de Ingreso</label>
          <Textarea v-model="form.observaciones_ingreso" rows="3" class="w-full" placeholder="Detalle clínico o notas de admisión..." />
        </div>
      </div>

      <!-- Submit Buttons -->
      <div class="flex items-center justify-end space-x-3 pt-4">
        <router-link to="/ordenes">
          <Button label="Cancelar" severity="secondary" text />
        </router-link>
        <Button
          type="submit"
          label="Registrar Orden Médica"
          icon="pi pi-check"
          size="large"
          :loading="isSubmitting"
        />
      </div>
    </form>

    <!-- Modal para crear paciente directamente -->
    <Dialog
      v-model:visible="isCreatePatientVisible"
      modal
      header="Registrar Nuevo Paciente"
      :style="{ width: '550px' }"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">DNI / Documento <span class="text-red-500">*</span></label>
            <InputText v-model="newPatientForm.documento" placeholder="Sin puntos" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Fecha Nacimiento <span class="text-red-500">*</span>
            </label>
            <InputText v-model="newPatientForm.fecha_nacimiento as any" type="date" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Apellidos <span class="text-red-500">*</span></label>
            <InputText v-model="newPatientForm.apellidos" placeholder="PÉREZ" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Nombres <span class="text-red-500">*</span></label>
            <InputText v-model="newPatientForm.nombres" placeholder="Juan Carlos" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Obra Social / Mutual</label>
            <Dropdown
              v-model="newPatientForm.obra_social as any"
              :options="mutuales"
              optionLabel="display_name"
              optionValue="sigla"
              placeholder="Seleccionar mutual..."
              filter
              showClear
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">N° Afiliado</label>
            <InputText v-model="newPatientForm.nro_afiliado as any" placeholder="N° de credencial" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Teléfono / Celular</label>
            <InputText v-model="newPatientForm.telefono as any" placeholder="11-4567-8900" class="w-full" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">Correo Electrónico</label>
            <InputText v-model="newPatientForm.email as any" type="email" placeholder="paciente@correo.com" class="w-full" />
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Cancelar" text severity="secondary" @click="isCreatePatientVisible = false" />
        <Button
          label="Guardar y Seleccionar"
          icon="pi pi-check"
          :loading="isSavingPatient"
          @click="handleSaveInlinePatient"
        />
      </template>
    </Dialog>
  </div>
</template>

