import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '../stores/auth.store';

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
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/DashboardView.vue'),
      },
      {
        path: 'ordenes',
        name: 'OrdenesList',
        component: () => import('../views/ordenes/OrdenesListView.vue'),
      },
      {
        path: 'ordenes/nueva',
        name: 'OrdenCreate',
        component: () => import('../views/ordenes/OrdenCreateView.vue'),
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
      },
      {
        path: 'pacientes',
        name: 'PacientesList',
        component: () => import('../views/pacientes/PacientesListView.vue'),
      },
      {
        path: 'obras-sociales',
        name: 'ObrasSocialesList',
        component: () => import('../views/mutuales/ObrasSocialesListView.vue'),
      },
      {
        path: 'mutuales',
        redirect: '/obras-sociales',
      },
      {
        path: 'usuarios',
        name: 'UsersList',
        component: () => import('../views/users/UsersListView.vue'),
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
    return next({ name: 'Dashboard' });
  }

  if (to.meta.roles && Array.isArray(to.meta.roles)) {
    const requiredRoles = to.meta.roles as string[];
    const hasRequiredRole = requiredRoles.some((role) => authStore.hasRole(role));
    if (!hasRequiredRole) {
      return next({ name: 'Dashboard' });
    }
  }

  next();
});

export default router;
