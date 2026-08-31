# DOCUMENTACIÓN TÉCNICA Y DE ARQUITECTURA
## SISTEMA DE GESTIÓN DE ÓRDENES MÉDICAS

---

## 1. INTRODUCCIÓN Y OBJETIVOS

Este documento registra la arquitectura, estructura de archivos, módulos, endpoints y decisiones de diseño del **Sistema de Gestión de Órdenes Médicas**.
El proyecto surge con la finalidad de modernizar y reemplazar un aplicativo legacy en PHP, priorizando:

- **Estabilidad y resiliencia:** Alta tolerancia a fallos y degradación elegante.
- **Trazabilidad estricta:** Registro inmutable de auditoría (Audit Trail) para todas las operaciones sobre órdenes médicas.
- **Modularidad y escalabilidad:** Arquitectura orientada a dominios (DDD / Clean Architecture).
- **Eficiencia de hardware:** Optimizado para despliegues ligeros en hardware local (ZimaBoard x86) y preparado para escalado en la nube (VPS / Cloud).

---

## 2. STACK TECNOLÓGICO SELECCIONADO

### Backend
- **Lenguaje:** Python 3.11+
- **Framework Web:** FastAPI
- **ORM / Capa de Datos:** SQLAlchemy 2.0+ (modo asíncrono con `asyncpg`)
- **Migraciones:** Alembic
- **Validación y Serialización:** Pydantic v2 y Pydantic-Settings
- **Seguridad y Criptografía:** Passlib (Argon2 con fallback a Bcrypt), Python-Jose (JWT tokens)
- **Logging Estructurado:** Loguru

### Frontend *(Planificado)*
- **Framework:** Vue 3 (Composition API con `<script setup lang="ts">`)
- **Build Tool:** Vite + TypeScript
- **Librería de Componentes:** PrimeVue (Presets modernos Tailwind / Aura)
- **Estilos:** Tailwind CSS
- **Gestión de Estado:** Pinia
- **Enrutamiento:** Vue Router 4
- **Cliente HTTP:** Axios (con interceptores centralizados)
- **Validación de Formularios:** VeeValidate + Zod

### Base de Datos e Infraestructura
- **Motor:** PostgreSQL 16+ con soporte transaccional estricto y tipos JSONB.
- **Contenedores:** Docker y Docker Compose.
- **Proxy Inverso:** Nginx / Caddy.


---

## 3. ESTRUCTURA DEL BACKEND

Se ha implementado una arquitectura limpia y desacoplada organizada por dominios de negocio:

```text
backend/
├── alembic/                      # Directorio de migraciones de base de datos
│   └── versions/                 # Archivos de versionado Alembic
├── app/
│   ├── core/                     # Servicios y configuraciones transversales
│   │   ├── config.py             # Variables de entorno y configuración central (Pydantic Settings)
│   │   ├── database.py           # Conexión AsyncSession y engine SQLAlchemy
│   │   ├── exceptions.py         # Jerarquía de excepciones personalizadas de la aplicación
│   │   ├── logging.py            # Logger estructurado (Loguru) con rotación a disco
│   │   └── security.py           # Hashing de contraseñas (Argon2/Bcrypt) y generación/validación JWT
│   ├── shared/                   # Clases y mixins compartidos
│   │   └── base_model.py         # DeclarativeBase, UUIDPrimaryKeyMixin, TimestampMixin
│   ├── modules/                  # Módulos organizados por dominio
│   │   ├── auth/                 # Autenticación, login y refresco de tokens
│   │   ├── users/                # Gestión de usuarios, roles y permisos
│   │   ├── pacientes/            # Padrón de pacientes y datos clínicos asociados
│   │   ├── ordenes/              # Ciclo de vida y planificación de órdenes médicas
│   │   ├── auditorias/           # Registro de auditoría, solicitudes de cambio y trazabilidad
│   │   └── dashboard/            # Agregaciones, métricas e indicadores de rendimiento
│   └── main.py                   # Fábrica de aplicación FastAPI, CORS, middlewares y health check
├── .env.example                  # Plantilla de variables de entorno requeridas
├── Dockerfile                    # Definición de contenedor liviano basado en Python 3.11-slim
└── requirements.txt              # Dependencias fijadas del proyecto
```

Cada módulo dentro de `app/modules/<dominio>/` cuenta con la siguiente segregación estandarizada:
- `models.py`: Entidades y mapeo relacional de SQLAlchemy 2.0.
- `schemas.py`: Esquemas DTO de entrada, salida y actualización (Pydantic v2).
- `repository.py`: Capa de persistencia y consultas asíncronas a la base de datos.
- `service.py`: Lógica pura de negocio y orquestación de operaciones.
- `router.py`: Controladores de ruta y endpoints HTTP FastAPI.


---

## 4. DETALLE DE COMPONENTES DEL BACKEND IMPLEMENTADOS

### 4.1 Configuración Central (`app/core/config.py`)
- Clase `Settings` basada en `pydantic_settings.BaseSettings`.
- Construcción dinámica de la URL asíncrona de base de datos (`postgresql+asyncpg://...`).
- Gestión de CORS (`BACKEND_CORS_ORIGINS`) con validador para admitir listas o cadenas separadas por comas.
- Parámetros de JWT (`SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`).
- Límites de subida de archivos y directorio de almacenamiento (`UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`).

### 4.2 Persistencia Asíncrona (`app/core/database.py`)
- Creación de `create_async_engine` optimizado con `pool_pre_ping=True`, tamaño de pool y desbordamiento configurado.
- Creador de sesiones `AsyncSessionLocal` (`async_sessionmaker`).
- Generador de dependencias `get_db` con commit automático y rollback en caso de excepciones.

### 4.3 Seguridad y Criptografía (`app/core/security.py`)
- Contexto de contraseñas `CryptContext` con soporte primario de **Argon2** y compatibilidad con **Bcrypt**.
- Generación de tokens de acceso (`create_access_token`) con expiración en minutos y claim de tipo `access`.
- Generación de tokens de refresco (`create_refresh_token`) con expiración en días y claim de tipo `refresh`.
- Decodificación y validación de tokens JWT (`decode_token`).

### 4.4 Manejo Uniforme de Errores (`app/core/exceptions.py`)
- `AppException`: Excepción base con `status_code` y `detail`.
- `EntityNotFoundException` (404 Not Found): Para búsquedas fallidas por ID.
- `EntityAlreadyExistsException` (409 Conflict): Para restricciones únicas duplicadas (emails, DNI, etc.).
- `InvalidCredentialsException` (401 Unauthorized): Con cabecera `WWW-Authenticate: Bearer`.
- `ForbiddenActionException` (403 Forbidden): Para acceso denegado según rol/permiso.

### 4.5 Logging Estructurado (`app/core/logging.py`)
- Configuración con `Loguru`.
- Salida formateada con colores en consola (`sys.stdout`) para desarrollo y producción.
- Registro persistente rotativo en `logs/app_{YYYY-MM-DD}.log` con rotación a los 50 MB, retención de 30 días y compresión `.zip`.

### 4.6 Base Compartida de Modelos (`app/shared/base_model.py`)
- `Base`: `DeclarativeBase` de SQLAlchemy.
- `UUIDPrimaryKeyMixin`: Generación automática de IDs UUIDv4 indexados.
- `TimestampMixin`: Campos `created_at` y `updated_at` con `DateTime(timezone=True)` y timestamps de servidor.

### 4.7 Servidor y Ciclo de Vida (`app/main.py`)
- Fábrica `create_application()` con metadatos de OpenAPI (`/docs`, `/redoc`).
- Middleware de CORS configurado.
- Manejador global de excepciones para `AppException` y capturador de errores inesperados (500) con log de trazabilidad.
- Endpoint de verificación de salud operativo: `GET /health`.
- Inclusión de routers modulares: `/api/v1/auth` y `/api/v1`.

---

## 5. MÓDULO DE USUARIOS, ROLES, SUCURSALES Y AUTENTICACIÓN

### 5.1 Modelo Relacional (ERD)
- **`Sucursal` (`sucursales`):** `id` (UUIDv4), `nombre` (VARCHAR 100), `codigo` (VARCHAR 20, UNIQUE), `activa` (BOOLEAN).
- **`ObraSocial` (`obras_sociales`):** `id` (UUIDv4), `codigo` (VARCHAR 50, UNIQUE), `sigla` (VARCHAR 50), `nombre` (VARCHAR 150), `codigo_externo` (VARCHAR 50 NULLABLE), `dias_vencimiento` (INTEGER), `copago_default` (NUMERIC(12,2) DEFAULT 0.00), `activa` (BOOLEAN).
- **`Permission` (`permissions`):** `id` (UUIDv4), `code` (VARCHAR 80, UNIQUE), `module` (VARCHAR 50), `description` (VARCHAR 255).
- **`Role` (`roles`):** `id` (UUIDv4), `code` (VARCHAR 50, UNIQUE), `name` (VARCHAR 100), `description` (VARCHAR 255), `is_system` (BOOLEAN).
- **`role_permissions`:** Tabla intermedia `role_id` (FK roles.id ON DELETE CASCADE) + `permission_id` (FK permissions.id ON DELETE CASCADE).
- **`User` (`users`):** `id` (UUIDv4), `username` (VARCHAR 50, UNIQUE), `email` (VARCHAR 255, UNIQUE), `hashed_password` (VARCHAR 255), `first_name` (VARCHAR 100), `last_name` (VARCHAR 100), `is_active` (BOOLEAN), `is_superuser` (BOOLEAN), `role_id` (FK roles.id), `sucursal_id` (FK sucursales.id NULLABLE), `last_login_at` (TIMESTAMP NULLABLE).

### 5.2 Capa de Repositorio y Servicio
- **`SucursalRepository` / `SucursalService`:** Altas, bajas lógicas y consultas de sucursales.
- **`RoleRepository` / `RoleService`:** Creación y asignación de permisos a roles.
- **`UserRepository` / `UserService`:** Creación con hash Argon2, validación de unicidad para username/email, actualización de perfil y cambio seguro de contraseña.
- **`AuthService`:** Autenticación unificada (username o email indistintamente), emisión de JWT Access Tokens (60 min) y Refresh Tokens (7 días), y refresco transparente.

### 5.3 Seguridad y Dependencias RBAC (`app/modules/auth/dependencies.py`)
- `get_current_user`: Extracción y validación de Bearer Token JWT en cabecera HTTP.
- `require_roles(allowed_roles: List[str])`: Guardia de autorización por lista de roles (ej. `['ADMIN']`, `['ADMIN', 'AUDITOR']`).
- `require_permission(permission_code: str)`: Guardia de autorización por código de permiso específico.

### 5.4 Endpoints HTTP Expuestos

| Método | Endpoint | Descripción | Acceso / Permiso |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Inicio de sesión con usuario o email y password | Público |
| `POST` | `/api/v1/auth/refresh` | Renovación de token de acceso mediante refresh token | Público |
| `GET` | `/api/v1/auth/me` | Obtener perfil y permisos de la sesión actual | Autenticado |
| `GET` | `/api/v1/sucursales` | Listar sucursales (con filtro opcional `only_active`) | Autenticado |
| `POST` | `/api/v1/sucursales` | Crear una nueva sucursal | Rol: `ADMIN` |
| `GET` | `/api/v1/roles` | Listar roles del sistema y sus permisos asociados | Autenticado |
| `POST` | `/api/v1/roles` | Crear un nuevo rol con permisos | Rol: `ADMIN` |
| `PUT` | `/api/v1/roles/{id}` | Actualizar rol y permisos asignados | Rol: `ADMIN` |
| `DELETE` | `/api/v1/roles/{id}` | Eliminar rol personalizado | Rol: `ADMIN` |
| `GET` | `/api/v1/permissions` | Listar catálogo de permisos atómicos | Rol: `ADMIN` |
| `GET` | `/api/v1/users` | Listar usuarios con filtros por sucursal, rol y estado activo/inactivo | Autenticado |
| `POST` | `/api/v1/users` | Registrar un nuevo usuario con control de jerarquía de rol | Autenticado |
| `GET` | `/api/v1/users/{id}` | Obtener detalle completo de un usuario | Autenticado |
| `PUT` | `/api/v1/users/{id}` | Actualizar datos de un usuario | Rol: `ADMIN` |
| `PATCH` | `/api/v1/users/{id}/toggle-active` | Activar o inactivar cuenta de usuario | Rol: `ADMIN` |
| `POST` | `/api/v1/users/{id}/reset-password` | Restablecer contraseña por el Administrador (sin clave anterior) | Rol: `ADMIN` |
| `POST` | `/api/v1/users/{id}/change-password` | Actualización de contraseña propia | Autenticado |

---

## 6. MÓDULO DE PACIENTES

### 6.1 Modelo Relacional (ERD)
- **`Paciente` (`pacientes`):**
  - `id`: UUIDv4 (Primary Key).
  - `documento`: VARCHAR(30), único e indexado (DNI/Pasaporte/Cédula).
  - `nombres`: VARCHAR(100), no nulo (almacenado en Title Case).
  - `apellidos`: VARCHAR(100), no nulo (almacenado en UPPERCASE).
  - `fecha_nacimiento`: DATE (Obligatoria para altas, formato YYYY-MM-DD).
  - `obra_social`: VARCHAR(100), indexado nullable (almacenado en UPPERCASE).
  - `nro_afiliado`: VARCHAR(50), nullable.
  - `telefono`: VARCHAR(30), nullable.
  - `email`: VARCHAR(255), nullable.
  - `is_active`: BOOLEAN, default `True`.
  - `created_at`, `updated_at`: TIMESTAMPTZ automáticos.

### 6.2 Capa de Repositorio y Servicio
- **`PacienteRepository`:**
  - Búsqueda exacta por ID y por Documento.
  - Búsqueda rápida con `ILIKE` para autocompletado en el registro de órdenes médicas.
  - Listado paginado con filtros combinados (`search`, `obra_social`, `only_active`).
- **`PacienteService`:**
  - Validación de unicidad de documento al crear y actualizar.
  - Sanitización y estandarización automática de cadenas (mayúsculas/minúsculas).

### 6.3 Endpoints HTTP Expuestos

| Método | Endpoint | Descripción | Acceso / Permiso |
|---|---|---|---|
| `GET` | `/api/v1/pacientes` | Listar pacientes con paginación (`skip`, `limit`) y filtros (`search`, `obra_social`) | Autenticado |
| `GET` | `/api/v1/pacientes/search` | Búsqueda rápida para autocompletado de formularios (`q`, `limit`) | Autenticado |
| `POST` | `/api/v1/pacientes` | Registrar un nuevo paciente | Autenticado |
| `GET` | `/api/v1/pacientes/{id}` | Obtener ficha completa de paciente por ID | Autenticado |
| `GET` | `/api/v1/pacientes/documento/{doc}` | Buscar paciente por número de documento | Autenticado |
| `PUT` | `/api/v1/pacientes/{id}` | Actualizar datos filiatorios del paciente | Autenticado |

---

## 7. MÓDULO DE ÓRDENES MÉDICAS, CICLO DE VIDA Y TRAZABILIDAD

### 7.1 Modelo Relacional (ERD)

- **`OrdenMedica` (`ordenes_medicas`):**
  - `id`: UUIDv4 (Primary Key).
  - `nro_orden`: VARCHAR(50), único e indexado (generado correlativo anual: `ORD-YYYY-XXXXXX`).
  - `paciente_id`: UUIDv4 (FK `pacientes.id`, `ON DELETE RESTRICT`).
  - `sucursal_id`: UUIDv4 (FK `sucursales.id`, `ON DELETE RESTRICT`).
  - `created_by_user_id`: UUIDv4 (FK `users.id`, `ON DELETE RESTRICT`).
  - `assigned_auditor_id`: UUIDv4 (FK `users.id`, `ON DELETE SET NULL`, nullable).
  - `estado`: Enum `estado_orden_enum` (`Ingreso`, `en Auditoria`, `Solicitudes de auditoria`, `Actualizada`, `Auditoria Finalizada`, `Cancelada`, `Cerrada ok`, `Cerrada`).
  - `fecha_prescripcion`: DATE (Fecha en que el profesional médico emitió la orden).
  - `cantidad_ordenes_fisicas`: INTEGER (Cantidad de cupones / recetas físicas).
  - `mutual`: VARCHAR(100), indexado (Obra social / Prepaga).
  - `nro_afiliado`: VARCHAR(50), nullable (Obligatorio en alta de orden).
  - `valor_copago`: NUMERIC(12, 2) (Copago a abonar por el paciente).
  - `valor_estudios_no_autorizados`: NUMERIC(12, 2) (Monto de prácticas no autorizadas).
  - `abona_apb`: BOOLEAN (Indica si abona Acto Profesional Bioquímico).
  - `debe_orden_medica`: BOOLEAN (Indica si adeuda receta física original).
  - `fecha_vencimiento`: DATE nullable (Fecha límite de validez).
  - `numeros_auditoria`: JSONB (Array de códigos / números de auditoría autorizados).
  - **Datos de Contacto:** `contacto_nombre`, `contacto_horario`, `contacto_telefono`, `contacto_celular`, `contacto_email`.
  - **Observaciones:** `observaciones_ingreso`, `motivo_cancelacion`.

- **`AdjuntoOrden` (`ordenes_adjuntos`):**
  - `id`: UUIDv4.
  - `orden_id`: UUIDv4 (FK `ordenes_medicas.id`, `ON DELETE CASCADE`).
  - `subido_por_id`: UUIDv4 (FK `users.id`).
  - `nombre_archivo_original`, `nombre_archivo_almacenado`, `ruta_almacenamiento`, `tipo_mime`, `tamano_bytes`.

- **`AuditoriaSolicitud` (`auditoria_solicitudes`):**
  - `id`: UUIDv4.
  - `orden_id`: UUIDv4 (FK `ordenes_medicas.id`, `ON DELETE CASCADE`).
  - `auditor_id`: UUIDv4 (FK `users.id`).
  - `motivo_solicitud`: VARCHAR(150), `mensaje_auditor`: TEXT.
  - `respuesta_operador`: TEXT nullable, `respondido_por_id`: UUIDv4 nullable, `fecha_respuesta`: TIMESTAMPTZ nullable.
  - `estado`: Enum `estado_solicitud_enum` (`PENDIENTE`, `INFORMACION`, `RESPONDIDA`, `CERRADA`).

- **`RegistroLlamadaPaciente` (`ordenes_llamadas_pacientes`):**
  - Registro histórico de llamados de aviso y consultas del paciente.
  - `id`: UUIDv4, `orden_id`: UUIDv4, `user_id`: UUIDv4 (operador que realizó o atendió la llamada).
  - `tipo_llamada`: Enum `tipo_llamada_enum` (`SOLICITUD_AUDITORIA`, `AUDITORIA_FINALIZADA`, `CONSULTA_PACIENTE`, `SEGUIMIENTO_SUCURSAL`, `OTRO`).
  - `resultado`: Enum `resultado_llamada_enum` (`EXITOSA`, `NO_CONTESTA`, `NUMERO_ERRONEO`, `REINTENTAR`).
  - `observaciones`: TEXT (detalle de lo conversado).

- **`AuditoriaLog` (`auditoria_logs`):**
  - Bitácora inmutable (Audit Trail) para trazabilidad legal y auditoría interna.
  - `id`: UUIDv4, `orden_id`: UUIDv4 (FK `ordenes_medicas.id`), `user_id`: UUIDv4 nullable.
  - `accion`: VARCHAR(80), `estado_anterior`: VARCHAR(50), `estado_nuevo`: VARCHAR(50).
  - `detalles`: JSONB (snapshot / diff de cambios realizados).
  - `ip_address`: VARCHAR(50), `user_agent`: VARCHAR(255), `created_at`: TIMESTAMPTZ.

### 7.2 Máquina de Estados y Reglas de Negocio
1. **`Ingreso`:** Estado inicial al crear la orden médica.
2. **`en Auditoria`:** Se asigna un auditor médico a la orden o pasa a revisión técnica.
3. **`Solicitudes de auditoria`:** El auditor emite una observación/requerimiento documental; la orden queda a la espera de subsanación por la sucursal.
   - **Flujo de Llamada Obligatoria 1:** Se incorpora de inmediato a la **Bandeja de Llamadas Pendientes** para avisar al paciente.
   - Al registrarse un contacto exitoso, la orden **desaparece de la lista de llamadas pendientes**, pero **se mantiene en estado `Solicitudes de auditoria`**, marcando la fecha y operador que comunicó.
4. **`Actualizada`:** La sucursal responde a la observación o sube la documentación faltante; regresa al flujo de auditoría.
5. **`Auditoria Finalizada`:** El auditor médico aprueba la orden.
   - **Flujo de Llamada Obligatoria 2:** Se incorpora a la **Bandeja de Llamadas Pendientes** para notificar al paciente que su trámite fue aprobado.
   - Al registrarse contacto exitoso, **desaparece de la lista de pendientes**, manteniéndose en estado `Auditoria Finalizada` con su correspondiente registro.
6. **`Cerrada ok` / `Cerrada`:** Cierre administrativo / liquidación completada.
7. **`Cancelada`:** Anulación formal de la orden (requiere registrar obligatoriamente el motivo de cancelación).

### 7.3 Endpoints HTTP Expuestos

| Método | Endpoint | Descripción | Acceso / Permiso |
|---|---|---|---|
| `GET` | `/api/v1/ordenes` | Listar órdenes con filtros avanzados (estado, fechas, mutual, sucursal, etc.) | Autenticado (acotado por rol) |
| `GET` | `/api/v1/ordenes/llamadas-pendientes` | Bandeja de órdenes que requieren llamado de aviso al paciente | Autenticado |
| `POST` | `/api/v1/ordenes/{id}/registrar-llamada` | Registrar intento/llamada al paciente (limpia pendientes si es exitosa) | Autenticado |
| `POST` | `/api/v1/ordenes` | Crear una nueva orden médica | Autenticado |
| `GET` | `/api/v1/ordenes/{id}` | Obtener detalle completo, histórico de estados y adjuntos | Autenticado |
| `PUT` | `/api/v1/ordenes/{id}` | Modificar datos de una orden (no terminal) | Autenticado |
| `POST` | `/api/v1/ordenes/{id}/estado` | Ejecutar transición de estado del ciclo de vida | Autenticado |
| `POST` | `/api/v1/ordenes/{id}/asignar-auditor` | Asignar o reasignar auditor médico | Roles: `ADMIN`, `AUDITOR` |
| `POST` | `/api/v1/ordenes/{id}/solicitudes` | Emitir solicitud u observación médica | Roles: `ADMIN`, `AUDITOR` |
| `POST` | `/api/v1/ordenes/solicitudes/{id}/responder` | Responder requerimiento desde la sucursal | Autenticado |
| `POST` | `/api/v1/ordenes/{id}/adjuntos` | Subir archivo fotográfico / documental (PDF, PNG, JPG) | Autenticado |
| `GET` | `/api/v1/ordenes/adjuntos/{id}/descargar` | Descargar / Visualizar archivo adjunto | Autenticado |

---

## 8. INFRAESTRUCTURA, MIGRACIONES (ALEMBIC) Y SEMILLERO (SEED)

### 8.1 Configuración de Alembic Asíncrono (`alembic.ini` y `alembic/env.py`)
- Integración nativa con `asyncpg` y `SQLAlchemy 2.0 AsyncEngine`.
- Enlace dinámico con `settings.DATABASE_URL`.
- Registro centralizado de metadatos de todos los dominios (`users`, `pacientes`, `ordenes`).

### 8.2 Migración Inicial (`backend/alembic/versions/0001_initial_schema.py`)
Crea el esquema completo con integridad referencial:
1. **Tipos Enumerados:** `estado_orden_enum`, `estado_solicitud_enum`, `tipo_llamada_enum`, `resultado_llamada_enum`.
2. **Tablas Relacionales:**
   - `sucursales` (con índices únicos en `codigo`).
   - `permissions` (con índices únicos en `code`).
   - `roles` (con índices únicos en `code`).
   - `role_permissions` (tabla asociativa Many-to-Many con eliminación en cascada).
   - `users` (con índices únicos en `username` y `email`, FK a `roles` y `sucursales`).
   - `pacientes` (con índice único en `documento` e índice en `obra_social`).
   - `ordenes_medicas` (con índice único en `nro_orden`, índices en `estado`, `mutual`, `paciente_id`, `sucursal_id`).
   - `ordenes_adjuntos` (con FK a `ordenes_medicas` y `users`).
   - `auditoria_solicitudes` (con FK a `ordenes_medicas` y `users`).
   - `auditoria_logs` (con FK a `ordenes_medicas` y `users`).
   - `ordenes_llamadas_pacientes` (con FK a `ordenes_medicas` y `users`).
3. **Función Downgrade:** Reversión completa y limpia de tablas y tipos ENUM.

### 8.3 Semillero Inicial de Datos (`backend/app/core/seed.py`)
Script ejecutable para inicializar la base de datos con:
- **Sucursal Predeterminada:** `"Sede Central"` (`codigo="CENTRAL"`).
- **Catálogo de Permisos:** `users:manage`, `sucursales:manage`, `pacientes:manage`, `ordenes:create`, `ordenes:view`, `ordenes:update`, `ordenes:audit`, `ordenes:calls`, `dashboard:view`.
- **Roles Base:** `ADMIN` (acceso total), `AUDITOR` (auditoría médica), `USUARIO` (operador de sucursal).
- **Superusuario Inicial:**
  - **Usuario:** `admin`
  - **Contraseña:** `admin123456`
  - **Email:** `admin@auditoriasmedicas.local`

### 8.4 Despliegue con Docker Compose (`docker-compose.yml`)
- **`postgres`:** PostgreSQL 16 Alpine con health check (`pg_isready`), volumen persistente `postgres_data`.
- **`backend`:** Contenedor FastAPI Python 3.11-slim con aplicación automática de migraciones (`alembic upgrade head`), ejecución de seed (`python -m backend.app.core.seed`) y servidor Uvicorn con auto-reload.

---

## 9. MÓDULO DE DASHBOARD, MÉTRICAS Y REPORTES

### 9.1 Indicadores Clave de Rendimiento (KPIs)
- **Totales y Volúmenes:** Total de órdenes históricas, órdenes activas (no canceladas ni cerradas).
- **Desglose de Estados:** Cantidad de órdenes en `Ingreso`, `en Auditoria`, `Solicitudes de auditoria`, `Actualizada`, `Auditoria Finalizada`, `Cerrada ok`, `Cancelada`.
- **Tasa de Aprobación (%):** Indicador de calidad médica `(Aprobadas / Total Auditadas) * 100`.
- **Llamadas Pendientes:** Contador total de avisos pendientes a pacientes desglosado por solicitudes y por auditorías finalizadas.
- **Recaudación:** Total de copagos recaudados en moneda local.

### 9.2 Distribuciones y Tendencias para Gráficos
- **Distribución por Estado:** Cantidades y porcentajes calculados para gráficos de torta / donut.
- **Distribución por Sucursal:** Comparativa de órdenes abiertas vs órdenes cerradas por cada sede médica (gráfico de barras apiladas).
- **Top Mutuales / Obras Sociales:** Ranking de las 5 mutuales con mayor volumen y copago acumulado.
- **Tendencias Temporales (14 días):** Flujo diario de órdenes ingresadas vs órdenes finalizadas (gráfico de líneas temporales).

### 9.3 Exportación y Reportes (`GET /api/v1/dashboard/reportes/ordenes-csv`)
- Generación de reportes tabulares en streaming con codificación `UTF-8 BOM` para compatibilidad nativa e inmediata con Microsoft Excel.
- Permite filtros combinados por sucursal, estado, mutual y rango de fechas de prescripción.

### 9.4 Endpoints HTTP Expuestos

| Método | Endpoint | Descripción | Acceso / Permiso |
|---|---|---|---|
| `GET` | `/api/v1/dashboard/kpis` | Resumen de métricas y contadores clave | Autenticado (acotado por rol/sucursal) |
| `GET` | `/api/v1/dashboard/charts` | Datos formateados para gráficos analíticos | Autenticado (acotado por rol/sucursal) |
| `GET` | `/api/v1/dashboard/reportes/ordenes-csv` | Descarga de reporte en archivo CSV compatible con Excel | Autenticado (acotado por rol/sucursal) |

---

## 10. VALIDACIÓN Y PRUEBAS AUTOMATIZADAS DE LA API REST (`test_local_api.py`)

Se ha creado y ejecutado con éxito una suite integral de pruebas asíncronas para validar todos los flujos de la API REST:
- **`GET /health`**: Retorna `200 OK` y estado `healthy`.
- **`POST /api/v1/auth/login`**: Autenticación exitosa tanto por **username** (`admin`) como por **email** (`admin@auditoriasmedicas.local`), con emisión de tokens JWT.
- **`GET /api/v1/auth/me`**: Validación de sesión, obtención de rol `ADMIN`, sucursal y permisos.
- **`GET /api/v1/sucursales`**: Consulta de sedes autorizadas.
- **`POST /api/v1/pacientes`**: Alta de paciente con normalización de datos.
- **`POST /api/v1/ordenes`**: Generación de número correlativo anual (`ORD-YYYY-XXXXXX`) y creación en estado `Ingreso`.
- **`POST /api/v1/ordenes/{id}/solicitudes`**: Creación de observación médica por auditor y transición a `Solicitudes de auditoria`.
- **`GET /api/v1/ordenes/llamadas-pendientes`**: Incorporación inmediata a la bandeja de llamadas pendientes para avisar al paciente.
- **`POST /api/v1/ordenes/{id}/registrar-llamada`**: Registro de llamada exitosa; la orden desaparece de pendientes manteniendo su estado del ciclo de vida.
- **`GET /api/v1/dashboard/kpis`**: Cálculo en tiempo real de órdenes activas, recaudación y tasa de aprobación.

---

## 11. IMPLEMENTACIÓN DEL FRONTEND (VUE 3 + PRIMEVUE 4 + TAILWIND + PINIA)

Se ha creado y compilado exitosamente la aplicación web frontend en la carpeta `frontend/`:

### 11.1 Arquitectura y Tecnologías
- **Framework:** Vue 3 con Composition API y `<script setup lang="ts">`.
- **Build Tool & Tipado:** Vite 6 + TypeScript 5.6.
- **UI & Estilos:** PrimeVue 4 (tema `Aura` preset) + Tailwind CSS (Paleta Corporativa Azul / Medical Blue) + PrimeIcons.
- **Gestión de Estado:** Pinia (`auth.store.ts`, `ordenes.store.ts`).

- **Enrutamiento:** Vue Router 4 con guardias de navegación automáticos (`requiresAuth`, RBAC por rol `meta: { roles: ['ADMIN'] }`).
- **Cliente HTTP Centralizado:** Axios con interceptores para inyección de token Bearer y refresco automático transparente en 401.

### 11.2 Estructura de Vistas y Componentes
- **`AppLayout.vue`**: Layout corporativo con barra lateral que **inicia colapsada por defecto**, menú responsivo, selector de sucursal, perfil de usuario activo y badge de alertas de llamadas pendientes con contador en tiempo real.
- **`LoginView.vue`**: Pantalla de autenticación con soporte dual (username / email) y manejo de estados de carga.
- **`DashboardView.vue`**: Tarjetas de KPIs analíticos (totales, activas, en auditoría, tasa de aprobación, llamadas pendientes, copagos), gráficos de distribución por estado y sucursales, y botón de exportación a Excel (CSV).
- **`OrdenesListView.vue`**: Vista dinámica con arquitectura **Master-Detail Split View** (Maestro-Detalle en dos paneles). Permite navegar entre expedientes sin recargar la pantalla, seleccionar órdenes con un solo clic y alternar a vista de **Pantalla Completa** mediante botón dedicado en la barra de acciones superior, en cada fila del DataTable o en la cabecera del panel lateral.
- **`OrdenDetailPanel.vue`**: Expediente reactivo embebido con persistencia de tab activo, botón directo de **Pantalla Completa** para maximizar el expediente a pedido del usuario, pestaña de **Códigos de Auditoría** con agregador 1 a 1 y eliminación individual, visualizador **Popup Dialog** de fotos y PDFs (`<iframe>` e `<img>` sin descargar), pestaña de **Auditorías Previas** del paciente y modal de edición completa con selector de mutual y horarios de contacto.
- **`OrdenCreateView.vue`**: Formulario de alta con selector de **Obras Sociales / Mutuales** con cálculo automático de días de vencimiento de prescripción, selector de horarios de contacto (`Todo el día`, `Por la mañana`, `Por la tarde`, `Por la noche`, `Solo WhatsApp`, `Solo mail`), banner de alerta ante órdenes activas abiertas, y modal "+ Nuevo Paciente" al vuelo.
- **`OrdenDetailView.vue`**: Vista de detalle standalone a pantalla completa para acceso directo o maximizado con botón superior `← Volver al Listado de Órdenes` y sincronización integral de todas las herramientas del expediente (visores modales, auditorías previas, edición de datos y bitácora).
- **`LlamadasPendientesView.vue`**: Bandeja especializada para call center / recepción con filtros por sucursal, tabla optimizada y compacta con botón y modal **Popup de Observaciones** (detallando observaciones del auditor, resolución final de auditoría y notas de ingreso), acceso directo a pantalla completa de la orden y modal para registrar llamadas (`RegistrarLlamadaModal.vue`) sin alterar el estado del ciclo de vida de la orden médica.
- **`PacientesListView.vue`**: Padrón general de pacientes con búsqueda rápida y modal para registro/edición.
- **`ObrasSocialesListView.vue`**: Módulo integral de gestión y catálogo de Obras Sociales / Mutuales con altas, edición de siglas, razones sociales, códigos externos, configuración de días de validez/vencimiento y activación/desactivación operativa.
- **`UsersListView.vue`**: Módulo integral con pestañas para **Usuarios del Sistema** y **Roles y Permisos (RBAC)**, permitiendo crear roles personalizados, editar nombres, descripciones y asignar permisos atómicos agrupados por módulo.
- **`SucursalesListView.vue`**: Módulo de administración de sedes médicas.
- **`ConfiguracionView.vue`**: Módulo exclusivo para administradores con tres pestañas: **Motivos de Cancelación**, **Estados del Sistema (con ID numérico para n8n/APIs)** y **Ciclo de Vida y Reglas de Negocio**. Permite crear nuevos estados y clasificarlos como *En Proceso* o *Finalización*.










---

## 12. EJECUCIÓN Y ACCESO LOCAL

### 12.1 Servicios Activos
- **Backend API (FastAPI):** `http://127.0.0.1:8000`
  - Documentación Swagger Interactiva: `http://127.0.0.1:8000/docs`
  - Verificación de Salud: `http://127.0.0.1:8000/health`
- **Frontend SPA (Vue 3 + PrimeVue):** `http://127.0.0.1:5173`

### 12.2 Credenciales de Acceso Predeterminadas
- **Usuario:** `admin` (o `admin@auditoriasmedicas.local`)
- **Contraseña:** `admin123456`
- **Rol:** `ADMIN` (acceso a todos los módulos y sucursales)

---

## 13. GUÍA DE DESPLIEGUE EN PRODUCCIÓN (ZIMABOARD X86 Y GITHUB)

### 13.1 Arquitectura de Contenedores de Producción
Para maximizar el rendimiento y minimizar el consumo de recursos en hardware local (ZimaBoard con procesador Intel Celeron x86 y memoria RAM ajustada), se implementó una estrategia de contenedores altamente optimizada:

1. **Frontend (Nginx Alpine + Multi-stage Build):**
   - **Etapa de Construcción (Node 20 Alpine):** Instala dependencias y compila los paquetes minificados y optimizados en `dist/`.
   - **Etapa de Ejecución (Nginx Alpine):** Sirve únicamente los archivos estáticos estables (`.js`, `.css`, `.woff2`, `.html`), con compresión **Gzip** activa y cabeceras de caché inmutable para activos.
   - **Consumo de memoria:** Reduce el consumo de RAM de ~350MB (Node runtime) a menos de 15MB (Nginx).
   - **Enrutamiento y Reverse Proxy Integrado:** Nginx captura las rutas SPA mediante `try_files $uri $uri/ /index.html` (evitando errores 404 al recargar) y proxiea de forma transparente todas las peticiones `/api/` y `/docs` hacia el contenedor `backend:8000`.

2. **Backend (FastAPI + Python 3.11-slim):**
   - Script de entrada `entrypoint.sh` automatizado.
   - Aplica migraciones pendientes de Alembic (`alembic upgrade head`) al arrancar el contenedor.
   - Ejecuta la siembra de datos maestros de forma idempotente (`seed.py`).
   - Inicia el servidor Uvicorn con 2 workers balanceados, soporte de cabeceras proxy (`--proxy-headers`) y reenvío de IPs.

3. **Base de Datos (PostgreSQL 16 Alpine):**
   - Imagen ligera y segura basada en Alpine Linux.
   - Almacenamiento transaccional persistente mediante volumen Docker `postgres_data`.
   - Healthcheck integrado con `pg_isready` para sincronizar el arranque seguro del backend.

### 13.2 Estructura de Archivos para Producción
- `docker-compose.yml`: Configuración de servicios productivos para ZimaBoard / Servidor.
- `docker-compose.dev.yml`: Configuración para desarrollo local con hot-reload en contenedores.
- `.env.example`: Plantilla documentada de variables de entorno (puertos, credenciales PostgreSQL, clave secreta JWT, orígenes CORS).
- `frontend/Dockerfile`: Multi-stage Dockerfile para frontend.
- `frontend/nginx.conf`: Configuración del servidor web de producción y reverse proxy.
- `backend/Dockerfile`: Dockerfile de producción para FastAPI.
- `backend/entrypoint.sh`: Automatizador de arranque, migraciones y seed.
- `.gitignore`: Configuración estricta para excluir bases de datos SQLite locales, entornos virtuales, node_modules, logs y capturas de QA antes de subir a GitHub.
- `README.md`: Documentación completa y manual paso a paso de instalación en ZimaBoard.

### 13.3 Pasos para Subir a GitHub
1. Inicializar y verificar el repositorio local (`git status`).
2. Vincular el repositorio remoto de GitHub:
   ```bash
   git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   ```
3. Agregar y confirmar los cambios:
   ```bash
   git add .
   git commit -m "feat: Sistema de Gestión de Órdenes Médicas - Producción y Docker para ZimaBoard"
   git branch -M main
   git push -u origin main
   ```

### 13.4 Pasos para Desplegar en ZimaBoard
1. Conectarse a la ZimaBoard vía SSH o mediante la terminal de CasaOS.
2. Clonar el repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git /DATA/AppData/ordenes-medicas
   cd /DATA/AppData/ordenes-medicas
   ```
3. Configurar `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
4. Levantar el stack completo:
   ```bash
   docker compose up -d --build
   ```
5. Acceder a `http://IP_ZIMABOARD` o mediante tu dominio con las credenciales de administrador (`admin` / `admin123456`).

### 13.5 Integración y Acceso Seguro con Cloudflare (`auditorias.jmob.ar`)
El stack está diseñado bajo el patrón de **Dominio Unificado (Same-Origin Reverse Proxy)**:
- Nginx recibe el tráfico HTTPS enrutado por Cloudflare bajo el dominio `auditorias.jmob.ar`.
- Toda llamada del frontend a la API se ejecuta contra `/api/v1` (relativa), eliminando bloqueos de CORS entre diferentes puertos y previniendo alertas de Mixed Content.
- Nginx inyecta la cabecera `CF-Connecting-IP` y reenvía `X-Forwarded-For` y `X-Forwarded-Proto` hacia el backend FastAPI, permitiendo que el módulo de bitácora (Audit Trail) registre la IP real del usuario en cada auditoría médica.
- Configuración en Cloudflare Tunnel:
  - Public Hostname: `auditorias.jmob.ar`
  - Service: `HTTP -> localhost:80` (o el puerto configurado en `APP_PORT`).


- **Solución al error de validación Pydantic en `BACKEND_CORS_ORIGINS`:** Se implementó un parser resiliente en `backend/app/core/config.py` que admite comodín `*`, listas JSON o cadenas separadas por coma sin arrojar errores de validación en Docker Compose.

- **Mejoras solicitadas por usuarios (Mutuales, N° Afiliado y Totales a abonar):**
  - Se convirtió el campo de Obra Social en Pacientes a un selector `Dropdown` con búsqueda conectado al catálogo de mutuales.
  - Se incorporó el campo `nro_afiliado` en el modelo y esquema de Órdenes Médicas, con auto-completado automático desde el paciente seleccionado.
  - En la tabla de órdenes y en los paneles de detalle se muestra el **Valor Total a Abonar** (Bono/Copago + Estudios No Autorizados) con desglose claro de cada concepto.

- **Corrección de sincronización de columnas en PostgreSQL (`lifespan`):** Se añadió migración automática segura `IF NOT EXISTS` para `nro_afiliado`, `valor_estudios_no_autorizados`, `observacion_resultado_auditoria` y `debe_orden_medica` al iniciar el backend.
- **Sincronización de Alembic con `nro_afiliado`:** Se actualizó `0001_initial_schema.py` para incluir la columna `nro_afiliado` en `ordenes_medicas`.

- **Script de migración y diagnóstico (`migrar_columnas.py`):** Permite ejecutar `ALTER TABLE IF NOT EXISTS` e inspeccionar registros existentes directamente en PostgreSQL de ZimaBoard.

- **Corrección de actualización de jerarquía de roles (`hierarchy_level`):** Se mapeó `hierarchy_level` en `RoleService.update_role` y `create_role` en `backend/app/modules/users/service.py` para persistir correctamente el nivel jerárquico.

- **Actualización de Documentación OpenAPI / Swagger (`/docs`):**
  - Se añadieron metadatos enriquecidos con especificación completa de esquemas, códigos de respuesta, autenticación JWT Bearer y descripción del ciclo de vida de 8 estados de las órdenes médicas.
- **Manual de Usuario Integrado (`/manual_usuario` y `/manual`):**
  - Se diseñó e implementó una vista interactiva de manual de usuario con 9 capítulos temáticos (Acceso, Pacientes, Registro de Órdenes, Expediente y Visor Popup, Ciclo de Auditoría, Llamadas a Pacientes, Dashboard/Excel, Roles Jerárquicos y API/n8n).
  - Incluye buscador rápido por palabras clave, índice de navegación interactivo y botón de impresión / guardado en PDF.
  - Accesible desde el menú lateral para todos los usuarios autenticados.

- **Eliminación de archivos adjuntos:**
  - Endpoint `DELETE /api/v1/ordenes/adjuntos/{adjunto_id}` para eliminar archivos adjuntos no deseados con remoción física del disco y registro inmutable en la bitácora de auditoría (*Audit Trail*).
  - Botón de papelera roja 🗑️ en el panel de detalle (`OrdenDetailPanel.vue`) y en la vista completa (`OrdenDetailView.vue`) con confirmación interactiva.

- **Corrección de importación de `os` y `logger` en `OrdenMedicaService`:** Se añadieron los módulos faltantes en `backend/app/modules/ordenes/service.py` para prevenir error 500 al eliminar archivos adjuntos.

- **Configuración de Zona Horaria Argentina (`America/Argentina/Buenos_Aires` GMT-3):**
  - Se configuró la variable de entorno `TZ=America/Argentina/Buenos_Aires` e instalación de `tzdata` en los contenedores Docker (`postgres`, `backend`, `frontend`).
  - Se creó la utilidad `frontend/src/utils/date.ts` con funciones `formatDateTime` y `formatDate` para representar todas las marcas temporales, historial de auditoría y fechas en la hora local oficial de Argentina (UTC-3).


---

## 14. ACTUALIZACIONES RECIENTES EN EL FLUJO DE AUDITORÍA Y ÓRDENES

### 14.1 Observaciones de Auditoría Informativas vs Requerimientos
- **Tipo de Observación:** Se incorporó el estado `INFORMACION` al enum `EstadoSolicitudAuditoria`.
- **Comportamiento en Flujo:** Al emitir una observación como *Solo Información* (`es_informativa: true`), la misma se registra con estado `INFORMACION` (color azul con badge identificatorio), **no altera el estado de la orden médica** y **no genera una llamada pendiente**. Si es una *Solicitud de Auditoría* regular, pasa la orden a `Solicitudes de auditoria` y genera la llamada obligatoria correspondiente.

### 14.2 Registro Directo de Comunicaciones y Consultas Telefónicas
- **Nuevos Tipos de Llamada:** Se extendió el catálogo `TipoLlamadaPaciente` con `CONSULTA_PACIENTE`, `SEGUIMIENTO_SUCURSAL` y `OTRO`.
- **Botón "+ Registrar Llamada" en Expediente:** Permite asentar en la pestaña de *Llamadas* del detalle de la orden cualquier comunicación entrante del paciente o seguimiento interno de la sucursal, con selección de resultado y observaciones detalladas.

### 14.3 Copago Predeterminado por Obra Social / Mutual
- **Catálogo de Mutuales:** Se agregó la columna `copago_default` en `obras_sociales` y en su interfaz de administración.
- **Carga Automática:** Al seleccionar la Obra Social en el formulario de alta de órdenes, el valor de copago se completa automáticamente con el sugerido por la mutual, manteniéndose 100% editable por el operador.

### 14.4 Validación Estricta de Campos Obligatorios
- **Alta de Pacientes:** Documento, Nombres, Apellidos y Fecha de Nacimiento son obligatorios tanto en el catálogo como en el modal inline.
- **Alta de Órdenes Médicas:** Fecha de prescripción, Paciente, Mutual, N° Afiliado / Credencial, Cantidad de recetas físicas (> 0), Sucursal emisora, Nombre de contacto, Teléfono (fijo o celular al menos uno) y Horario preferido de contacto.

### 14.5 Control de Acto Profesional Bioquímico (APB)
- Se añadió la columna booleana `abona_apb` a `ordenes_medicas`.
- Selector interactivo en el formulario de alta y en el modal de edición de la orden, visible además como badge distintivo `🧪 APB` en el expediente.


### 14.6 Resolución de Avisos Pendientes al Registrar Llamadas del Paciente
- **Flujo de Comunicación Bidireccional:** Si una orden posee un aviso pendiente (por observación de auditoría o resolución final) y el paciente se comunica con el laboratorio (`CONSULTA_PACIENTE` u otro tipo de llamada), el operador puede marcar la casilla **"Dar por comunicado el aviso y quitar de Llamadas Pendientes"** (activa por defecto en llamadas exitosas).
- **Efecto Inmediato:** Al guardar el registro, el sistema registra la conversación completa en el historial, marca `llamada_solicitud_completada = True` (o `llamada_finalizada_completada = True`), y **remueve automáticamente la orden de la bandeja de Llamadas Pendientes**, manteniendo inalterado el ciclo de vida de la orden médica.
