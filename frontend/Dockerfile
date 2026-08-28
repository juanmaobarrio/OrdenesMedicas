# ==========================================
# ETAPA 1: Construcción (Build Stage)
# ==========================================
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copiar manifiestos e instalar dependencias
COPY package*.json ./
RUN npm install

# Copiar código fuente y compilar
COPY . .

# Argumento para URL base de API en tiempo de build (por defecto ruta relativa /api/v1 compatible con Nginx proxy)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ==========================================
# ETAPA 2: Servidor de Producción (Nginx)
# ==========================================
FROM nginx:alpine AS production-stage

# Copiar configuración personalizada de Nginx con soporte SPA y Reverse Proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos estáticos compilados desde la etapa de construcción
COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
