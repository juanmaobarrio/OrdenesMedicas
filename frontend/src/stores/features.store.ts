import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { configService } from '../services/config.service';
import { SystemFeaturesConfig, SystemFeaturesConfigUpdate } from '../types/ordenes';

export const useFeaturesStore = defineStore('features', () => {
  const features = ref<SystemFeaturesConfig>({
    modulo_mail: false,
    calculadora_estudios: false,
    estudios_autorizacion: false,
    indicaciones_estudios: false,
    asignar_auditor: false,
  });

  const isLoaded = ref(false);
  const isLoading = ref(false);

  // Getters / Computed helpers
  const isMailEnabled = computed(() => Boolean(features.value.modulo_mail));
  const isCalculadoraEnabled = computed(() => Boolean(features.value.calculadora_estudios));
  const isEstudiosAutorizacionEnabled = computed(() => Boolean(features.value.estudios_autorizacion));
  const isIndicacionesEnabled = computed(() => Boolean(features.value.indicaciones_estudios));
  const isAsignarAuditorEnabled = computed(() => Boolean(features.value.asignar_auditor));

  const fetchFeatures = async (force = false) => {
    if (isLoaded.value && !force) return features.value;
    isLoading.value = true;
    try {
      const data = await configService.getFeatures();
      features.value = data;
      isLoaded.value = true;
    } catch (err) {
      console.warn('No se pudieron cargar las features del sistema:', err);
    } finally {
      isLoading.value = false;
    }
    return features.value;
  };

  const updateFeatures = async (payload: SystemFeaturesConfigUpdate) => {
    isLoading.value = true;
    try {
      const updated = await configService.updateFeatures(payload);
      features.value = updated;
      isLoaded.value = true;
      return updated;
    } finally {
      isLoading.value = false;
    }
  };

  return {
    features,
    isLoaded,
    isLoading,
    isMailEnabled,
    isCalculadoraEnabled,
    isEstudiosAutorizacionEnabled,
    isIndicacionesEnabled,
    isAsignarAuditorEnabled,
    fetchFeatures,
    updateFeatures,
  };
});
