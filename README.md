# Sistema de Gestión de Órdenes Médicas

Plataforma integral, moderna y resiliente para la administración, auditoría médica, trazabilidad legal y seguimiento de órdenes y prescripciones médicas. Diseñada para reemplazar aplicaciones legacy con una arquitectura moderna de alta disponibilidad, tolerancia a fallos y optimizada para hardware local de bajo consumo (**ZimaBoard x86**) así como servidores VPS en la nube.

---

## 🚀 Tecnologías Principales

- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2.0 (Async ORM), Alembic, Pydantic v2, Passlib (Argon2 / Bcrypt), Python-Jose (JWT).
- **Frontend:** Vue 3 (Composition API, `<script setup lang="ts">`), Vite, PrimeVue v4, Tailwind CSS, Pinia, Vue Router 4, Axios, Chart.js.
- **Base de Datos:** PostgreSQL 16 (Alpine) con soporte transaccional estricto, índices optimizados y almacenamiento de datos dinámicos JSONB.
- **Infraestructura y Producción:** Docker & Docker Compose, Nginx Alpine (Multi-stage build con gzip y fallback SPA).

---

## 📋 Módulos y Capacidades del Sistema

1. **Gestión de Órdenes Médicas:**
   - Carga con validación de vencimiento automático según Obra Social / Mutual.
   - Control de copagos, estudios no autorizados y alerta de órdenes físicas adeudadas.
   - Ciclo de vida completo: `Ingreso`, `en Auditoria`, `Solicitudes de auditoria`, `Actualizada`, `Auditoria Finalizada`, `Dar de baja`, `Cancelada`, `Cerrada`.
2. **Módulo de Auditoría Médica:**
   - Panel de auditor para emisión de solicitudes u observaciones médicas.
   - Respuestas operativas desde sucursal con carga de adjuntos y re-evaluación.
3. **Gestión Telefónica / Llamadas a Pacientes:**
   - Registro de llamadas en hitos clave (`Solicitudes de Auditoría` y `Auditoría Finalizada`).
   - Modal rápido para registro de llamadas con visualización de deuda de receta médica.
4. **Padrón de Pacientes y Catálogo de Mutuales:**
   - Búsqueda en tiempo real por DNI, nombres y obra social.
   - Configuración de días de vencimiento por cada prestador médico.
5. **Trazabilidad Legal (Audit Trail Inmutable):**
   - Registro de cada cambio de estado, subida de documentos, observaciones, usuario responsable, IP y timestamp.
6. **Dashboard Ejecutivo y Reportes:**
   - Métricas de órdenes por estado, distribución por sucursal, porcentaje de efectividad y tendencias mensuales.
7. **Administración de Usuarios y Roles (RBAC Granular):**
   - Gestión completa de operadores, auditores y administradores.
   - Reseteo seguro de contraseñas y control de permisos por nivel jerárquico.
   - Catálogo administrable de motivos de cancelación y estados del sistema.

---

## 🛠️ Guía de Despliegue en Producción (ZimaBoard x86 / Linux)

### 1. Requisitos Previos en ZimaBoard / Servidor
- **Sistema Operativo:** CasaOS, Debian 12, Ubuntu Server 22.04/24.04, o cualquier Linux x86_64.
- **Docker:** Versión 24.0+
- **Docker Compose:** Versión 2.20+ (`docker compose` con soporte V2)
- **Git:** Instalado en el sistema (`sudo apt update && sudo apt install -y git docker.io docker-compose-plugin`)

---

### 2. Paso a Paso para Despliegue

#### Paso 1: Clonar el Repositorio desde GitHub
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git /DATA/AppData/ordenes-medicas
cd /DATA/AppData/ordenes-medicas
```

#### Paso 2: Crear el Archivo de Variables de Entorno
Copia la plantilla `.env.example` al archivo definitivo `.env`:
```bash
cp .env.example .env
```

Edita las credenciales seguras con `nano .env`:
```bash
nano .env
```
> **Nota de Seguridad:** Asegúrate de cambiar `POSTGRES_PASSWORD` y definir una `SECRET_KEY` aleatoria de más de 32 caracteres. Ajusta `APP_PORT` al puerto donde quieras acceder a la aplicación (ej: `80`, `8080` o `3000`).

#### Paso 3: Construir y Levantar los Contenedores
```bash
docker compose up -d --build
```

Docker se encargará automáticamente de:
1. Levantar el motor de base de datos **PostgreSQL 16 Alpine**.
2. Compilar el **Backend FastAPI** en Python 3.11-slim.
3. Ejecutar las migraciones de **Alembic** (`alembic upgrade head`) en la base de datos.
4. Sembrar los datos maestros iniciales (**Seed** con roles, permisos, usuario admin, mutuales y estados).
5. Compilar el **Frontend Vue 3** en una imagen de **Nginx Alpine** ultra liviana (< 15MB de consumo de RAM).

#### Paso 4: Verificar el Estado de los Servicios
```bash
docker compose ps
docker compose logs -f backend
```

---

### 3. Acceso mediante Dominio y Cloudflare (`auditorias.jmob.ar`)

El sistema está **completamente listo y optimizado** para funcionar detrás de Cloudflare (HTTPS, Cloudflare Tunnel `cloudflared` o DNS Proxy):

- **Arquitectura de Dominio Único:** El frontend Nginx y el backend FastAPI operan bajo el mismo dominio de forma transparente. Todas las llamadas a la API se realizan a través de la ruta relativa `/api/v1`, evitando cualquier bloqueo de CORS o problemas de contenido mixto (Mixed Content HTTP/HTTPS).
- **Soporte de Headers Cloudflare:** Nginx y FastAPI reenvían y reconocen automáticamente las cabeceras `CF-Connecting-IP`, `X-Forwarded-Proto` (HTTPS) y `X-Forwarded-For`.

#### Opción A: Mediante Cloudflare Tunnel (Recomendado para ZimaBoard / CasaOS)
Si utilizas **Cloudflare Tunnel (`cloudflared`)** en tu ZimaBoard:
1. En el panel de **Cloudflare Zero Trust** > **Networks** > **Tunnels** (o en la configuración local de tu túnel):
2. Agrega un **Public Hostname**:
   - **Subdominio / Dominio:** `auditorias.jmob.ar`
   - **Type (Servicio):** `HTTP`
   - **URL / Host:** `localhost:80` (o `127.0.0.1:80` o la IP de tu ZimaBoard en el puerto configurado en `APP_PORT`).
3. ¡Listo! Cloudflare se encargará automáticamente del certificado SSL/TLS y podrás ingresar a `https://auditorias.jmob.ar`.

#### Opción B: Mediante Cloudflare Proxy DNS + Nginx / Traefik / Caddy
Si apuntas el registro DNS tipo `A` o `CNAME` de `auditorias.jmob.ar` hacia la IP de tu servidor con el proxy de Cloudflare activado (nube naranja):
1. Asegúrate de que el puerto `80` (o `443`) de tu ZimaBoard esté expuesto o redirigido.
2. En Cloudflare SSL/TLS, selecciona el modo **Full** o **Flexible**.

---

### 4. Credenciales de Acceso por Defecto

Una vez que los contenedores estén en estado *healthy/running*:

- **URL de la Aplicación Web:** `http://IP_DE_TU_ZIMABOARD` (o `http://localhost:80`)
- **Usuario Administrador:** `admin`
- **Contraseña Inicial:** `admin123456`
- **Documentación Swagger API:** `http://IP_DE_TU_ZIMABOARD/docs`

> ⚠️ **Recomendación de Seguridad:** Inicia sesión con la cuenta de administrador e ingresa inmediatamente a **Usuarios > Cambiar Contraseña** para establecer una clave segura.

---

## 💾 Mantenimiento y Respaldos en ZimaBoard

### Realizar un Respaldo (Backup) de la Base de Datos PostgreSQL
```bash
docker exec -t ordenes_medicas_postgres pg_dump -U postgres ordenes_medicas_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar un Respaldo
```bash
cat backup_archivo.sql | docker exec -i ordenes_medicas_postgres psql -U postgres -d ordenes_medicas_db
```

### Reinicio y Actualización del Sistema
Para actualizar el aplicativo a la última versión de GitHub:
```bash
git pull origin main
docker compose up -d --build
```

---

## 💻 Desarrollo Local (Local Development)

### Opción A: Entorno Contenedorizado de Desarrollo
```bash
docker compose -f docker-compose.dev.yml up --build
```

### Opción B: Entorno Local Directo (FastAPI + Vite + SQLite/PostgreSQL)

#### 1. Backend (FastAPI):
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno locales (SQLite automático):
cp .env.example .env

# Ejecutar servidor de desarrollo con recarga en caliente:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend (Vue 3 + Vite):
```bash
cd frontend
npm install
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

---

## 📄 Licencia y Autores
Sistema desarrollado bajo estándares de arquitectura limpia y mejores prácticas de la industria para instituciones médicas y auditorías de salud.
