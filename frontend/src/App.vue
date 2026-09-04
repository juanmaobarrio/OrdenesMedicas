<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuthStore } from './stores/auth.store';
import { useFeaturesStore } from './stores/features.store';

const authStore = useAuthStore();
const featuresStore = useFeaturesStore();

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await featuresStore.fetchFeatures();
  }
});
</script>

<template>
  <router-view />
</template>

<style>
/* Global Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
