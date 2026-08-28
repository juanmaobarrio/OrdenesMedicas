<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { dashboardService } from '../../services/dashboard.service';
import { DashboardCharts, KpiMetrics } from '../../types/dashboard';
import Button from 'primevue/button';

import LoadingSpinner from '../../components/common/LoadingSpinner.vue';
import StatusTag from '../../components/common/StatusTag.vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();
const kpis = ref<KpiMetrics | null>(null);
const charts = ref<DashboardCharts | null>(null);
const isLoading = ref<boolean>(true);
const isExporting = ref<boolean>(false);

const loadDashboardData = async () => {
  isLoading.value = true;
  try {
    const [kpiRes, chartsRes] = await Promise.all([
      dashboardService.getKpis(),
      dashboardService.getCharts(),
    ]);
    kpis.value = kpiRes;
    charts.value = chartsRes;
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar las métricas del dashboard',
      life: 4000,
    });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadDashboardData();
});

const handleDownloadCsv = async () => {
  isExporting.value = true;
  try {
    const blob = await dashboardService.downloadCsv({});
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `reporte_ordenes_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.add({
      severity: 'success',
      summary: 'Reporte Exportado',
      detail: 'El archivo CSV se descargó correctamente.',
      life: 3000,
    });
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo generar el reporte CSV.',
      life: 4000,
    });
  } finally {
    isExporting.value = false;
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header with Action -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Panel de Control & Indicadores</h2>
        <p class="text-sm text-slate-500">Métricas consolidadas de órdenes médicas y auditorías en tiempo real</p>
      </div>
      <div class="flex items-center space-x-3">
        <Button
          icon="pi pi-refresh"
          severity="secondary"
          text
          rounded
          :loading="isLoading"
          @click="loadDashboardData"
          title="Actualizar datos"
        />
        <Button
          label="Exportar a Excel (CSV)"
          icon="pi pi-file-excel"
          severity="info"
          :loading="isExporting"
          @click="handleDownloadCsv"
        />

      </div>
    </div>

    <LoadingSpinner v-if="isLoading" message="Calculando indicadores del sistema..." />

    <template v-else-if="kpis">
      <!-- KPI Stats Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Total Órdenes -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-slate-400 uppercase">Total Órdenes</p>
            <p class="text-2xl font-bold text-slate-800 mt-1">{{ kpis.total_ordenes }}</p>
            <p class="text-xs text-blue-600 font-medium mt-1">{{ kpis.ordenes_activas }} en proceso activo</p>

          </div>
          <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <i class="pi pi-file text-xl"></i>
          </div>
        </div>

        <!-- En Auditoría -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-slate-400 uppercase">En Auditoría</p>
            <p class="text-2xl font-bold text-amber-600 mt-1">{{ kpis.ordenes_en_auditoria }}</p>
            <p class="text-xs text-slate-500 mt-1">{{ kpis.ordenes_con_solicitudes }} con observaciones</p>
          </div>
          <div class="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <i class="pi pi-search text-xl"></i>
          </div>
        </div>

        <!-- Tasa de Aprobación -->
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-slate-400 uppercase">Tasa de Aprobación</p>
            <p class="text-2xl font-bold text-emerald-600 mt-1">{{ kpis.tasa_aprobacion_porcentaje }}%</p>
            <p class="text-xs text-slate-500 mt-1">{{ kpis.ordenes_cerradas }} cerradas exitosas</p>
          </div>
          <div class="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <i class="pi pi-check-circle text-xl"></i>
          </div>
        </div>


        <!-- Llamadas Pendientes (Alerta) -->
        <router-link
          to="/llamadas-pendientes"
          class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between hover:border-red-300 transition group cursor-pointer"
        >
          <div>
            <p class="text-xs font-semibold text-slate-400 uppercase group-hover:text-red-500 transition">
              Llamadas Pendientes
            </p>
            <p class="text-2xl font-bold text-red-600 mt-1">{{ kpis.llamadas_pendientes_total }}</p>
            <p class="text-xs text-red-500 font-medium mt-1">
              {{ kpis.llamadas_pendientes_solicitud }} obs. / {{ kpis.llamadas_pendientes_finalizada }} finalizadas
            </p>
          </div>
          <div class="w-12 h-12 rounded-xl bg-red-50 text-red-600 flex items-center justify-center group-hover:scale-110 transition">
            <i class="pi pi-phone text-xl"></i>
          </div>
        </router-link>
      </div>

      <!-- Charts & Breakdown Section -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Distribución por Estados -->
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 class="text-base font-bold text-slate-800 mb-4 flex items-center justify-between">
            <span>Distribución de Estados</span>
            <i class="pi pi-chart-pie text-slate-400"></i>
          </h3>
          <div class="space-y-3">
            <div
              v-for="item in charts?.estados"
              :key="item.estado"
              class="flex items-center justify-between text-sm py-1.5 border-b border-slate-100 last:border-0"
            >
              <div class="flex items-center space-x-2">
                <StatusTag :value="item.estado" />
              </div>
              <div class="flex items-center space-x-3">
                <span class="font-semibold text-slate-700">{{ item.cantidad }}</span>
                <span class="text-xs text-slate-400 w-12 text-right">({{ item.porcentaje }}%)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Distribución por Sucursales -->
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 class="text-base font-bold text-slate-800 mb-4 flex items-center justify-between">
            <span>Órdenes por Sucursal</span>
            <i class="pi pi-building text-slate-400"></i>
          </h3>
          <div class="space-y-4">
            <div
              v-for="suc in charts?.sucursales"
              :key="suc.sucursal_nombre"
              class="space-y-1.5"
            >
              <div class="flex justify-between text-xs font-semibold">
                <span class="text-slate-700">{{ suc.sucursal_nombre }}</span>
                <span class="text-slate-500">{{ suc.total_ordenes }} total</span>
              </div>
              <div class="w-full bg-slate-100 rounded-full h-2.5 flex overflow-hidden">
                <div
                  class="bg-amber-500 h-2.5"
                  :style="{ width: `${suc.total_ordenes ? (suc.ordenes_abiertas / suc.total_ordenes) * 100 : 0}%` }"
                  title="Abiertas"
                ></div>
                <div
                  class="bg-blue-600 h-2.5"
                  :style="{ width: `${suc.total_ordenes ? (suc.ordenes_cerradas / suc.total_ordenes) * 100 : 0}%` }"
                  title="Cerradas"
                ></div>

              </div>
              <div class="flex justify-between text-[11px] text-slate-400">
                <span>{{ suc.ordenes_abiertas }} abiertas</span>
                <span>{{ suc.ordenes_cerradas }} cerradas</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Mutuales -->
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 class="text-base font-bold text-slate-800 mb-4 flex items-center justify-between">
            <span>Top Coberturas / Mutuales</span>
            <i class="pi pi-id-card text-slate-400"></i>
          </h3>
          <div class="space-y-3">
            <div
              v-for="(mut, idx) in charts?.mutuales_top"
              :key="mut.mutual"
              class="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100"
            >
              <div class="flex items-center space-x-3">
                <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center">
                  {{ idx + 1 }}
                </span>

                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ mut.mutual }}</p>
                  <p class="text-xs text-slate-500">{{ mut.cantidad_ordenes }} órdenes ingresadas</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-xs font-bold text-slate-700">${{ mut.total_copago }}</p>
                <p class="text-[10px] text-slate-400">en copagos</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
