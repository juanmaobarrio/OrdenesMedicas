# GUÍA DE INTEGRACIÓN Y API REST PARA AUTOMATIZACIONES (n8n & WEB SERVICES)
## SISTEMA DE GESTIÓN DE ÓRDENES MÉDICAS

---

## 1. INTRODUCCIÓN Y ARQUITECTURA DE INTEGRACIÓN

Este documento proporciona las especificaciones técnicas completas para consumir la API REST del **Sistema de Gestión de Órdenes Médicas** desde servicios externos, scripts y herramientas de automatización como **n8n**.

### 💡 Filosofía de Automatización Externa con n8n
Para mantener el núcleo de la aplicación simple, resiliente y de alto rendimiento:
- **Tareas de Web Scraping y control de portales de mutuales externas:** Se delegan a workflows en **n8n**, que luego actualizan el estado de las órdenes en este sistema mediante la API REST.
- **Envío masivo o programado de Emails / WhatsApp:** Se ejecutan en **n8n**, consultando las bandejas pendientes de este sistema y registrando la trazabilidad del contacto a través de la API.

---

## 2. ENTORNO Y URLS BASE

| Entorno | Base URL | OpenAPI / Swagger Docs |
|---|---|---|
| **Desarrollo Local** | `http://127.0.0.1:8000/api/v1` | `http://127.0.0.1:8000/docs` |
| **Producción / VPS** | `https://tu-dominio.com/api/v1` | `https://tu-dominio.com/docs` |

Todas las respuestas de la API utilizan formato **JSON** con codificación **UTF-8**.

---

## 3. AUTENTICACIÓN Y SEGURIDAD (JWT TOKENS)

Todas las rutas protegidas requieren enviar un **Bearer Token JWT** en la cabecera HTTP:
```http
Authorization: Bearer <ACCESS_TOKEN>
```

### 3.1 Obtener Token de Acceso (Login)
- **Endpoint:** `POST /api/v1/auth/login`
- **Content-Type:** `application/json` o `application/x-www-form-urlencoded`
- **Acceso:** Público

#### Request Body:
```json
{
  "username_or_email": "admin",
  "password": "admin123456"
}
```

#### Response (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

> **💡 Configuración recomendada en n8n:**
> 1. Crear un nodo **HTTP Request** inicial de autenticación que haga `POST /api/v1/auth/login`.
> 2. Guardar el `access_token` en el contexto del flujo o usar la opción **Generic Credential Type: Header Auth** con nombre `Authorization` y valor `Bearer {{$json.access_token}}`.
> 3. El token tiene una validez predeterminada de 60 minutos.

---

## 4. DICCIONARIO DE ESTADOS Y REGLAS DE NEGOCIO

### 4.1 Estados del Ciclo de Vida y sus IDs Numéricos para API / n8n
| ID | Código | Nombre del Estado | Tipo | Requiere Motivo / Observación |
|---|---|---|---|---|
| **1** | `INGRESO` | `Ingreso` | Proceso | No |
| **2** | `EN_AUDITORIA` | `en Auditoria` | Proceso | No |
| **3** | `SOLICITUDES_AUDITORIA` | `Solicitudes de auditoria` | Proceso | No (entra a llamadas pendientes) |
| **4** | `ACTUALIZADA` | `Actualizada` | Proceso | No |
| **5** | `AUDITORIA_FINALIZADA` | `Auditoria Finalizada` | Proceso | **Sí: observación de resultado** (entra a llamadas pendientes) |
| **6** | `DAR_DE_BAJA` | `Dar de baja` | Finalización | **Sí: motivo obligatorio** |
| **7** | `CANCELADA` | `Cancelada` | Finalización | **Sí: motivo obligatorio** |
| **8** | `CERRADA` | `Cerrada` | Finalización | No (Resolución exitosa definitiva: paciente atendido) |

> **💡 Consejo para n8n:** Al cambiar el estado de una orden médica, puedes enviar directamente el campo numérico `"estado_id": 5` en lugar del texto del estado. Esto hace que tus automatizaciones sean inmunes a cambios de nombres o descripciones.

---

## 5. CATÁLOGO DE ENDPOINTS PRINCIPALES

### 5.1 Gestión de Órdenes Médicas

#### A. Listar Órdenes con Filtros
- **Endpoint:** `GET /api/v1/ordenes`
- **Parámetros Query (Opcionales):**
  - `estado`: Filtrar por estado (`Ingreso`, `en Auditoria`, `Solicitudes de auditoria`, `Actualizada`, `Auditoria Finalizada`, `Dar de baja`, `Cancelada`, `Cerrada`)
  - `mutual`: Filtrar por sigla de obra social (ej: `OSDE`, `PAMI`, `SM`)
  - `search`: Búsqueda por número de orden, DNI o nombre del paciente
  - `sucursal_id`: UUID de la sucursal
  - `fecha_desde` / `fecha_hasta`: Formato `YYYY-MM-DD`
  - `skip` (default 0), `limit` (default 50)

```bash
# Ejemplo cURL: Buscar órdenes en Auditoría para procesar en n8n
curl -X GET "http://127.0.0.1:8000/api/v1/ordenes?estado=en%20Auditoria&limit=100" \
  -H "Authorization: Bearer <TOKEN>"
```

#### B. Obtener Detalle Completo de una Orden
- **Endpoint:** `GET /api/v1/ordenes/{id}`
- Retorna la ficha del paciente, sucursal, números de auditoría, adjuntos, observaciones, llamadas registradas, bitácora y la **información completa de la mutual vinculada** (`mutual_data`, `mutual_id`, `mutual_codigo_externo`).

**Ejemplo de respuesta con datos de mutual:**
```json
{
  "id": "298d862f-2e26-437b-98bc-d117c0de6247",
  "nro_orden": "ORD-2026-000022",
  "estado": "Ingreso",
  "mutual": "IOMA",
  "mutual_id": "d764f156-4821-4c50-8de4-3c250427d752",
  "mutual_codigo_externo": "EXT-IOMA",
  "mutual_data": {
    "id": "d764f156-4821-4c50-8de4-3c250427d752",
    "codigo": "IOMA",
    "sigla": "IOMA",
    "nombre": "Instituto de Obra Medico Asistencial",
    "codigo_externo": "EXT-IOMA",
    "display_name": "IOMA - Instituto de Obra Medico Asistencial",
    "dias_vencimiento": 60,
    "copago_default": 6500.00,
    "porcentaje_cobertura_apb": 0.00
  }
}
```

#### C. Crear una Nueva Orden Médica
- **Endpoint:** `POST /api/v1/ordenes`
- **Campos Obligatorios:** `paciente_id`, `sucursal_id`, `fecha_prescripcion`, `cantidad_ordenes_fisicas` (>0), `mutual`, `nro_afiliado`, `contacto_nombre`, `contacto_horario`, y al menos un teléfono (`contacto_telefono` o `contacto_celular`).
- **Request Body:**
```json
{
  "paciente_id": "8a719bb8-41be-4b95-a226-9d8a55e1db0b",
  "sucursal_id": "e67e3a9c-0c3a-4467-bc18-eb34d168346f",
  "fecha_prescripcion": "2026-08-27",
  "cantidad_ordenes_fisicas": 1,
  "mutual": "OSDE",
  "nro_afiliado": "12345678/01",
  "valor_copago": 2500.00,
  "valor_estudios_no_autorizados": 0,
  "abona_apb": true,
  "valor_apb": 0,
  "ya_se_atendio": true,
  "monto_abonado_atencion": 15000.00,
  "fecha_vencimiento": "2026-09-26",
  "numeros_auditoria": ["AUT-1002", "AUT-1003"],
  "debe_orden_medica": true,
  "contacto_nombre": "Laura Martínez",
  "contacto_horario": "Por la mañana",
  "contacto_telefono": "1166778899",
  "contacto_celular": "1166778899",
  "contacto_email": "paciente@correo.com",
  "observaciones_ingreso": "Paciente con cirugía programada el próximo lunes."
}
```

#### D. Actualizar Datos de una Orden Médica
- **Endpoint:** `PUT /api/v1/ordenes/{id}`
- **Permiso requerido:** `ordenes:update`
- **Regla Especial de Jerarquía:** Los campos `cantidad_ordenes_fisicas` y `sucursal_id` únicamente pueden ser modificados por usuarios con un nivel jerárquico **superior a 30** (`hierarchy_level > 30`, como Auditores o Administradores). Si un usuario estándar intenta modificarlos, la API responderá con `HTTP 403 Forbidden`.
- **Request Body (Campos opcionales):**
```json
{
  "cantidad_ordenes_fisicas": 2,
  "sucursal_id": "e67e3a9c-0c3a-4467-bc18-eb34d168346f",
  "mutual": "OSDE",
  "valor_copago": 3000.00,
  "ya_se_atendio": true,
  "monto_abonado_atencion": 12000.00,
  "contacto_telefono": "1144556677",
  "debe_orden_medica": false
}
```

#### E. Cambiar Estado del Ciclo de Vida (Por ID o por Nombre)
- **Endpoint:** `POST /api/v1/ordenes/{id}/estado`
- **Casos de Uso Principales (Soporta `estado_id` numérico o `nuevo_estado` en texto):**

**1. Marcar como "Auditoria Finalizada" (Aprobada) usando `estado_id: 5` (permite ajustar copago y no autorizados):**
```json
{
  "estado_id": 5,
  "observacion_resultado": "Auditoría Aprobada 100%. Se autorizan las 3 prácticas sin copago.",
  "valor_copago": 1500.00,
  "valor_estudios_no_autorizados": 0.00
}
```

**2. Marcar como "Cancelada" usando `estado_id: 7` (con motivo obligatorio):**
```json
{
  "estado_id": 7,
  "motivo": "Orden Vencida - La prescripción médica superó los 30 días de vigencia"
}
```

**3. Marcar como "Cerrada" usando `estado_id: 8` (Paciente atendido con éxito):**
```json
{
  "estado_id": 8
}
```

**4. Marcar como "Dar de baja" usando `estado_id: 6`:**
```json
{
  "estado_id": 6,
  "motivo": "Baja por error de carga en recepción"
}
```

#### E. Emitir Observación del Auditor
- **Endpoint:** `POST /api/v1/ordenes/{id}/solicitudes`
- **Tipos de Observación:**
  - **Solicitud de Auditoría (`es_informativa: false`):** Pasa la orden a `Solicitudes de auditoria` y la incorpora a la bandeja de llamadas pendientes para contactar al paciente.
  - **Solo Información (`es_informativa: true`):** Queda con estado `INFORMACION` (color azul en el expediente), **no altera el estado de la orden** y **no genera llamada pendiente**.

```json
{
  "motivo_solicitud": "Falta diagnóstico presuntivo",
  "mensaje_auditor": "El médico solicitante debe aclarar diagnóstico para autorizar la práctica 66001.",
  "es_informativa": false
}
```

#### F. Responder Observación del Auditor
- **Endpoint:** `POST /api/v1/ordenes/solicitudes/{solicitud_id}/responder`
- Pasa la orden automáticamente al estado `Actualizada`.
```json
{
  "respuesta_operador": "Se adjuntó nuevo resumen clínico firmado por el especialista."
}
```

### 5.2 Bandeja de Llamadas Pendientes a Pacientes

#### A. Consultar Pacientes que Requieren Aviso
- **Endpoint:** `GET /api/v1/ordenes/llamadas-pendientes`
- **Query Params:** `sucursal_id` (opcional).
- **Retorna:** Lista de órdenes en `Solicitudes de auditoria` o `Auditoria Finalizada` que aún no tienen aviso exitoso registrado.
- **Campos devueltos útiles para n8n:**
  - `nro_orden`, `paciente_nombre`, `paciente_telefono`, `contacto_email`, `contacto_horario`
  - `tipo_llamada_requerida`: `SOLICITUD_AUDITORIA` o `AUDITORIA_FINALIZADA`
  - `observacion_resultado_auditoria`: Mensaje de resolución del auditor
  - `solicitudes_pendientes`: Lista de observaciones detalladas del auditor

#### B. Registrar Resultado de la Notificación / Llamada / Consulta Directa
- **Endpoint:** `POST /api/v1/ordenes/{id}/registrar-llamada`
- **Tipos de Llamada (`tipo_llamada`):**
  - `SOLICITUD_AUDITORIA`: Aviso al paciente sobre requerimiento médico.
  - `AUDITORIA_FINALIZADA`: Aviso al paciente sobre aprobación/resolución médica.
  - `CONSULTA_PACIENTE`: Consulta entrante del paciente hacia el laboratorio.
  - `SEGUIMIENTO_SUCURSAL`: Seguimiento interno de la sucursal.
  - `OTRO`: Otro motivo de comunicación.
- **Resolución de Avisos Pendientes:** Si `completar_aviso_pendiente: true` y el resultado es `EXITOSA`, el sistema **da por cumplido cualquier aviso pendiente y remueve la orden de la bandeja de Llamadas Pendientes**.

```json
{
  "tipo_llamada": "CONSULTA_PACIENTE",
  "resultado": "EXITOSA",
  "observaciones": "El paciente llamó consultando por el estado. Se le informó la observación del auditor y se comprometió a acercar la documentación.",
  "completar_aviso_pendiente": true
}
```

Valores válidos para `resultado`:
- `EXITOSA`: Contacto efectivo (remueve de la bandeja de pendientes si correspondía).
- `NO_CONTESTA`: No respondió (permanece en pendientes para reintentar).
- `NUMERO_ERRONEO`: Teléfono inválido.
- `REINTENTAR`: Solicita nuevo intento.

---

### 5.3 Gestión de Pacientes

#### A. Buscar Paciente por DNI
- **Endpoint:** `GET /api/v1/pacientes/documento/{documento}`

#### B. Registrar Paciente
- **Endpoint:** `POST /api/v1/pacientes`
- **Campos Obligatorios:** `documento`, `nombres`, `apellidos`, `fecha_nacimiento` (Formato `YYYY-MM-DD`).
```json
{
  "documento": "40123456",
  "nombres": "Carlos",
  "apellidos": "GÓMEZ",
  "fecha_nacimiento": "1995-04-12",
  "obra_social": "OSDE",
  "nro_afiliado": "2-887766-01",
  "telefono": "1144556677",
  "email": "carlos.gomez@correo.com",
  "is_active": true
}
```

---

### 5.4 Adjuntos y Documentación

#### A. Subir Archivo Adjunto (Prescripción, Receta o Foto)
- **Endpoint:** `POST /api/v1/ordenes/{id}/adjuntos`
- **Content-Type:** `multipart/form-data`
- **Parámetro Form:** `file` (Formatos admitidos: `.pdf`, `.png`, `.jpg`, `.jpeg`).

#### B. Descargar / Visualizar Archivo
- **Endpoint:** `GET /api/v1/ordenes/adjuntos/{adjunto_id}/descargar`

---

### 5.5 Catálogos y Configuración

#### A. Obras Sociales / Mutuales
- `GET /api/v1/mutuales?only_active=true`
- `POST /api/v1/mutuales`
  - Body: `{ "codigo": "OSDE", "sigla": "OSDE", "nombre": "OSDE Binario", "dias_vencimiento": 30, "copago_default": 2500.00, "activa": true }`
- `PUT /api/v1/mutuales/{id}`
  - Body: `{ "nombre": "OSDE Binario", "dias_vencimiento": 30, "copago_default": 3000.00 }`
- `PATCH /api/v1/mutuales/{id}/toggle-active`

#### B. Motivos de Cancelación
- `GET /api/v1/config/motivos-cancelacion?only_active=true`
- `POST /api/v1/config/motivos-cancelacion`
- `PUT /api/v1/config/motivos-cancelacion/{id}`
- `PATCH /api/v1/config/motivos-cancelacion/{id}/toggle-active`

#### C. Estados del Sistema (con ID Numérico para n8n)
- `GET /api/v1/config/estados?only_active=true`
- `POST /api/v1/config/estados`
- `PUT /api/v1/config/estados/{id}`
- `PATCH /api/v1/config/estados/{id}/toggle-active`

#### D. Indicaciones Clínicas de Estudios
- `GET /api/v1/config/indicaciones?only_active=true`
- `POST /api/v1/config/indicaciones`
- `POST /api/v1/config/indicaciones/reorder`
  - Body: `{ "items": [{ "id": "uuid", "orden_secuencia": 1 }, { "id": "uuid", "orden_secuencia": 2 }] }`
- `PUT /api/v1/config/indicaciones/{id}`
- `DELETE /api/v1/config/indicaciones/{id}`

#### E. Roles y Permisos (RBAC)
- `GET /api/v1/roles` (listar roles)
- `GET /api/v1/permissions` (listar catálogo de permisos atómicos)
- `POST /api/v1/roles` (crear rol con lista de `permission_ids`)
- `PUT /api/v1/roles/{id}` (editar rol y permisos)
- `DELETE /api/v1/roles/{id}` (eliminar rol)

---

## 6. WORKFLOWS Y BLUEPRINTS PARA n8n

A continuación se detallan los 2 flujos más comunes para automatizar con n8n:

### 🤖 Workflow 1: Control Periódico de Auditorías en Portales de Mutuales Externas
```text
[Cron / Schedule Trigger (cada 15 min)]
   │
   ▼
[HTTP Request (Login API)] ────────► Obtiene access_token
   │
   ▼
[HTTP Request (GET /ordenes?estado=en Auditoria)] ──► Lista órdenes esperando resolución
   │
   ▼
[Loop / Split in Batches]
   │
   ▼
[Web Scraping / HTTP Request a Portal de la Mutual Externa (ej: OSDE / PAMI)]
   │
   ├──► [¿Aprobada?] ──► [HTTP Request (POST /ordenes/{id}/estado)]
   │                       Body: { "nuevo_estado": "Auditoria Finalizada", "observacion_resultado": "Autorizada por web service de mutual..." }
   │
   ├──► [¿Observada?] ─► [HTTP Request (POST /ordenes/{id}/solicitudes)]
   │                       Body: { "motivo_solicitud": "Rechazo documental", "mensaje_auditor": "El portal de la mutual solicita..." }
   │
   └──► [¿Rechazada?] ─► [HTTP Request (POST /ordenes/{id}/estado)]
                           Body: { "nuevo_estado": "Cancelada", "motivo": "Rechazada por la mutual" }
```

---

### 📧 Workflow 2: Envío Automático de Mails / WhatsApp y Registro de Llamada
```text
[Cron / Schedule Trigger (cada 10 min)]
   │
   ▼
[HTTP Request (GET /ordenes/llamadas-pendientes)] ──► Obtiene pacientes que requieren aviso
   │
   ▼
[Loop / Item Lists]
   │
   ▼
[Send Email Node (SMTP/SendGrid) o WhatsApp API] ──► Envía notificación con los datos de la orden
   │
   ▼
[HTTP Request (POST /ordenes/{id}/registrar-llamada)]
   Body: {
     "tipo_llamada": "{{$json.tipo_llamada_requerida}}",
     "resultado": "EXITOSA",
     "observaciones": "Email de aviso enviado automáticamente a {{$json.contacto_email}}"
   }
   (La orden desaparece automáticamente de pendientes sin alterar su estado)
```

---

## 7. CÓDIGOS DE ESTADO HTTP Y MANEJO DE ERRORES

| Código HTTP | Significado | Causa común |
|---|---|---|
| `200 OK` | Operación exitosa | Consulta o actualización correcta. |
| `201 Created` | Recurso creado | Alta de orden, paciente, solicitud o adjunto. |
| `400 Bad Request` | Validación de negocio | Falta motivo al cancelar orden o datos obligatorios. |
| `401 Unauthorized` | No autenticado | Token ausente, expirado o inválido. |
| `403 Forbidden` | Acceso denegado | Rol insuficiente o intento de modificar orden cerrada/cancelada. |
| `404 Not Found` | No encontrado | ID de orden, paciente o adjunto inexistente. |
| `409 Conflict` | Conflicto de unicidad | DNI o Código duplicado. |
| `422 Unprocessable` | Error de esquema | Tipos de datos inválidos en el payload JSON. |


---

### 5.6 Desglose de Estudios y Calculadora de Presupuestos (Integración n8n / Externa)

Las órdenes médicas soportan el desglose individual de prácticas con su código, nombre, precio y estado de autorización (`true` si fue cubierta por la mutual, `false` si es rechazada/a cargo del paciente).

#### A. Actualizar Desglose de Estudios con un solo Request (Recomendado para n8n)
- **Endpoint:** `PUT /api/v1/ordenes/{id}/estudios-detalle`
- **Sincronización Automática Inteligente:** Al enviar este desglose, el backend:
  1. Almacena la estructura completa para la **Calculadora de Estudios**.
  2. Auto-deriva la lista `estudios_autorizados` (nombres donde `autorizado = true`).
  3. Auto-deriva la lista `estudios_no_autorizados` (nombres donde `autorizado = false`).
  4. Auto-calcula la suma de precios no autorizados en `valor_estudios_no_autorizados`.

**Formato 1: Objeto JSON con clave `estudios_detalle`:**
```json
{
  "estudios_detalle": [
    {
      "codigo": "660001",
      "nombre": "Hemograma completo",
      "precio": 0,
      "autorizado": true
    },
    {
      "codigo": "660450",
      "nombre": "Vitamina D3 (25-OH)",
      "precio": 15400.00,
      "autorizado": false
    },
    {
      "codigo": "660720",
      "nombre": "Hepatograma",
      "precio": 0,
      "autorizado": true
    },
    {
      "codigo": "660890",
      "nombre": "Anticuerpos Anti-TPO",
      "precio": 9800.00,
      "autorizado": false
    }
  ]
}
```

**Formato 2: Array directo JSON (también soportado):**
```json
[
  { "codigo": "660001", "nombre": "Hemograma completo", "precio": 0, "autorizado": true },
  { "codigo": "660450", "nombre": "Vitamina D3 (25-OH)", "precio": 15400.00, "autorizado": false }
]
```

#### B. Enviar Desglose en la Creación de la Orden
- **Endpoint:** `POST /api/v1/ordenes`
- Puede incluir la clave `"estudios_detalle": [...]` en el payload principal.

#### C. Enviar Desglose al Finalizar Auditoría o Cambiar Estado
- **Endpoint:** `POST /api/v1/ordenes/{id}/estado`
- Permite enviar conjuntamente `"estado_id": 5` (o `"nuevo_estado": "Auditoria Finalizada"`), `"observacion_resultado"` y `"estudios_detalle": [...]`.


---

### 5.7 Feature Flags y Control de Funcionalidades del Sistema

El sistema cuenta con un conmutador de funcionalidades (Feature Flags) persistido en la base de datos y administrable vía API o desde la interfaz web.

#### A. Consultar Estado de Funcionalidades Activas
- **Endpoint:** `GET /api/v1/config/features`
- **Response Body:**
```json
{
  "modulo_mail": false,
  "calculadora_estudios": false,
  "estudios_autorizacion": false,
  "indicaciones_estudios": false,
  "asignar_auditor": false,
  "atencion_previa": false,
  "reportes_estadisticas": false
}
```

#### B. Actualizar Funcionalidades (Solo Administradores)
- **Endpoint:** `PUT /api/v1/config/features`
- **Request Body (Permite actualización parcial o total):**
```json
{
  "modulo_mail": true,
  "calculadora_estudios": true
}
```
- **Campos Disponibles:**
  - `modulo_mail` (boolean): Activa el módulo de despacho de emails ZeptoMail y plantillas.
  - `calculadora_estudios` (boolean): Activa el botón y modal de la calculadora de presupuesto de estudios.
  - `estudios_autorizacion` (boolean): Activa los campos de prácticas autorizadas, no autorizadas y aranceles particulares.
  - `indicaciones_estudios` (boolean): Activa el selector y gestión de indicaciones clínicas de preparación.
  - `asignar_auditor` (boolean): Activa la vinculación y filtros de auditor médico en las órdenes.
  - `atencion_previa` (boolean): Activa el control de paciente ya atendido/abonado, banners de reintegro y alertas en bandeja de llamadas.
  - `reportes_estadisticas` (boolean): Activa el generador avanzado de reportes, estadísticas multidimensionales e impresión PDF (solo Admin).

---

### 5.8 Motor de Reportes y Estadísticas Configurables (Exclusivo Administrador)

- **Endpoint:** `POST /api/v1/dashboard/reportes/ejecutar`
- **Permiso / Rol:** Exclusivo rol `ADMIN`
- **Request Body:**
```json
{
  "preset": "tasa_rechazo",
  "dimension_primaria": "mutual",
  "dimension_secundaria": "tiempo",
  "agrupacion_tiempo": "mes",
  "fecha_desde": "2026-06-01",
  "fecha_hasta": "2026-09-04",
  "mutuales": ["OSDE", "SWISS MEDICAL"],
  "solo_con_reintegro": false
}
```
- **Campos del Request:**
  - `preset` (opcional): `"ordenes_tiempo"`, `"motivos_cancelacion"`, `"tasa_rechazo"`, `"financiero_reintegros"`.
  - `dimension_primaria`: `"mutual"`, `"tiempo"`, `"motivo_cancelacion"`, `"sucursal"`, `"estado"`.
  - `dimension_secundaria` (opcional): Cruce analítico secundario.
  - `agrupacion_tiempo`: `"mes"`, `"semana"`, `"dia"`, `"anio"`.
  - `fecha_desde` / `fecha_hasta`: Filtro por fecha de prescripción (formato `YYYY-MM-DD`).
  - `mutuales` (array opcional): Filtro por siglas de obras sociales.
  - `solo_con_reintegro` (boolean opcional): Filtrar órdenes de pacientes que ya se atendieron.

---

### 5.9 Plantilla de Correo, Variables Dinámicas y Aviso de Orden Médica Física
El correo de resolución de auditoría se genera con la plantilla predeterminada o con cualquier plantilla personalizada del catálogo (`plantillas_email`).

#### A. Previsualizar el Correo Generado
- **Endpoint:** `GET /api/v1/ordenes/{id}/preview-email`
- **Response Body (extracto):**
```json
{
  "destinatario_email": "paciente@correo.com",
  "destinatario_nombre": "Laura Martínez",
  "asunto": "Resolución de Auditoría Médica - Orden N° ORD-2026-000021",
  "cuerpo_html": "<!DOCTYPE html>...",
  "tiene_email": true,
  "ya_enviado": false,
  "mail_enviado_fecha": null,
  "plantilla_id": "uuid-de-la-plantilla-default",
  "plantillas_disponibles": [],
  "debe_orden_medica": true
}
```
- El campo `debe_orden_medica` refleja el flag homónimo de la orden y permite a las integraciones externas saber si el aviso de receta física fue incluido en el cuerpo.

#### B. Variables Dinámicas Soportadas en Plantillas
| Variable | Contenido |
|---|---|
| `{{paciente_nombre}}` | Nombre y apellido del paciente o persona de contacto. |
| `{{nro_orden}}` | Identificador de la orden (ej: `ORD-2026-000001`). |
| `{{mutual}}` | Obra Social / Prepaga aplicada. |
| `{{observacion_resultado}}` | Dictamen médico de la resolución de auditoría. |
| `{{copago}}` | Importe del copago / bono mutual. |
| `{{estudios_no_autorizados_valor}}` | Suma de prácticas no autorizadas. |
| `{{valor_apb}}` | Importe del Acto Profesional Bioquímico. |
| `{{total_abonar}}` | Total a abonar (Copago + No autorizados + APB). |
| `{{estudios_autorizados}}` | Listado de prácticas autorizadas. |
| `{{estudios_no_autorizados}}` | Listado de prácticas a cargo del paciente. |
| `{{indicaciones}}` | Indicaciones de preparación clínica consolidadas. |
| `{{sucursal_nombre}}` | Sede emisora de la orden. |
| `{{debe_orden_medica}}` | **Recuadro naranja de advertencia** que recuerda al paciente traer la orden médica física original. Se renderiza **solo si la orden tiene marcada la deuda de receta física**; en caso contrario el marcador se reemplaza por cadena vacía y el recuadro no aparece. |
| `{{aviso_orden_fisica}}` | Alias equivalente del anterior, para nombres semánticos en plantillas personalizadas. |

> **💡 Consejo para n8n:** si tu workflow arma el correo por fuera del sistema (SMTP / SendGrid / WhatsApp), consultá `debe_orden_medica` en `GET /api/v1/ordenes/{id}` y agregá el recordatorio de la receta física en el mensaje. El flag también viene incluido en la bandeja de llamadas (`GET /api/v1/ordenes/llamadas-pendientes`), lo que permite ramificar el texto del aviso automático según corresponda.

#### C. Obtener el Código HTML Base de la Plantilla
- **Endpoint:** `GET /api/v1/config/plantillas-email-codigo-base`
- Devuelve el HTML corporativo oficial con todos los marcadores, incluyendo `{{debe_orden_medica}}`.

---

#### D. Aviso de Orden Médica Física Adeudada en el Correo de Resolución

Cuando la orden tiene marcado el flag `debe_orden_medica` (el paciente recibió la prescripción de forma digital y **adeuda la receta física original**), el correo de resolución de auditoría incluye un **recuadro de advertencia** recordándole que debe traer la orden original el día de la toma de muestra.

- **Ubicación:** inmediatamente después del bloque de *Indicaciones de Preparación* y antes del aviso de *Comunicación Directa*.
- **Diseño:** fondo ámbar (`#fff7ed`), borde naranja de 2px con barra lateral de 6px (`#ea580c`), título con ícono ⚠️ y frases clave en negrita.
- **Condicional:** si `debe_orden_medica = false`, el marcador se reemplaza por **cadena vacía** y el recuadro no se renderiza (no queda hueco ni borde residual).

**Variables dinámicas equivalentes disponibles en el gestor de plantillas:**

| Marcador | Contenido |
|---|---|
| `{{debe_orden_medica}}` | Recuadro HTML completo de advertencia, o cadena vacía si la orden no adeuda la receta física. |
| `{{aviso_orden_fisica}}` | Alias del anterior (misma salida), para nombres semánticos en plantillas personalizadas. |

**Implementación:**
- `generar_plantilla_email_resolucion()` acepta el parámetro `debe_orden_medica: bool`. El bloque se inyecta tanto en el diseño corporativo por defecto como en el diccionario de reemplazo de plantillas personalizadas.
- `build_preview_email()` y `enviar_email_resolucion()` pasan `bool(orden.debe_orden_medica)`. El preview expone el campo `debe_orden_medica` en `PreviewEmailResolucionRead`.
- `EmailResolucionModal.vue` resuelve ambos marcadores al cambiar de plantilla.
- `migrate_plantilla_aviso_orden_fisica()` en `backend/app/main.py`: migración **aditiva e idempotente** ejecutada al arrancar para **SQLite y PostgreSQL**, que inyecta el bloque en la plantilla `DEFAULT` ya persistida. **No modifica** plantillas personalizadas por el usuario.

---

### 5.10 Nombre del Usuario que Imprime las Indicaciones

El documento de impresión de indicaciones clínicas muestra el **nombre de pila del usuario que emite la impresión**, en el encabezado, inmediatamente debajo del número de orden (por política institucional **no se incluye el apellido**).

- **Marcador de plantilla:** `{{usuario_nombre}}`, disponible en el editor de la plantilla de impresión (`/configuracion`) y documentado en el popup de variables.
- **Origen del dato:** propiedad `nombre_pila` del modelo `User` (`backend/app/modules/users/models.py`), que devuelve `first_name` y cae a `username` y luego a `"Sistema"` si no hubiera nombre cargado.
- **Endpoint:** `GET /api/v1/ordenes/{id}/imprimir-indicaciones-data` y `POST /api/v1/ordenes/imprimir-indicaciones-preview` devuelven `usuario_nombre` y lo inyectan en el HTML ensamblado.
- **Frontend:** `ImpresionIndicacionesModal.vue` resuelve el marcador en los reemplazos locales; `ordenes.service.ts` tipa `usuario_nombre` en ambas respuestas.
- **Validación:** verificado end-to-end contra la API — el encabezado renderiza `Orden N°: ORD-2026-000021` seguido de `Impreso por: Administrador`, sin filtrar el apellido. Captura: `impresion_header_usuario.png`.
