import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authService } from '../services/auth.service';
import { LoginCredentials, UserSession } from '../types/auth';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserSession | null>(null);
  const token = ref<string | null>(localStorage.getItem('access_token'));
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);
  const isAdmin = computed(() => user.value?.role_code === 'ADMIN' || user.value?.is_superuser === true);
  const isAuditor = computed(() => user.value?.role_code === 'AUDITOR');
  const isUsuario = computed(() => user.value?.role_code === 'USUARIO');

  const hasRole = (role: string) => {
    if (user.value?.is_superuser) return true;
    return user.value?.role_code === role;
  };

  const hasPermission = (permission: string) => {
    if (user.value?.is_superuser) return true;
    return user.value?.permissions.includes(permission) ?? false;
  };

  const login = async (credentials: LoginCredentials) => {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await authService.login(credentials);
      token.value = response.access_token;
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      await fetchCurrentUser();
      return true;
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al iniciar sesión';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchCurrentUser = async () => {
    if (!token.value) return;
    try {
      const userData = await authService.getCurrentUser();
      user.value = userData;
    } catch (err) {
      logout();
    }
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    isAuditor,
    isUsuario,
    hasRole,
    hasPermission,
    login,
    fetchCurrentUser,
    logout,
  };
});
