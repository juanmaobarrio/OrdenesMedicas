#!/bin/sh
set -e

echo "=== Iniciando Backend de Sistema de Órdenes Médicas ==="

# Esperar activamente a que PostgreSQL esté disponible y responda
DB_HOST="${POSTGRES_SERVER:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "Esperando conexión a PostgreSQL en $DB_HOST:$DB_PORT..."
MAX_RETRIES=30
COUNT=0
while ! python -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('$DB_HOST', int('$DB_PORT'))); s.close()" 2>/dev/null; do
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "Aviso: Se superó el tiempo de espera por PostgreSQL. Continuando de todos modos..."
        break
    fi
    echo "PostgreSQL no responde aún ($COUNT/$MAX_RETRIES). Esperando 2 segundos..."
    sleep 2
done
echo "Conexión con PostgreSQL establecida correctamente."

# Ejecutar migraciones de Alembic si existe la configuración
if [ -f "backend/alembic.ini" ]; then
    echo "Aplicando migraciones de base de datos..."
    alembic -c backend/alembic.ini upgrade head || echo "Aviso: Continuando con inicialización ORM..."
elif [ -f "alembic.ini" ]; then
    alembic upgrade head || echo "Aviso: Continuando con inicialización ORM..."
fi

# Ejecutar siembra de datos iniciales y verificación de columnas
echo "Verificando / sembrando datos iniciales y columnas del sistema..."
python -m backend.app.core.migrar_columnas || true
python -m backend.app.core.seed || {
    echo "Advertencia: Error durante la siembra de datos."
}

echo "Iniciando servidor de aplicaciones Uvicorn..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --proxy-headers --forwarded-allow-ips="*"
