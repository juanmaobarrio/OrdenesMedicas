<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../../stores/auth.store';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';
import Message from 'primevue/message';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const identifier = ref('');
const password = ref('');
const errorMessage = ref<string | null>(null);

const handleLogin = async () => {
  if (!identifier.value.trim() || !password.value.trim()) {
    errorMessage.value = 'Por favor complete todos los campos';
    return;
  }

  errorMessage.value = null;
  try {
    await authStore.login({
      identifier: identifier.value.trim(),
      password: password.value,
    });
    const redirectPath = (route.query.redirect as string) || '/dashboard';
    router.push(redirectPath);
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Credenciales inválidas o cuenta inactiva';
  }
};
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-blue-950 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-slate-100">
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto bg-blue-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-blue-500/30 mb-4">
          <i class="pi pi-heart-fill text-3xl"></i>
        </div>

        <h2 class="text-2xl font-bold text-slate-800">Gestión de Órdenes Médicas</h2>
        <p class="text-sm text-slate-500 mt-1">Ingrese sus credenciales para acceder al sistema</p>
      </div>

      <Message v-if="errorMessage" severity="error" class="mb-4" :closable="false">
        {{ errorMessage }}
      </Message>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Usuario o Correo Electrónico
          </label>
          <div class="p-input-icon-left w-full">
            <i class="pi pi-user text-slate-400"></i>
            <InputText
              v-model="identifier"
              type="text"
              class="w-full pl-10"
              placeholder="admin o usuario@correo.com"
              autofocus
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Contraseña
          </label>
          <div class="p-input-icon-left w-full">
            <i class="pi pi-lock text-slate-400"></i>
            <Password
              v-model="password"
              class="w-full"
              inputClass="w-full pl-10"
              :feedback="false"
              toggleMask
              placeholder="••••••••"
            />
          </div>
        </div>

        <Button
          type="submit"
          label="Iniciar Sesión"
          icon="pi pi-sign-in"
          class="w-full mt-2"
          :loading="authStore.isLoading"
        />
      </form>

      <div class="mt-6 pt-6 border-t border-slate-100 text-center text-xs text-slate-400">
        Sistema de Gestión Médica & Auditoría &bull; Versión 2.0
      </div>
    </div>
  </div>
</template>
