@echo off
cd /d "%~dp0"
title Sistema de Ordenes Medicas (Lanzador General)
echo ===================================================================
echo   INICIANDO SISTEMA DE GESTION DE ORDENES MEDICAS (LOCAL)
echo ===================================================================
echo.
echo [1/2] Levantando Servidor Backend FastAPI en segundo plano...
start "Backend FastAPI" cmd /k "cd /d ""%~dp0"" && ""%~dp0.venv\Scripts\python.exe"" ""%~dp0run_backend.py"""

echo [2/2] Levantando Frontend Vue 3 en segundo plano...
start "Frontend Vue 3" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo.
echo ===================================================================
echo  Los dos servicios se estan ejecutando en ventanas independientes.
echo  Puedes ingresar en tu navegador a: http://localhost:5173
echo  Usuario: admin
echo  Clave:   6367Angelic
echo ===================================================================
echo.
timeout /t 5
