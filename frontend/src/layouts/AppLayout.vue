<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth.store';
import { useOrdenesStore } from '../stores/ordenes.store';
import Button from 'primevue/button';
import Badge from 'primevue/badge';
import Toast from 'primevue/toast';
import ConfirmDialog from 'primevue/confirmdialog';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const ordenesStore = useOrdenesStore();

const isSidebarOpen = ref(false);


onMounted(async () => {
  // Cargar llamadas pendientes para el badge
  ordenesStore.fetchLlamadasPendientes();
});

const pendingCallsCount = computed(() => ordenesStore.llamadasPendientes.length);

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

const navigationItems = computed(() => {
  const items = [
    { label: 'Dashboard', icon: 'pi pi-chart-bar', to: '/dashboard' },
    { label: 'Órdenes Médicas', icon: 'pi pi-file', to: '/ordenes' },
    { label: 'Nueva Orden', icon: 'pi pi-plus-circle', to: '/ordenes/nueva' },
    {
      label: 'Llamadas a Pacientes',
      icon: 'pi pi-phone',
      to: '/llamadas-pendientes',
      badge: pendingCallsCount.value > 0 ? pendingCallsCount.value : undefined,
      badgeSeverity: 'danger',
    },
    { label: 'Padrón de Pacientes', icon: 'pi pi-users', to: '/pacientes' },
    { label: 'Usuarios y Roles', icon: 'pi pi-user-edit', to: '/usuarios' },
    { label: 'Manual de Usuario', icon: 'pi pi-book', to: '/manual_usuario' },
  ];

  if (authStore.isAdmin) {
    items.push(
      { label: 'Obras Sociales', icon: 'pi pi-id-card', to: '/obras-sociales' },
      { label: 'Sucursales', icon: 'pi pi-building', to: '/sucursales' },
      { label: 'Configuración', icon: 'pi pi-cog', to: '/configuracion' }
    );
  }

  return items;
});

const isCurrentRoute = (path: string) => {
  if (path === '/ordenes') {
    return route.path === '/ordenes';
  }
  return route.path.startsWith(path);
};

const pageTitle = computed(() => {
  switch (route.name) {
    case 'Dashboard':
      return 'Panel de Control & Indicadores';
    case 'OrdenesList':
      return 'Gestión de Órdenes Médicas';
    case 'OrdenCreate':
      return 'Registro de Nueva Orden Médica';
    case 'OrdenDetail':
      return 'Expediente Clínico';
    case 'LlamadasPendientes':
      return 'Bandeja de Llamadas a Pacientes';
    case 'PacientesList':
      return 'Padrón de Pacientes';
    case 'ObrasSocialesList':
      return 'Obras Sociales y Mutuales';
    case 'UsersList':
      return 'Gestión de Usuarios y Roles';
    case 'SucursalesList':
      return 'Sedes y Sucursales';
    case 'Configuracion':
      return 'Configuración del Sistema';
    case 'ManualUsuario':
      return 'Manual de Uso del Sistema';
    default:
      return '';
  }
});
</script>

<template>
  <div class="h-screen w-screen overflow-hidden flex bg-slate-100">
    <Toast position="top-right" />
    <ConfirmDialog />

    <!-- Sidebar -->
    <aside
      class="h-screen flex flex-col justify-between bg-slate-900 text-slate-100 transition-all duration-300 z-30 shadow-xl flex-shrink-0"
      :class="isSidebarOpen ? 'w-64' : 'w-20'"
    >
      <!-- Logo / Header -->
      <div class="h-16 flex-shrink-0 flex items-center justify-between px-4 border-b border-slate-800">
        <div v-if="isSidebarOpen" class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow">
            OM
          </div>
          <span class="font-bold text-sm tracking-wide text-white uppercase">Órdenes Médicas</span>
        </div>
        <div v-else class="mx-auto w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white">
          OM
        </div>

        <button
          @click="isSidebarOpen = !isSidebarOpen"
          class="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition"
        >
          <i :class="isSidebarOpen ? 'pi pi-angle-left' : 'pi pi-angle-right'"></i>
        </button>
      </div>

      <!-- Navigation Links -->
      <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <router-link
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition group"
          :class="[
            isCurrentRoute(item.to)
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-300 hover:bg-slate-800 hover:text-white'
          ]"

        >
          <i :class="item.icon" class="text-lg mr-3 flex-shrink-0"></i>
          <span v-if="isSidebarOpen" class="flex-1 truncate">{{ item.label }}</span>
          <Badge
            v-if="isSidebarOpen && item.badge"
            :value="item.badge"
            :severity="(item.badgeSeverity as any) || 'info'"
            class="ml-auto"
          />
        </router-link>
      </nav>

      <!-- Sucursal & User Card -->
      <div class="flex-shrink-0 p-3 border-t border-slate-800 bg-slate-950/70">
        <div v-if="isSidebarOpen" class="flex items-center space-x-3 mb-2">
          <div class="w-9 h-9 rounded-full bg-slate-700 flex items-center justify-center text-slate-300 font-semibold text-xs border border-slate-600">
            {{ authStore.user?.username.slice(0, 2).toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-semibold text-white truncate">{{ authStore.user?.full_name }}</p>
            <p class="text-[11px] text-blue-400 truncate">{{ authStore.user?.role_name }}</p>

            <p class="text-[10px] text-slate-400 truncate">{{ authStore.user?.sucursal_nombre || 'Todas las Sedes' }}</p>
          </div>
        </div>
        <Button
          @click="handleLogout"
          icon="pi pi-sign-out"
          :label="isSidebarOpen ? 'Cerrar Sesión' : undefined"
          text
          severity="danger"
          size="small"
          class="w-full text-xs"
          :class="!isSidebarOpen && 'justify-center px-0'"
          :title="!isSidebarOpen ? 'Cerrar Sesión' : undefined"
        />
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
      <!-- Topbar -->
      <header class="h-16 flex-shrink-0 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10 shadow-sm">
        <div class="flex items-center space-x-3">
          <h1 class="text-base font-bold text-slate-800 tracking-tight">
            {{ pageTitle }}
          </h1>
        </div>

        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2 text-xs font-medium text-slate-600 bg-slate-100 py-1.5 px-3 rounded-full border border-slate-200">
            <i class="pi pi-building text-blue-600"></i>
            <span>{{ authStore.user?.sucursal_nombre || 'Sede Central' }}</span>
          </div>


          <router-link
            to="/llamadas-pendientes"
            class="relative p-2 rounded-full text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
            title="Llamadas Pendientes a Pacientes"
          >
            <i class="pi pi-phone text-lg"></i>
            <span
              v-if="pendingCallsCount > 0"
              class="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center animate-pulse"
            >
              {{ pendingCallsCount }}
            </span>
          </router-link>
        </div>
      </header>

      <!-- Main Body -->
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>
