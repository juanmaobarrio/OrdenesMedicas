export interface ObraSocial {
  id: string;
  codigo: string;
  sigla: string;
  nombre: string;
  codigo_externo?: string | null;
  dias_vencimiento: number;
  copago_default?: number;
  porcentaje_cobertura_apb?: number;
  activa: boolean;
  display_name: string;
  created_at?: string;
  updated_at?: string;
}

export interface ObraSocialCreate {
  codigo: string;
  sigla: string;
  nombre: string;
  codigo_externo?: string | null;
  dias_vencimiento: number;
  copago_default?: number;
  porcentaje_cobertura_apb?: number;
  activa?: boolean;
}

export interface ObraSocialUpdate {
  sigla?: string;
  nombre?: string;
  codigo_externo?: string | null;
  dias_vencimiento?: number;
  copago_default?: number;
  porcentaje_cobertura_apb?: number;
  activa?: boolean;
}
