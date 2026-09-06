<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { dashboardService } from '../../services/dashboard.service';
import { usersService } from '../../services/users.service';
import { mutualesService } from '../../services/mutuales.service';
import {
  ReporteConfigurableRequest,
  ReporteConfigurableResponse,
} from '../../types/dashboard';
import { ObraSocial, Sucursal } from '../../types';

import Button from 'primevue/button';
import Dropdown from 'primevue/dropdown';
import MultiSelect from 'primevue/multiselect';
import Calendar from 'primevue/calendar';
import Checkbox from 'primevue/checkbox';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Chart from 'primevue/chart';
import Tag from 'primevue/tag';
import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const sucursales = ref<Sucursal[]>([]);
const mutuales = ref<ObraSocial[]>([]);
const isLoading = ref(false);
const isExporting = ref(false);
const reporte = ref<ReporteConfigurableResponse | null>(null);
const showFiltrosAvanzados = ref(false);

// Fechas por defecto: últimos 90 días
const hoy = new Date();
const fechaInicioDefault = new Date();
fechaInicioDefault.setDate(hoy.getDate() - 90);

const presetSeleccionado = ref<string>('ordenes_tiempo');

const formFiltros = ref({
  preset: 'ordenes_tiempo',
  dimension_primaria: 'mutual',
  dimension_secundaria: 'tiempo' as string | null,
  agrupacion_tiempo: 'mes',
  fecha_desde: fechaInicioDefault as Date | null,
  fecha_hasta: hoy as Date | null,
  mutuales: [] as string[],
  sucursal_id: null as string | null,
  estado: null as string | null,
  solo_con_reintegro: false,
});

const opcionesDimensiones = [
  { label: 'Obra Social / Mutual', value: 'mutual' },
  { label: 'Unidad de Tiempo', value: 'tiempo' },
  { label: 'Motivo de Cancelación', value: 'motivo_cancelacion' },
  { label: 'Sucursal / Sede', value: 'sucursal' },
  { label: 'Estado del Ciclo de Vida', value: 'estado' },
];

const opcionesDimensionSecundaria = [
  { label: 'Ninguna (Sin cruce)', value: null },
  { label: 'Unidad de Tiempo', value: 'tiempo' },
  { label: 'Obra Social / Mutual', value: 'mutual' },
  { label: 'Estado de Orden', value: 'estado' },
  { label: 'Sucursal / Sede', value: 'sucursal' },
];

const opcionesTiempo = [
  { label: 'Por Mes', value: 'mes' },
  { label: 'Por Semana', value: 'semana' },
  { label: 'Por Día', value: 'dia' },
  { label: 'Por Año', value: 'anio' },
];

const opcionesEstados = [
  { label: 'Ingreso', value: 'Ingreso' },
  { label: 'En Auditoría', value: 'en Auditoria' },
  { label: 'Solicitudes de Auditoría', value: 'Solicitudes de auditoria' },
  { label: 'Actualizada', value: 'Actualizada' },
  { label: 'Auditoría Finalizada', value: 'Auditoria Finalizada' },
  { label: 'Cancelada', value: 'Cancelada' },
  { label: 'Dar de baja', value: 'Dar de baja' },
  { label: 'Cerrada', value: 'Cerrada' },
];

const presets = [
  {
    id: 'ordenes_tiempo',
    label: 'Órdenes vs. Tiempo',
    icon: 'pi pi-calendar',
    dimPrimaria: 'mutual',
    dimSecundaria: 'tiempo',
    agrupTiempo: 'mes',
    estado: null,
    soloReintegro: false,
  },
  {
    id: 'motivos_cancelacion',
    label: 'Motivos de Cancelación',
    icon: 'pi pi-ban',
    dimPrimaria: 'motivo_cancelacion',
    dimSecundaria: 'mutual',
    agrupTiempo: 'mes',
    estado: 'Cancelada',
    soloReintegro: false,
  },
  {
    id: 'tasa_rechazo',
    label: 'Tasa de Rechazo de Estudios',
    icon: 'pi pi-percentage',
    dimPrimaria: 'mutual',
    dimSecundaria: null,
    agrupTiempo: 'mes',
    estado: null,
    soloReintegro: false,
  },
  {
    id: 'financiero_reintegros',
    label: 'Liquidación & Reintegros',
    icon: 'pi pi-wallet',
    dimPrimaria: 'mutual',
    dimSecundaria: null,
    agrupTiempo: 'mes',
    estado: null,
    soloReintegro: false,
  },
  {
    id: 'personalizado',
    label: 'Personalizado',
    icon: 'pi pi-sliders-h',
    dimPrimaria: 'mutual',
    dimSecundaria: null,
    agrupTiempo: 'mes',
    estado: null,
    soloReintegro: false,
  },
];

const aplicarPreset = (pId: string) => {
  presetSeleccionado.value = pId;
  formFiltros.value.preset = pId;

  const target = presets.find((p) => p.id === pId);
  if (target && pId !== 'personalizado') {
    formFiltros.value.dimension_primaria = target.dimPrimaria;
    formFiltros.value.dimension_secundaria = target.dimSecundaria;
    formFiltros.value.agrupacion_tiempo = target.agrupTiempo;
    if (target.estado) {
      formFiltros.value.estado = target.estado;
    } else if (pId === 'ordenes_tiempo' || pId === 'tasa_rechazo' || pId === 'financiero_reintegros') {
      formFiltros.value.estado = null;
    }
    formFiltros.value.solo_con_reintegro = target.soloReintegro;
    ejecutarReporte();
  } else if (pId === 'personalizado') {
    showFiltrosAvanzados.value = true;
  }
};

const ejecutarReporte = async () => {
  isLoading.value = true;
  try {
    const formattedDate = (d: Date | null) => (d ? d.toISOString().slice(0, 10) : null);
    const payload: ReporteConfigurableRequest = {
      preset: formFiltros.value.preset,
      dimension_primaria: formFiltros.value.dimension_primaria,
      dimension_secundaria: formFiltros.value.dimension_secundaria,
      agrupacion_tiempo: formFiltros.value.agrupacion_tiempo,
      fecha_desde: formattedDate(formFiltros.value.fecha_desde),
      fecha_hasta: formattedDate(formFiltros.value.fecha_hasta),
      mutuales: formFiltros.value.mutuales && formFiltros.value.mutuales.length > 0 ? formFiltros.value.mutuales : null,
      sucursal_id: formFiltros.value.sucursal_id || null,
      estado: formFiltros.value.estado || null,
      solo_con_reintegro: formFiltros.value.solo_con_reintegro,
    };

    const res = await dashboardService.ejecutarReporte(payload);
    reporte.value = res;
  } catch (err: any) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'No se pudo generar el reporte estadístico',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  try {
    const [sucRes, mutRes] = await Promise.all([
      usersService.listSucursales(),
      mutualesService.list(true),
    ]);
    sucursales.value = sucRes;
    mutuales.value = mutRes;
  } catch (err) {
    console.warn('Error cargando catálogos de filtros:', err);
  }
  await ejecutarReporte();
});

const chartData = computed(() => {
  if (!reporte.value) return { labels: [], datasets: [] };
  return {
    labels: reporte.value.grafico_labels,
    datasets: reporte.value.grafico_datasets,
  };
});

const chartOptions = computed(() => {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: { size: 11, family: 'Inter, system-ui, sans-serif' },
        },
      },
    },
    scales: {
      x: {
        ticks: { font: { size: 10 } },
        grid: { color: 'rgba(226, 232, 240, 0.5)' },
      },
      y: {
        ticks: { font: { size: 10 } },
        grid: { color: 'rgba(226, 232, 240, 0.5)' },
      },
    },
  };
});

const imprimirReportePdf = () => {
  window.print();
};

const exportarCsv = () => {
  if (!reporte.value || reporte.value.filas.length === 0) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'No hay datos para exportar', life: 3000 });
    return;
  }

  isExporting.value = true;
  try {
    const encabezados = [
      'Clave Primaria',
      'Etiqueta Primaria',
      'Clave Secundaria',
      'Etiqueta Secundaria',
      'Total Órdenes',
      'Aprobadas',
      'Canceladas',
      'En Proceso',
      'Total Estudios',
      'Estudios Autorizados',
      'Estudios Rechazados',
      '% Rechazo Estudios',
      'Copago ($)',
      'No Autorizados ($)',
      'APB ($)',
      'Total Facturado Auditoría ($)',
      'Total Abonado Atención ($)',
      'Reintegros a Favor ($)',
      'Pacientes con Reintegro',
    ];

    const filasCsv = reporte.value.filas.map((f) => [
      `"${f.clave_primaria}"`,
      `"${f.etiqueta_primaria}"`,
      `"${f.clave_secundaria || ''}"`,
      `"${f.etiqueta_secundaria || ''}"`,
      f.total_ordenes,
      f.ordenes_aprobadas,
      f.ordenes_canceladas,
      f.ordenes_en_proceso,
      f.total_estudios_evaluados,
      f.total_estudios_autorizados,
      f.total_estudios_rechazados,
      `${f.porcentaje_rechazo_estudios}%`,
      f.total_copago,
      f.total_no_autorizados,
      f.total_apb,
      f.total_facturado_auditoria,
      f.total_abonado_atencion,
      f.total_reintegros_a_favor,
      f.cant_pacientes_reintegro,
    ]);

    const contenido = '\ufeff' + [encabezados.join(';'), ...filasCsv.map((r) => r.join(';'))].join('\n');
    const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `reporte_${reporte.value.titulo_reporte.toLowerCase().replace(/\\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.add({ severity: 'success', summary: 'Exportado', detail: 'Reporte CSV descargado con éxito', life: 3000 });
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Error al generar CSV', life: 3000 });
  } finally {
    isExporting.value = false;
  }
};
</script>

<template>
  <div class="reportes-view space-y-6">
    <!-- Membrete Exclusivo para Impresión / PDF -->
    <div class="only-print p-4 mb-4 border-b-2 border-slate-800 flex items-start justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">LABORATORIO DE ANÁLISIS CLÍNICOS</h1>
        <p class="text-sm font-semibold text-slate-700 uppercase mt-0.5">{{ reporte?.titulo_reporte || 'INFORME ESTADÍSTICO DE GESTIÓN' }}</p>
        <p class="text-xs text-slate-500">{{ reporte?.subtitulo }}</p>
      </div>
      <div class="text-right text-xs text-slate-600 space-y-0.5">
        <p><span class="font-bold">Período:</span> {{ reporte?.periodo_desde || 'Inicio' }} al {{ reporte?.periodo_hasta || 'Actualidad' }}</p>
        <p><span class="font-bold">Emisión:</span> {{ reporte?.fecha_generacion }}</p>
        <p><span class="font-bold">Generado por:</span> {{ reporte?.generado_por }}</p>
      </div>
    </div>

    <!-- Header en Pantalla -->
    <div class="no-print flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <i class="pi pi-chart-bar text-indigo-600"></i>
          <span>Reportes Estadísticos & Generador Personalizado</span>
        </h2>
        <p class="text-xs text-slate-500">
          Análisis multidimensional de órdenes, obras sociales, motivos de cancelación, tasas de rechazo y liquidaciones
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <Button
          label="Imprimir / PDF"
          icon="pi pi-print"
          severity="secondary"
          size="small"
          class="text-xs"
          @click="imprimirReportePdf"
        />
        <Button
          label="Exportar CSV"
          icon="pi pi-file-excel"
          severity="success"
          size="small"
          class="text-xs"
          :loading="isExporting"
          @click="exportarCsv"
        />
        <Button
          :label="showFiltrosAvanzados ? 'Ocultar Filtros' : 'Filtros Avanzados'"
          :icon="showFiltrosAvanzados ? 'pi pi-chevron-up' : 'pi pi-filter'"
          severity="primary"
          outlined
          size="small"
          class="text-xs"
          @click="showFiltrosAvanzados = !showFiltrosAvanzados"
        />
      </div>
    </div>

    <!-- Barra de Presets Rápidos -->
    <div class="no-print bg-white p-3 rounded-xl border border-slate-200 shadow-xs flex items-center gap-2 overflow-x-auto">
      <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mr-1 shrink-0">
        <i class="pi pi-bolt text-amber-500 mr-1"></i>Reportes Rápidos:
      </span>
      <button
        v-for="p in presets"
        :key="p.id"
        type="button"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition shrink-0"
        :class="
          presetSeleccionado === p.id
            ? 'bg-indigo-50 border-indigo-500 text-indigo-900 shadow-xs'
            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
        "
        @click="aplicarPreset(p.id)"
      >
        <i :class="p.icon" class="text-xs"></i>
        <span>{{ p.label }}</span>
      </button>
    </div>

    <!-- Panel de Filtros Configurables -->
    <div
      v-if="showFiltrosAvanzados"
      class="no-print bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4 animate-fadeIn"
    >
      <div class="flex items-center justify-between border-b border-slate-100 pb-2">
        <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
          <i class="pi pi-sliders-h text-indigo-600"></i>
          <span>Variables de Configuración del Reporte</span>
        </h4>
        <span class="text-xs text-slate-400">Personalice los ejes de agrupación y el rango temporal</span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Eje Primario (Agrupar por)</label>
          <Dropdown
            v-model="formFiltros.dimension_primaria"
            :options="opcionesDimensiones"
            optionLabel="label"
            optionValue="value"
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Eje Secundario (Cruce)</label>
          <Dropdown
            v-model="formFiltros.dimension_secundaria"
            :options="opcionesDimensionSecundaria"
            optionLabel="label"
            optionValue="value"
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Unidad de Tiempo</label>
          <Dropdown
            v-model="formFiltros.agrupacion_tiempo"
            :options="opcionesTiempo"
            optionLabel="label"
            optionValue="value"
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Estado de Orden</label>
          <Dropdown
            v-model="formFiltros.estado"
            :options="opcionesEstados"
            optionLabel="label"
            optionValue="value"
            placeholder="Todos los estados"
            showClear
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Fecha Desde</label>
          <Calendar v-model="formFiltros.fecha_desde" dateFormat="dd/mm/yy" class="w-full text-xs" showIcon />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Fecha Hasta</label>
          <Calendar v-model="formFiltros.fecha_hasta" dateFormat="dd/mm/yy" class="w-full text-xs" showIcon />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Sucursal / Sede</label>
          <Dropdown
            v-model="formFiltros.sucursal_id"
            :options="sucursales"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Todas las sucursales"
            showClear
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block font-bold text-slate-700 uppercase mb-1">Obras Sociales Específicas</label>
          <MultiSelect
            v-model="formFiltros.mutuales"
            :options="mutuales"
            optionLabel="sigla"
            optionValue="sigla"
            placeholder="Todas las mutuales"
            display="chip"
            class="w-full text-xs"
          />
        </div>

        <div class="sm:col-span-2 lg:col-span-4 flex items-center justify-between pt-2 border-t border-slate-100">
          <div class="flex items-center space-x-2">
            <Checkbox v-model="formFiltros.solo_con_reintegro" binary inputId="checkSoloReintegro" />
            <label for="checkSoloReintegro" class="text-xs font-semibold text-slate-700 cursor-pointer">
              Filtrar solo órdenes donde el paciente ya se atendió previamente (Cálculo de Reintegro)
            </label>
          </div>
          <Button
            label="Generar Reporte"
            icon="pi pi-check"
            severity="primary"
            size="small"
            class="text-xs font-bold px-4"
            :loading="isLoading"
            @click="ejecutarReporte"
          />
        </div>
      </div>
    </div>

    <!-- Placeholder de carga -->
    <LoadingSpinner v-if="isLoading && !reporte" message="Calculando agregaciones estadísticas..." />

    <!-- Contenido del Reporte -->
    <div v-else-if="reporte" class="space-y-6">
      <!-- Resumen Ejecutivo de Métricas (Tarjetas KPI) -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span class="text-[10px] font-bold text-slate-400 uppercase">Órdenes Evaluadas</span>
          <p class="text-2xl font-extrabold text-slate-800 mt-0.5">{{ reporte.resumen_global.total_ordenes }}</p>
          <span class="text-[10px] text-slate-500">en el período seleccionado</span>
        </div>

        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span class="text-[10px] font-bold text-red-600 uppercase">Tasa Rechazo de Estudios</span>
          <p class="text-2xl font-extrabold text-red-700 mt-0.5">{{ reporte.resumen_global.promedio_tasa_rechazo }}%</p>
          <span class="text-[10px] text-slate-500">{{ reporte.resumen_global.total_estudios_rechazados }} de {{ reporte.resumen_global.total_estudios_evaluados }} prácticas</span>
        </div>

        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span class="text-[10px] font-bold text-blue-600 uppercase">Total Copagos Obra Social</span>
          <p class="text-2xl font-extrabold text-blue-900 mt-0.5">${{ Number(reporte.resumen_global.total_copago || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</p>
          <span class="text-[10px] text-slate-500">+ ${{ Number(reporte.resumen_global.total_no_autorizados || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }} particulares</span>
        </div>

        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span class="text-[10px] font-bold text-emerald-600 uppercase">Reintegros a Favor del Paciente</span>
          <p class="text-2xl font-extrabold text-emerald-800 mt-0.5">${{ Number(reporte.resumen_global.total_reintegros || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}</p>
          <span class="text-[10px] text-slate-500">a devolver a pacientes atendidos</span>
        </div>
      </div>

      <!-- Gráfico Estadístico Interactivo -->
      <div v-if="chartData.labels && chartData.labels.length > 0" class="no-print bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
          <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
            <i class="pi pi-chart-line text-indigo-600"></i>
            <span>Visualización Gráfica Comparativa</span>
          </h4>
          <span class="text-xs text-slate-400">Principales 15 grupos representados</span>
        </div>
        <div class="h-64 sm:h-72">
          <Chart type="bar" :data="chartData" :options="chartOptions" class="h-full w-full" />
        </div>
      </div>

      <!-- Tabla de Datos Detallada -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="no-print p-4 bg-slate-50 border-b border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div>
            <h4 class="text-sm font-bold text-slate-800">{{ reporte.titulo_reporte }}</h4>
            <p class="text-xs text-slate-500">{{ reporte.subtitulo }} ({{ reporte.filas.length }} grupos consolidados)</p>
          </div>
          <span class="text-xs font-mono text-slate-400">Moneda: ARS ($)</span>
        </div>

        <DataTable
          :value="reporte.filas"
          stripedRows
          responsiveLayout="scroll"
          class="p-datatable-sm text-xs"
          rowHover
        >
          <!-- Eje Primario -->
          <Column field="etiqueta_primaria" header="Agrupación Principal" sortable>
            <template #body="{ data }">
              <span class="font-bold text-slate-800 text-xs">{{ data.etiqueta_primaria }}</span>
            </template>
          </Column>

          <!-- Eje Secundario si existe -->
          <Column v-if="formFiltros.dimension_secundaria" field="etiqueta_secundaria" header="Cruce Secundario" sortable>
            <template #body="{ data }">
              <span class="font-medium text-slate-600 text-xs">{{ data.etiqueta_secundaria || '-' }}</span>
            </template>
          </Column>

          <!-- Volumen de Órdenes -->
          <Column field="total_ordenes" header="Total Órdenes" sortable style="width: 110px">
            <template #body="{ data }">
              <span class="font-bold font-mono text-xs text-slate-900">{{ data.total_ordenes }}</span>
            </template>
          </Column>

          <Column field="ordenes_aprobadas" header="Aprobadas" sortable style="width: 100px">
            <template #body="{ data }">
              <span class="font-semibold text-emerald-700 text-xs">{{ data.ordenes_aprobadas }}</span>
            </template>
          </Column>

          <Column field="ordenes_canceladas" header="Canceladas" sortable style="width: 100px">
            <template #body="{ data }">
              <span class="font-semibold text-red-700 text-xs">{{ data.ordenes_canceladas }}</span>
            </template>
          </Column>

          <!-- Tasa de Rechazo de Estudios -->
          <Column field="porcentaje_rechazo_estudios" header="Rechazo Estudios" sortable style="width: 140px">
            <template #body="{ data }">
              <div class="flex items-center space-x-1.5">
                <Tag
                  :value="`${data.porcentaje_rechazo_estudios}%`"
                  :severity="data.porcentaje_rechazo_estudios > 25 ? 'danger' : (data.porcentaje_rechazo_estudios > 10 ? 'warn' : 'success')"
                  class="text-[10px] font-bold"
                />
                <span class="text-[10px] text-slate-400">
                  ({{ data.total_estudios_rechazados }}/{{ data.total_estudios_evaluados }})
                </span>
              </div>
            </template>
          </Column>

          <!-- Copago Obra Social -->
          <Column field="total_copago" header="Copagos ($)" sortable style="width: 120px">
            <template #body="{ data }">
              <span class="font-mono text-xs text-blue-900 font-semibold">
                ${{ Number(data.total_copago).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
              </span>
            </template>
          </Column>

          <!-- No Autorizados -->
          <Column field="total_no_autorizados" header="Particulares ($)" sortable style="width: 120px">
            <template #body="{ data }">
              <span class="font-mono text-xs text-amber-900 font-semibold">
                ${{ Number(data.total_no_autorizados).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
              </span>
            </template>
          </Column>

          <!-- Facturado Auditoría Total -->
          <Column field="total_facturado_auditoria" header="Total Auditoría ($)" sortable style="width: 130px">
            <template #body="{ data }">
              <span class="font-mono text-xs text-slate-900 font-bold">
                ${{ Number(data.total_facturado_auditoria).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
              </span>
            </template>
          </Column>

          <!-- Reintegros si corresponde -->
          <Column field="total_reintegros_a_favor" header="Reintegros Paciente ($)" sortable style="width: 140px">
            <template #body="{ data }">
              <span
                class="font-mono text-xs font-bold"
                :class="Number(data.total_reintegros_a_favor) > 0 ? 'text-emerald-700' : 'text-slate-400'"
              >
                ${{ Number(data.total_reintegros_a_favor).toLocaleString('es-AR', { minimumFractionDigits: 2 }) }}
              </span>
              <span v-if="data.cant_pacientes_reintegro > 0" class="block text-[10px] text-emerald-800">
                ({{ data.cant_pacientes_reintegro }} pac.)
              </span>
            </template>
          </Column>
        </DataTable>
      </div>

      <!-- Pie de Firma Exclusivo para Impresión -->
      <div class="only-print mt-12 pt-8 flex items-center justify-between text-xs text-slate-700">
        <div class="text-center w-56 border-t border-slate-400 pt-2">
          <p class="font-bold">Firma Dirección Médica</p>
          <p class="text-[10px] text-slate-500">Laboratorio de Análisis Clínicos</p>
        </div>
        <div class="text-center w-56 border-t border-slate-400 pt-2">
          <p class="font-bold">Responsable de Auditoría</p>
          <p class="text-[10px] text-slate-500">Revisión y Control de Gestión</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.only-print {
  display: none;
}

@media print {
  .no-print {
    display: none !important;
  }

  .only-print {
    display: block !important;
  }

  .reportes-view {
    background: white !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  :deep(.p-datatable) {
    font-size: 10px !important;
  }

  :deep(.p-datatable-thead > tr > th) {
    background: #f1f5f9 !important;
    color: #0f172a !important;
    padding: 4px 6px !important;
    border: 1px solid #cbd5e1 !important;
  }

  :deep(.p-datatable-tbody > tr > td) {
    padding: 4px 6px !important;
    border: 1px solid #e2e8f0 !important;
  }
}
</style>
