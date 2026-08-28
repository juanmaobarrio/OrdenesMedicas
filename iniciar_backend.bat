@echo off
cd /d "%~dp0"
title Backend FastAPI
echo ========================================================
echo Iniciando Backend FastAPI en http://127.0.0.1:8000
echo ========================================================
"%~dp0.venv\Scripts\python.exe" "%~dp0run_backend.py"
pause
