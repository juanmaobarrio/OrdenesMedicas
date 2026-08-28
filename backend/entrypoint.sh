#!/bin/sh
set -e

echo "=== Iniciando Backend de Sistema de Órdenes Médicas ==="

# Ejecutar migraciones de Alembic si existe la configuración
if [ -f "backend/alembic.ini" ]; then
    echo "Aplicando migraciones de base de datos..."
    alembic -c backend/alembic.ini upgrade head || echo "Aviso: Continuando con inicialización ORM..."
elif [ -f "alembic.ini" ]; then
    alembic upgrade head || echo "Aviso: Continuando con inicialización ORM..."
fi

# Ejecutar siembra de datos iniciales
echo "Verificando / sembrando datos iniciales del sistema..."
python -m backend.app.core.seed || {
    echo "Advertencia: Error durante la siembra de datos."
}

echo "Iniciando servidor de aplicaciones Uvicorn..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --proxy-headers --forwarded-allow-ips="*"
