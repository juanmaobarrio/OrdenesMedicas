<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    minHeight?: string;
    readonly?: boolean;
    showHtmlToggle?: boolean;
  }>(),
  {
    placeholder: 'Escriba las indicaciones aquí...',
    minHeight: '140px',
    readonly: false,
    showHtmlToggle: true,
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const editorRef = ref<HTMLDivElement | null>(null);
const isRawHtmlMode = ref(false);
const rawHtml = ref('');

// Sincronizar el valor hacia el editor editable
const syncToEditor = (content: string) => {
  if (!editorRef.value) return;
  // Convertir texto plano con saltos de línea a párrafos/br si no tiene HTML
  let formatted = content || '';
  if (formatted && !/<(p|b|strong|i|em|u|ul|ol|li|br|mark|span|div)[^>]*>/i.test(formatted)) {
    formatted = formatted
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => `<p>${line}</p>`)
      .join('');
  }
  if (editorRef.value.innerHTML !== formatted) {
    editorRef.value.innerHTML = formatted;
  }
  rawHtml.value = formatted;
};

onMounted(() => {
  syncToEditor(props.modelValue);
});

watch(
  () => props.modelValue,
  (newVal) => {
    if (editorRef.value && editorRef.value.innerHTML !== newVal) {
      syncToEditor(newVal);
    }
  }
);

const handleInput = () => {
  if (!editorRef.value) return;
  const content = editorRef.value.innerHTML;
  rawHtml.value = content;
  emit('update:modelValue', content);
};

const handleRawHtmlChange = () => {
  emit('update:modelValue', rawHtml.value);
  if (editorRef.value) {
    editorRef.value.innerHTML = rawHtml.value;
  }
};

const toggleRawHtml = () => {
  if (isRawHtmlMode.value) {
    // Al volver al modo visual, sincronizar el editor
    if (editorRef.value) {
      editorRef.value.innerHTML = rawHtml.value;
    }
  } else {
    // Al entrar al modo HTML, sincronizar el texto plano
    if (editorRef.value) {
      rawHtml.value = editorRef.value.innerHTML;
    }
  }
  isRawHtmlMode.value = !isRawHtmlMode.value;
};

// Ejecutor de comandos de formato
const exec = (command: string, value: string | undefined = undefined) => {
  if (props.readonly) return;
  if (editorRef.value) {
    editorRef.value.focus();
  }
  document.execCommand(command, false, value);
  handleInput();
};

const applyHighlight = () => {
  if (props.readonly) return;
  if (editorRef.value) {
    editorRef.value.focus();
  }
  // Resaltado con color ámbar suave o amarillo de marcador
  const selection = window.getSelection();
  if (selection && selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    if (!range.collapsed) {
      const mark = document.createElement('mark');
      mark.style.backgroundColor = '#fef08a';
      mark.style.color = '#854d0e';
      mark.style.padding = '1px 4px';
      mark.style.borderRadius = '3px';
      mark.style.fontWeight = '600';
      try {
        range.surroundContents(mark);
        handleInput();
      } catch {
        exec('backColor', '#fef08a');
      }
      return;
    }
  }
  exec('backColor', '#fef08a');
};
</script>

<template>
  <div class="border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition">
    <!-- Barra de Herramientas -->
    <div
      v-if="!readonly"
      class="flex flex-wrap items-center gap-1 px-2.5 py-1.5 bg-slate-50 border-b border-slate-200 text-slate-700 select-none"
    >
      <button
        type="button"
        @mousedown.prevent="exec('bold')"
        class="p-1.5 rounded hover:bg-slate-200 text-slate-700 transition"
        title="Negrita (Ctrl+B)"
      >
        <span class="font-bold text-xs px-0.5">B</span>
      </button>

      <button
        type="button"
        @mousedown.prevent="exec('italic')"
        class="p-1.5 rounded hover:bg-slate-200 text-slate-700 transition"
        title="Cursiva (Ctrl+I)"
      >
        <span class="italic text-xs px-0.5 font-serif">I</span>
      </button>

      <button
        type="button"
        @mousedown.prevent="exec('underline')"
        class="p-1.5 rounded hover:bg-slate-200 text-slate-700 transition"
        title="Subrayado (Ctrl+U)"
      >
        <span class="underline text-xs px-0.5">U</span>
      </button>

      <div class="w-px h-4 bg-slate-300 mx-0.5"></div>

      <button
        type="button"
        @mousedown.prevent="exec('insertUnorderedList')"
        class="p-1.5 rounded hover:bg-slate-200 text-slate-700 transition text-xs flex items-center gap-1"
        title="Lista con Viñetas"
      >
        <i class="pi pi-list text-xs"></i>
      </button>

      <button
        type="button"
        @mousedown.prevent="exec('insertOrderedList')"
        class="p-1.5 rounded hover:bg-slate-200 text-slate-700 transition text-xs font-semibold px-1"
        title="Lista Numerada"
      >
        1. 2.
      </button>

      <div class="w-px h-4 bg-slate-300 mx-0.5"></div>

      <button
        type="button"
        @mousedown.prevent="applyHighlight"
        class="p-1.5 rounded hover:bg-amber-100 text-amber-800 transition text-xs flex items-center gap-1 font-semibold"
        title="Resaltar Texto Importante"
      >
        <span class="bg-amber-200 px-1 rounded text-[10px]">Marcador</span>
      </button>

      <button
        type="button"
        @mousedown.prevent="exec('removeFormat')"
        class="p-1.5 rounded hover:bg-slate-200 text-slate-500 transition text-xs"
        title="Limpiar Formato"
      >
        <i class="pi pi-filter-slash text-xs"></i>
      </button>

      <!-- Toggle Modo HTML -->
      <button
        v-if="showHtmlToggle"
        type="button"
        @click="toggleRawHtml"
        class="ml-auto px-2 py-0.5 rounded text-[11px] font-mono border transition"
        :class="isRawHtmlMode ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'"
        :title="isRawHtmlMode ? 'Volver a Vista Enriquecida' : 'Editar Código HTML directamente'"
      >
        {{ isRawHtmlMode ? '✕ Vista Visual' : '&lt;/&gt; HTML' }}
      </button>
    </div>

    <!-- Contenedor Editable Visual -->
    <div
      v-show="!isRawHtmlMode"
      ref="editorRef"
      :contenteditable="!readonly"
      :style="{ minHeight }"
      class="p-3 text-slate-800 text-sm outline-none overflow-y-auto leading-relaxed prose prose-sm max-w-none focus:outline-none"
      :data-placeholder="placeholder"
      @input="handleInput"
    ></div>

    <!-- Contenedor Modo Código HTML -->
    <textarea
      v-if="showHtmlToggle"
      v-show="isRawHtmlMode"
      v-model="rawHtml"
      :style="{ minHeight }"
      class="w-full p-3 font-mono text-xs text-slate-800 bg-slate-50 outline-none resize-y border-0 focus:ring-0"
      @input="handleRawHtmlChange"
    ></textarea>
  </div>
</template>

<style scoped>
[contenteditable]:empty:before {
  content: attr(data-placeholder);
  color: #94a3b8;
  pointer-events: none;
  display: block;
}

:deep(p) {
  margin-bottom: 0.5rem;
}

:deep(p:last-child) {
  margin-bottom: 0;
}

:deep(ul) {
  list-style-type: disc;
  margin-left: 1.25rem;
  margin-bottom: 0.5rem;
}

:deep(ol) {
  list-style-type: decimal;
  margin-left: 1.25rem;
  margin-bottom: 0.5rem;
}

:deep(li) {
  margin-bottom: 0.25rem;
}

:deep(mark) {
  background-color: #fef08a;
  color: #854d0e;
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 600;
}
</style>
