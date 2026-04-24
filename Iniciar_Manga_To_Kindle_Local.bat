@echo off
title MangaDex to Kindle (md2kindle)
color 0A

:: Asegurar que el script se ejecute en el directorio actual donde esta el .bat
cd /d "%~dp0"

echo ===================================================
echo  MangaDex to Kindle Converter  ^|  md2kindle v1.0
echo ===================================================
echo.

:: Activar virtual environment si existe
if exist ".venv\Scripts\activate.bat" (
    echo [+] Activando virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [!] No se encontro .venv, usando Python del sistema
)

:: Verificar que el paquete esta disponible antes de lanzar
.venv\Scripts\python.exe -c "import md2kindle" 2>nul
if errorlevel 1 (
    echo.
    echo [!] ERROR: El paquete md2kindle no se encontro en el entorno.
    echo     Asegurate de que .venv exista y tenga las dependencias instaladas.
    echo     Ejecuta: pip install -r requirements.txt
    echo.
    pause >nul
    exit /b 1
)

echo.
.venv\Scripts\python.exe md2kindle.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul
