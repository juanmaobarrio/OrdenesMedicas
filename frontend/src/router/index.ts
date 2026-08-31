import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '../stores/auth.store';

function getDefaultRoute(authStore: any): string {
  if (authStore.isAdmin || authStore.hasPermission('dashboard:view')) {
    return '/dashboard';
  }
  if (authStore.hasPermission('ordenes:view')) {
    return '/ordenes';
  }
  if (authStore.hasPermission('ordenes:calls')) {
    return '/llamadas-pendientes';
  }
  if (authStore.hasPermission('ordenes:create')) {
    return '/ordenes/nueva';
  }
  if (authStore.hasPermission('pacientes:manage')) {
    return '/pacientes';
  }
  if (authStore.hasPermission('users:manage')) {
    return '/usuarios';
  }
  return '/manual_usuario';
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'HomeRedirect',
        component: { render: () => null },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/DashboardView.vue'),
        meta: { permission: 'dashboard:view' },
      },
      {
        path: 'ordenes',
        name: 'OrdenesList',
        component: () => import('../views/ordenes/OrdenesListView.vue'),
        meta: { permission: 'ordenes:view' },
      },
      {
        path: 'ordenes/nueva',
        name: 'OrdenCreate',
        component: () => import('../views/ordenes/OrdenCreateView.vue'),
        meta: { permission: 'ordenes:create' },
      },
      {
        path: 'ordenes/:id',
        name: 'OrdenDetail',
        component: () => import('../views/ordenes/OrdenDetailView.vue'),
        props: true,
      },
      {
        path: 'llamadas-pendientes',
        name: 'LlamadasPendientes',
        component: () => import('../views/ordenes/LlamadasPendientesView.vue'),
        meta: { permission: 'ordenes:calls' },
      },
      {
        path: 'pacientes',
        name: 'PacientesList',
        component: () => import('../views/pacientes/PacientesListView.vue'),
        meta: { permission: 'pacientes:manage' },
      },
      {
        path: 'obras-sociales',
        name: 'ObrasSocialesList',
        component: () => import('../views/mutuales/ObrasSocialesListView.vue'),
        meta: { roles: ['ADMIN'] },
      },
      {
        path: 'mutuales',
        redirect: '/obras-sociales',
      },
      {
        path: 'usuarios',
        name: 'UsersList',
        component: () => import('../views/users/UsersListView.vue'),
        meta: { permission: 'users:manage' },
      },
      {
        path: 'sucursales',
        name: 'SucursalesList',
        component: () => import('../views/users/SucursalesListView.vue'),
        meta: { roles: ['ADMIN'] },
      },
      {
        path: 'configuracion',
        name: 'Configuracion',
        component: () => import('../views/config/ConfiguracionView.vue'),
        meta: { roles: ['ADMIN'] },
      },
      {
        path: 'manual_usuario',
        name: 'ManualUsuario',
        component: () => import('../views/help/ManualUsuarioView.vue'),
      },
      {
        path: 'manual',
        redirect: '/manual_usuario',
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();

  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser();
  }

  const isPublic = to.meta.public === true;
  const requiresAuth = to.meta.requiresAuth !== false;

  if (requiresAuth && !authStore.isAuthenticated && !isPublic) {
    return next({ name: 'Login', query: { redirect: to.fullPath } });
  }

  if (isPublic && authStore.isAuthenticated) {
    return next(getDefaultRoute(authStore));
  }

  // Redirección de landing "/"
  if (to.path === '/' || to.name === 'HomeRedirect') {
    return next(getDefaultRoute(authStore));
  }

  // Validación de permiso específico RBAC
  if (to.meta.permission && typeof to.meta.permission === 'string') {
    const hasPerm = authStore.isAdmin || authStore.hasPermission(to.meta.permission);
    if (!hasPerm) {
      return next(getDefaultRoute(authStore));
    }
  }

  // Validación por rol requerido
  if (to.meta.roles && Array.isArray(to.meta.roles)) {
    const requiredRoles = to.meta.roles as string[];
    const hasRequiredRole = authStore.isAdmin || requiredRoles.some((role) => authStore.hasRole(role));
    if (!hasRequiredRole) {
      return next(getDefaultRoute(authStore));
    }
  }

  next();
});

export default router;
