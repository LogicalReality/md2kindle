@echo off
title MangaDex to Kindle (md2kindle)
color 0A

:: Asegurar que el script se ejecute en el directorio actual donde esta el .bat
cd /d "%~dp0"

echo ===================================================
echo Iniciando el Script de MangaDex a Kindle
echo ===================================================
echo.

python md2kindle.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul
