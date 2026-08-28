export interface Paciente {
  id: string;
  documento: string;
  nombres: string;
  apellidos: string;
  nombre_completo: string;
  fecha_nacimiento?: string | null;
  obra_social?: string | null;
  nro_afiliado?: string | null;
  telefono?: string | null;
  email?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PacienteCreate {
  documento: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento?: string | null;
  obra_social?: string | null;
  nro_afiliado?: string | null;
  telefono?: string | null;
  email?: string | null;
  is_active?: boolean;
}

export interface PacienteSearchResult {
  id: string;
  documento: string;
  nombre_completo: string;
  obra_social?: string | null;
  nro_afiliado?: string | null;
  telefono?: string | null;
}

export interface PacientePaginatedResponse {
  items: Paciente[];
  total: number;
  skip: number;
  limit: number;
}
