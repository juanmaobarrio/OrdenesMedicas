@echo off
cd /d "%~dp0frontend"
title Frontend Vue 3 (Ordenes Medicas)
echo ========================================================
echo Iniciando Frontend Vue 3 en http://localhost:5173
echo ========================================================
set PATH=D:\Aplicaciones\nodejs;C:\WINDOWS\system32;%PATH%
call npm run dev
pause
