<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import { useToast } from 'primevue/usetoast';
import { OrdenMedicaDetail, IndicacionEstudio } from '../../types/ordenes';
import { configService } from '../../services/config.service';

const props = defineProps<{
  visible: boolean;
  orden: OrdenMedicaDetail | null;
  catalogoIndicaciones?: IndicacionEstudio[];
}>();

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
}>();

const toast = useToast();
const copied = ref(false);
const copiedWhatsapp = ref(false);
const tabSpeech = ref<'telefono' | 'whatsapp'>('telefono');
const catalogoInterno = ref<IndicacionEstudio[]>([]);

// Cargar catálogo de indicaciones si no vino provisto
const cargarCatalogoSiFalta = async () => {
  if ((!props.catalogoIndicaciones || props.catalogoIndicaciones.length === 0) && catalogoInterno.value.length === 0) {
    try {
      const list = await configService.listIndicaciones(true);
      catalogoInterno.value = list;
    } catch {
      // Ignorar fallback
    }
  }
};

onMounted(() => {
  cargarCatalogoSiFalta();
});

watch(() => props.visible, (val) => {
  if (val) {
    cargarCatalogoSiFalta();
  }
});

// Nombre y apellido
const nombrePaciente = computed(() => {
  if (!props.orden) return 'Paciente';
  if (props.orden.paciente) {
    return `${props.orden.paciente.nombres} ${props.orden.paciente.apellidos}`.trim();
  }
  return props.orden.contacto_nombre || 'Paciente';
});

// DNI
const documentoPaciente = computed(() => {
  return props.orden?.paciente?.documento || 'No informado';
});

// Mutual
const mutualNombre = computed(() => {
  if (!props.orden) return 'No especificada';
  if (props.orden.mutual_data?.display_name) {
    return props.orden.mutual_data.display_name;
  }
  if (props.orden.mutual_data?.nombre) {
    return `${props.orden.mutual} - ${props.orden.mutual_data.nombre}`;
  }
  return props.orden.mutual || 'No especificada';
});

// Teléfonos de contacto
const telefonoContacto = computed(() => {
  if (!props.orden) return '';
  return props.orden.contacto_celular || props.orden.contacto_telefono || props.orden.paciente?.telefono || '';
});

// Cálculos económicos
const copago = computed(() => Number(props.orden?.valor_copago || 0));
const noAutorizadosValor = computed(() => Number(props.orden?.valor_estudios_no_autorizados || 0));
const valorApb = computed(() => (props.orden?.abona_apb ? Number(props.orden?.valor_apb || 0) : 0));
const totalAbonar = computed(() => copago.value + noAutorizadosValor.value + valorApb.value);

const yaSeAtendio = computed(() => Boolean(props.orden?.ya_se_atendio));
const montoAbonado = computed(() => Number(props.orden?.monto_abonado_atencion || 0));
const reintegro = computed(() => {
  if (!yaSeAtendio.value) return 0;
  return montoAbonado.value - totalAbonar.value;
});

// Debe orden médica física
const debeOrdenFisica = computed(() => Boolean(props.orden?.debe_orden_medica));

// Prácticas autorizadas y no autorizadas
const autorizadas = computed(() => props.orden?.estudios_autorizados || []);
const noAutorizadas = computed(() => props.orden?.estudios_no_autorizados || []);

// Títulos de las indicaciones clínicas asignadas
const titulosIndicaciones = computed(() => {
  if (!props.orden?.indicaciones_ids || props.orden.indicaciones_ids.length === 0) {
    return [];
  }
  const catalogo = (props.catalogoIndicaciones && props.catalogoIndicaciones.length > 0)
    ? props.catalogoIndicaciones
    : catalogoInterno.value;

  return props.orden.indicaciones_ids.map((idOrCode) => {
    const found = catalogo.find((ind) => ind.id === idOrCode || ind.codigo === idOrCode);
    return found ? found.titulo : idOrCode;
  });
});

// Generación de Speech / Guion Modelo adaptado a la orden
const speechGenerado = computed(() => {
  if (!props.orden) return '';

  const saludo = `Hola, buenos días/tardes. ¿Hablo con ${nombrePaciente.value}?`;
  const intro = `Le hablo de Laboratorios Obarrio por su orden médica ${props.orden.nro_orden} de ${props.orden.mutual}.`;

  // Escenario 1: Ya se atendió previamente (Caso Reintegro / Saldo)
  if (yaSeAtendio.value) {
    if (reintegro.value > 0) {
      return `${saludo}
${intro}
Nos comunicamos para informarle que la auditoría de su orden médica ya ha finalizado exitosamente.
Como usted ya concurrió a realizarse los análisis y abonó un monto inicial de $${montoAbonado.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}, le informamos que tiene un REINTEGRO A SU FAVOR de $${reintegro.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}.
Por favor, acérquese con su DNI a nuestra sede para retirar su dinero cuando guste en nuestro horario habitual. ¿Tiene alguna duda?`;
    } else if (reintegro.value < 0) {
      const saldoPendiente = Math.abs(reintegro.value);
      return `${saludo}
${intro}
Nos comunicamos para informarle que la auditoría médica ha finalizado.
Al revisar la cobertura autorizada por su mutual, el costo total de los estudios quedó en $${totalAbonar.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}. Habiendo abonado previamente $${montoAbonado.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}, le queda una diferencia pendiente de $${saldoPendiente.toLocaleString('es-AR', { minimumFractionDigits: 2 })}.
Podrá cancelarla cuando pase a retirar sus resultados o en su próxima visita.`;
    } else {
      return `${saludo}
${intro}
Le informamos que la auditoría médica ha finalizado con total normalidad y su saldo quedó 100% saldado sin diferencias.`;
    }
  }

  // Escenario 2: No se atendió aún (Caso Normal de Atención)
  const lineas: string[] = [saludo, intro, 'Nos comunicamos para informarle que la auditoría de su orden médica ya se encuentra resuelta.'];

  // Estado de las prácticas
  if (noAutorizadas.value.length > 0 && autorizadas.value.length > 0) {
    lineas.push(
      `Su mutual autorizó las prácticas: ${autorizadas.value.join(', ')}. Quedaron como no autorizadas por la mutual: ${noAutorizadas.value.join(', ')}.`
    );
  } else if (noAutorizadas.value.length > 0) {
    lineas.push(`Las siguientes prácticas no tienen cobertura por mutual y quedan a su cargo: ${noAutorizadas.value.join(', ')}.`);
  } else if (autorizadas.value.length > 0) {
    lineas.push(`Todas sus prácticas fueron aprobadas por la mutual (${autorizadas.value.join(', ')}).`);
  }

  // Costos a abonar
  if (totalAbonar.value > 0) {
    lineas.push(
      `El total a abonar en recepción al momento de realizarse los estudios es de $${totalAbonar.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })} (Copago: $${copago.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}${noAutorizadosValor.value > 0 ? `, No autorizados: $${noAutorizadosValor.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}` : ''}${valorApb.value > 0 ? `, APB: $${valorApb.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}` : ''}).`
    );
  } else {
    lineas.push('Su orden médica cuenta con 100% de cobertura sin copago a abonar.');
  }

  // Alerta de receta física
  if (debeOrdenFisica.value) {
    lineas.push(
      '⚠️ Es fundamental e indispensable que recuerde traer la ORDEN MÉDICA FÍSICA ORIGINAL el día de la extracción, ya que fue ingresada digitalmente y la mutual nos exige el comprobante original.'
    );
  }

  // Indicaciones
  if (titulosIndicaciones.value.length > 0) {
    lineas.push(`Para su correcta preparación, recuerde cumplir con: ${titulosIndicaciones.value.join(', ')}.`);
  }

  lineas.push('¿Tiene alguna consulta sobre las indicaciones o el horario de extracción?');

  return lineas.join('\n\n');
});

// Speech alternativo en formato optimizado para WhatsApp / Mensaje de texto
const speechWhatsapp = computed(() => {
  if (!props.orden) return '';

  const saludo = `Hola *${nombrePaciente.value}*, te escribimos de *Laboratorios Obarrio*.`;
  const infoOrden = `Respecto a tu orden médica *${props.orden.nro_orden}* (${props.orden.mutual}):`;

  if (yaSeAtendio.value) {
    if (reintegro.value > 0) {
      return `${saludo} 👋

${infoOrden}
Te informamos que la auditoría médica ha *finalizado exitosamente*.

Como ya te realizaste los análisis y habías abonado *$${montoAbonado.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}*, tenés un *REINTEGRO A TU FAVOR de $${reintegro.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}* 💵.

Podés acercarte con tu DNI a nuestra sede para retirar tu dinero cuando gustes. ¡Muchas gracias!`;
    } else if (reintegro.value < 0) {
      const saldoPendiente = Math.abs(reintegro.value);
      return `${saludo} 👋

${infoOrden}
Te informamos que la auditoría médica ha finalizado. Al resolver la liquidación con tu mutual, el costo total fue de *$${totalAbonar.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}*. Habiendo abonado previamente *$${montoAbonado.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}*, resta una diferencia de *$${saldoPendiente.toLocaleString('es-AR', { minimumFractionDigits: 2 })}*.

Podrás abonarla al retirar tus resultados. ¡Muchas gracias!`;
    } else {
      return `${saludo} 👋

${infoOrden}
Te informamos que la auditoría médica ha *finalizado exitosamente* y tu trámite quedó 100% saldado sin diferencias pendientes.`;
    }
  }

  const bloques: string[] = [
    `${saludo} 👋`,
    `${infoOrden}\n¡Tu auditoría médica ya se encuentra *RESUELTA* y podés concurrir a realizarte los estudios!`,
  ];

  if (noAutorizadas.value.length > 0) {
    bloques.push(
      `⚠️ *Prácticas sin cobertura (particular):* ${noAutorizadas.value.join(', ')}`
    );
  }

  if (totalAbonar.value > 0) {
    bloques.push(`💰 *Total a abonar en recepción:* $${totalAbonar.value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}`);
  } else {
    bloques.push('✅ *Cobertura:* 100% autorizada (sin copago a abonar).');
  }

  if (debeOrdenFisica.value) {
    bloques.push('🚨 *ATENCIÓN:* Es indispensable que traigas la *ORDEN MÉDICA FÍSICA ORIGINAL* el día de la extracción.');
  }

  if (titulosIndicaciones.value.length > 0) {
    bloques.push(`📋 *Indicaciones de preparación:*\n• ${titulosIndicaciones.value.join('\n• ')}`);
  }

  bloques.push('Quedamos a tu disposición ante cualquier duda.');
  return bloques.join('\n\n');
});

const copiarSpeech = async (modo: 'telefono' | 'whatsapp' = 'telefono') => {
  const texto = modo === 'telefono' ? speechGenerado.value : speechWhatsapp.value;
  try {
    await navigator.clipboard.writeText(texto);
    if (modo === 'telefono') {
      copied.value = true;
      setTimeout(() => {
        copied.value = false;
      }, 2500);
    } else {
      copiedWhatsapp.value = true;
      setTimeout(() => {
        copiedWhatsapp.value = false;
      }, 2500);
    }
    toast.add({
      severity: 'success',
      summary: 'Texto Copiado',
      detail: modo === 'telefono' ? 'Guión telefónico copiado al portapapeles.' : 'Mensaje de WhatsApp copiado al portapapeles.',
      life: 3000,
    });
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error al copiar',
      detail: 'No se pudo copiar el texto automáticamente.',
      life: 3000,
    });
  }
};
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="Ayuda Memoria y Guía de Llamada al Paciente"
    :style="{ width: '850px', maxWidth: '95vw' }"
    :breakpoints="{ '960px': '90vw', '640px': '98vw' }"
    @update:visible="(val) => emit('update:visible', val)"
  >
    <div v-if="orden" class="space-y-4 text-xs">
      <!-- 1. Encabezado Paciente & Mutual -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-500 block">Paciente</span>
          <span class="text-sm font-extrabold text-slate-900 block flex items-center gap-1.5">
            <i class="pi pi-user text-blue-600"></i>
            {{ nombrePaciente }}
          </span>
          <span class="text-slate-500 text-[11px] block mt-0.5">DNI: <strong class="text-slate-800">{{ documentoPaciente }}</strong></span>
        </div>

        <div>
          <span class="text-[10px] uppercase font-bold text-slate-500 block">Mutual / Obra Social</span>
          <span class="text-xs font-bold text-slate-800 block flex items-center gap-1.5 mt-0.5">
            <i class="pi pi-shield text-indigo-600"></i>
            {{ mutualNombre }}
          </span>
          <span v-if="orden.nro_afiliado" class="text-slate-500 text-[11px] block mt-0.5">
            N° Afiliado: <strong class="text-slate-700">{{ orden.nro_afiliado }}</strong>
          </span>
        </div>

        <div>
          <span class="text-[10px] uppercase font-bold text-slate-500 block">Contacto Telefónico</span>
          <span class="text-xs font-bold text-emerald-700 block flex items-center gap-1.5 mt-0.5">
            <i class="pi pi-phone text-emerald-600"></i>
            {{ telefonoContacto || 'Sin teléfono cargado' }}
          </span>
          <span v-if="orden.contacto_horario" class="text-slate-500 text-[11px] block mt-0.5">
            Horario: {{ orden.contacto_horario }}
          </span>
        </div>
      </div>

      <!-- 2. Tarjetas de Alerta Críticas (Orden Física & Atención Previa / Reintegro) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Tarjeta Orden Física Adeudada -->
        <div
          class="p-3 rounded-xl border flex items-start gap-2.5 transition-colors"
          :class="debeOrdenFisica ? 'bg-red-50 border-red-300 text-red-950' : 'bg-emerald-50/60 border-emerald-200 text-emerald-950'"
        >
          <i
            class="pi text-base mt-0.5 shrink-0"
            :class="debeOrdenFisica ? 'pi-exclamation-triangle text-red-600 animate-pulse' : 'pi-check-circle text-emerald-600'"
          ></i>
          <div>
            <span class="font-bold uppercase text-[11px] block" :class="debeOrdenFisica ? 'text-red-900' : 'text-emerald-900'">
              {{ debeOrdenFisica ? '⚠️ Debe la Orden Médica Física' : '✓ No adeuda orden física' }}
            </span>
            <p class="text-[11px] mt-0.5 leading-snug" :class="debeOrdenFisica ? 'text-red-800' : 'text-emerald-800'">
              {{
                debeOrdenFisica
                  ? 'IMPORTANTE: Recordar al paciente que debe presentar la receta física original el día de la extracción.'
                  : 'La orden física ya fue entregada o no es adeudada.'
              }}
            </p>
          </div>
        </div>

        <!-- Tarjeta Atención Previa y Reintegro -->
        <div
          class="p-3 rounded-xl border flex items-start gap-2.5 transition-colors"
          :class="
            yaSeAtendio
              ? reintegro > 0
                ? 'bg-amber-50 border-amber-300 text-amber-950'
                : 'bg-orange-50 border-orange-300 text-orange-950'
              : 'bg-slate-50 border-slate-200 text-slate-800'
          "
        >
          <i
            class="pi text-base mt-0.5 shrink-0"
            :class="yaSeAtendio ? 'pi-wallet text-amber-600' : 'pi-calendar text-slate-500'"
          ></i>
          <div class="flex-1">
            <span class="font-bold uppercase text-[11px] block" :class="yaSeAtendio ? 'text-amber-900' : 'text-slate-700'">
              {{ yaSeAtendio ? '🩺 Paciente Ya Se Atendió (Hablar de Reintegro)' : 'Pendiente de Atención' }}
            </span>
            <div v-if="yaSeAtendio" class="text-[11px] mt-1 space-y-0.5">
              <div class="flex justify-between">
                <span>Abonó previamente:</span>
                <strong>${{ montoAbonado.toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</strong>
              </div>
              <div class="flex justify-between">
                <span>Costo real auditoría:</span>
                <strong>${{ totalAbonar.toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</strong>
              </div>
              <div
                class="pt-1 mt-1 border-t flex justify-between font-bold text-xs"
                :class="reintegro > 0 ? 'text-emerald-800' : (reintegro < 0 ? 'text-red-700' : 'text-slate-800')"
              >
                <span>{{ reintegro > 0 ? 'Reintegro a favor del paciente:' : (reintegro < 0 ? 'Saldo a cobrar:' : 'Saldo exacto:') }}</span>
                <span>${{ Math.abs(reintegro).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</span>
              </div>
            </div>
            <p v-else class="text-[11px] text-slate-500 mt-0.5">El paciente aún no concurrió a realizarse la toma de muestra.</p>
          </div>
        </div>
      </div>

      <!-- 3. Valores a Abonar & Prácticas Autorizadas / No Autorizadas -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Valores a Abonar -->
        <div class="p-3 bg-white rounded-xl border border-slate-200 shadow-xs space-y-2">
          <span class="text-[11px] font-bold uppercase text-slate-700 flex items-center gap-1.5">
            <i class="pi pi-dollar text-emerald-600"></i>
            Valores a Abonar
          </span>

          <div class="space-y-1 text-xs">
            <div class="flex justify-between py-0.5 border-b border-slate-100">
              <span class="text-slate-600">Copago / Bono Mutual:</span>
              <span class="font-semibold text-slate-800">${{ copago.toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</span>
            </div>
            <div class="flex justify-between py-0.5 border-b border-slate-100">
              <span class="text-slate-600">Estudios No Autorizados:</span>
              <span class="font-semibold" :class="noAutorizadosValor > 0 ? 'text-red-600' : 'text-slate-800'">
                ${{ noAutorizadosValor.toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
              </span>
            </div>
            <div v-if="orden.abona_apb" class="flex justify-between py-0.5 border-b border-slate-100">
              <span class="text-slate-600">Acto Bioquímico (APB):</span>
              <span class="font-semibold text-slate-800">${{ valorApb.toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</span>
            </div>
            <div class="flex justify-between pt-1.5 font-bold text-sm text-slate-900 bg-slate-50 px-2 py-1 rounded-lg">
              <span>TOTAL A ABONAR:</span>
              <span class="text-blue-700 font-mono">${{ totalAbonar.toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</span>
            </div>
          </div>
        </div>

        <!-- Prácticas Autorizadas y No Autorizadas -->
        <div class="p-3 bg-white rounded-xl border border-slate-200 shadow-xs space-y-2">
          <span class="text-[11px] font-bold uppercase text-slate-700 flex items-center gap-1.5">
            <i class="pi pi-list text-blue-600"></i>
            Estado de Prácticas
          </span>

          <div class="space-y-2">
            <!-- Autorizadas -->
            <div>
              <span class="text-[10px] font-bold text-emerald-800 uppercase block mb-1">
                ✓ Autorizadas ({{ autorizadas.length }})
              </span>
              <div v-if="autorizadas.length > 0" class="flex flex-wrap gap-1">
                <Tag
                  v-for="est in autorizadas"
                  :key="est"
                  :value="est"
                  severity="success"
                  class="text-[10px] font-semibold"
                />
              </div>
              <span v-else-if="noAutorizadas.length > 0" class="text-amber-800 font-semibold italic text-[11px]">
                Evaluar según no autorizadas
              </span>
              <span v-else class="text-slate-400 italic text-[11px]">Se autorizan las restantes prácticas de la prescripción.</span>
            </div>

            <!-- No Autorizadas -->
            <div>
              <span class="text-[10px] font-bold text-red-800 uppercase block mb-1">
                ✕ No Autorizadas / Particulares ({{ noAutorizadas.length }})
              </span>
              <div v-if="noAutorizadas.length > 0" class="flex flex-wrap gap-1">
                <Tag
                  v-for="est in noAutorizadas"
                  :key="est"
                  :value="est"
                  severity="danger"
                  class="text-[10px] font-semibold"
                />
              </div>
              <span v-else class="text-emerald-700 text-[11px] font-medium">Ninguna práctica rechazada (100% autorizada).</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Indicaciones Clínicas (Solo el título) -->
      <div class="p-3 bg-amber-50/50 rounded-xl border border-amber-200">
        <span class="text-[11px] font-bold uppercase text-amber-900 flex items-center gap-1.5 mb-1.5">
          <i class="pi pi-book text-amber-600"></i>
          Indicaciones Clínicas de Preparación (Solo Títulos)
        </span>
        <div v-if="titulosIndicaciones.length > 0" class="flex flex-wrap gap-1.5">
          <span
            v-for="titulo in titulosIndicaciones"
            :key="titulo"
            class="px-2 py-0.5 rounded-full bg-white text-amber-950 font-bold border border-amber-300 shadow-2xs text-[11px] flex items-center gap-1"
          >
            <i class="pi pi-check text-[9px] text-amber-600"></i>
            {{ titulo }}
          </span>
        </div>
        <p v-else class="text-slate-500 italic text-[11px]">
          Sin indicaciones clínicas específicas asignadas a la orden.
        </p>
      </div>

      <!-- 5. Speech Modelo para el Operador (Teléfono y WhatsApp) -->
      <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-300 shadow-2xs space-y-2.5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <!-- Selector de Pestaña Speech -->
          <div class="flex items-center space-x-1.5 bg-slate-200/80 p-0.5 rounded-lg w-fit">
            <button
              type="button"
              class="px-2.5 py-1 rounded-md text-xs font-bold transition flex items-center gap-1.5"
              :class="tabSpeech === 'telefono' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
              @click="tabSpeech = 'telefono'"
            >
              <i class="pi pi-phone text-[10px]"></i> Guión Telefónico
            </button>
            <button
              type="button"
              class="px-2.5 py-1 rounded-md text-xs font-bold transition flex items-center gap-1.5"
              :class="tabSpeech === 'whatsapp' ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
              @click="tabSpeech = 'whatsapp'"
            >
              <i class="pi pi-whatsapp text-[10px]"></i> Mensaje WhatsApp
            </button>
          </div>

          <Button
            :label="tabSpeech === 'telefono' ? (copied ? '¡Copiado!' : 'Copiar Guión') : (copiedWhatsapp ? '¡Copiado!' : 'Copiar WhatsApp')"
            :icon="(tabSpeech === 'telefono' ? copied : copiedWhatsapp) ? 'pi pi-check' : 'pi pi-copy'"
            :severity="(tabSpeech === 'telefono' ? copied : copiedWhatsapp) ? 'success' : 'secondary'"
            size="small"
            outlined
            class="text-xs py-1 px-3 self-end sm:self-auto"
            @click="copiarSpeech(tabSpeech)"
          />
        </div>

        <div
          v-if="tabSpeech === 'telefono'"
          class="bg-white p-3 rounded-lg border border-blue-200 text-slate-800 text-xs font-sans whitespace-pre-line leading-relaxed shadow-2xs select-all"
        >
          {{ speechGenerado }}
        </div>

        <div
          v-else
          class="bg-emerald-50/40 p-3 rounded-lg border border-emerald-200 text-slate-800 text-xs font-sans whitespace-pre-line leading-relaxed shadow-2xs select-all"
        >
          {{ speechWhatsapp }}
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        label="Cerrar"
        icon="pi pi-times"
        severity="secondary"
        text
        size="small"
        @click="emit('update:visible', false)"
      />
    </template>
  </Dialog>
</template>
