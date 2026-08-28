import { defineStore } from 'pinia';
import { ref } from 'vue';
import { ordenesService, ListOrdenesParams } from '../services/ordenes.service';
import {
  OrdenLlamadaPendienteItem,
  OrdenMedicaDetail,
  OrdenMedicaListItem,
  ResultadoLlamada,
  TipoLlamada,
} from '../types/ordenes';


export const useOrdenesStore = defineStore('ordenes', () => {
  const items = ref<OrdenMedicaListItem[]>([]);
  const total = ref<number>(0);
  const isLoading = ref<boolean>(false);
  const currentOrden = ref<OrdenMedicaDetail | null>(null);
  const llamadasPendientes = ref<OrdenLlamadaPendienteItem[]>([]);
  const isLoadingLlamadas = ref<boolean>(false);

  const filters = ref<ListOrdenesParams>({
    skip: 0,
    limit: 50,
    estado: undefined,
    sucursal_id: undefined,
    mutual: undefined,
    search: undefined,
    fecha_desde: undefined,
    fecha_hasta: undefined,
  });

  const fetchOrdenes = async () => {
    isLoading.value = true;
    try {
      const response = await ordenesService.list(filters.value);
      items.value = response.items;
      total.value = response.total;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchOrdenById = async (id: string) => {
    isLoading.value = true;
    try {
      const response = await ordenesService.getById(id);
      currentOrden.value = response;
      return response;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchLlamadasPendientes = async (sucursalId?: string) => {
    isLoadingLlamadas.value = true;
    try {
      const response = await ordenesService.listLlamadasPendientes(sucursalId);
      llamadasPendientes.value = response;
    } finally {
      isLoadingLlamadas.value = false;
    }
  };

  const registrarLlamada = async (
    ordenId: string,
    tipo: TipoLlamada,
    resultado: ResultadoLlamada,
    observaciones?: string
  ) => {
    const res = await ordenesService.registrarLlamada(ordenId, {
      tipo_llamada: tipo,
      resultado,
      observaciones,
    });
    // Si fue exitosa, remover de la lista local de llamadas pendientes
    if (resultado === 'EXITOSA') {
      llamadasPendientes.value = llamadasPendientes.value.filter((o) => o.id !== ordenId);
    }
    return res;
  };

  return {
    items,
    total,
    isLoading,
    currentOrden,
    llamadasPendientes,
    isLoadingLlamadas,
    filters,
    fetchOrdenes,
    fetchOrdenById,
    fetchLlamadasPendientes,
    registrarLlamada,
  };
});
