<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
  icon?: string;
}>();
</script>

<template>
  <div class="flex flex-col items-center justify-center p-12 text-center bg-white rounded-xl border border-dashed border-slate-300">
    <div class="w-12 h-12 mb-3 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
      <i :class="icon || 'pi pi-folder-open'" class="text-xl"></i>
    </div>
    <h3 class="text-base font-semibold text-slate-700">{{ title }}</h3>
    <p v-if="description" class="mt-1 text-sm text-slate-500 max-w-sm">{{ description }}</p>
    <slot name="action"></slot>
  </div>
</template>
