<script setup lang="ts">
import ProgressSpinner from 'primevue/progressspinner';

defineProps<{
  message?: string;
}>();
</script>

<template>
  <div class="flex flex-col items-center justify-center p-8 space-y-3">
    <ProgressSpinner style="width: 42px; height: 42px" strokeWidth="4" />
    <span v-if="message" class="text-sm font-medium text-slate-500">{{ message }}</span>
  </div>
</template>
