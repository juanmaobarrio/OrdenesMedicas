#!/bin/sh
set -e

echo "=== Iniciando Backend de Sistema de Órdenes Médicas ==="

# Ejecutar migraciones automáticas de Alembic
echo "Aplicando migraciones de base de datos..."
alembic upgrade head || {
    echo "Advertencia: Error al aplicar Alembic migrations. El servidor continuará e intentará inicializar mediante SQLAlchemy."
}

# Ejecutar siembra de datos iniciales
echo "Verificando / sembrando datos iniciales del sistema..."
python -m backend.app.core.seed || {
    echo "Advertencia: Error durante la siembra de datos o datos ya existentes."
}

echo "Iniciando servidor de aplicaciones Uvicorn..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --proxy-headers --forwarded-allow-ips="*"
