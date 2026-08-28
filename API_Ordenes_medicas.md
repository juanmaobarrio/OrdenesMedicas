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
- Retorna la ficha del paciente, sucursal, números de auditoría, adjuntos, observaciones, llamadas registradas y bitácora.

#### C. Crear una Nueva Orden Médica
- **Endpoint:** `POST /api/v1/ordenes`
- **Request Body:**
```json
{
  "paciente_id": "8a719bb8-41be-4b95-a226-9d8a55e1db0b",
  "sucursal_id": "e67e3a9c-0c3a-4467-bc18-eb34d168346f",
  "fecha_prescripcion": "2026-08-27",
  "cantidad_ordenes_fisicas": 1,
  "mutual": "OSDE",
  "valor_copago": 0,
  "valor_estudios_no_autorizados": 0,
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

#### D. Cambiar Estado del Ciclo de Vida (Por ID o por Nombre)
- **Endpoint:** `POST /api/v1/ordenes/{id}/estado`
- **Casos de Uso Principales (Soporta `estado_id` numérico o `nuevo_estado` en texto):**

**1. Marcar como "Auditoria Finalizada" (Aprobada) usando `estado_id: 5`:**
```json
{
  "estado_id": 5,
  "observacion_resultado": "Auditoría Aprobada 100%. Se autorizan las 3 prácticas sin copago."
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
- Pasa la orden automáticamente al estado `Solicitudes de auditoria` y la incorpora a la bandeja de llamadas.
```json
{
  "motivo_solicitud": "Falta diagnóstico",
  "mensaje_auditor": "El médico solicitante debe aclarar diagnóstico presuntivo para autorizar la práctica 66001."
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

#### B. Registrar Resultado de la Notificación / Llamada
- **Endpoint:** `POST /api/v1/ordenes/{id}/registrar-llamada`
- **Nota importante:** Registrar una llamada exitosa **saca la orden de la lista de llamadas pendientes**, pero **no altera el estado de la orden médica**.

```json
{
  "tipo_llamada": "AUDITORIA_FINALIZADA",
  "resultado": "EXITOSA",
  "observaciones": "Notificación enviada automáticamente por workflow n8n vía Email y WhatsApp."
}
```

Valores válidos para `resultado`:
- `EXITOSA`: Contacto efectivo (remueve de la bandeja de pendientes).
- `NO_CONTESTA`: No respondió (permanece en pendientes para reintentar).
- `NUMERO_ERRONEO`: Teléfono inválido.
- `REINTENTAR`: Solicita nuevo intento.

---

### 5.3 Gestión de Pacientes

#### A. Buscar Paciente por DNI
- **Endpoint:** `GET /api/v1/pacientes/documento/{documento}`

#### B. Registrar Paciente
- **Endpoint:** `POST /api/v1/pacientes`
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
- `PUT /api/v1/mutuales/{id}`
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

#### D. Roles y Permisos (RBAC)
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
