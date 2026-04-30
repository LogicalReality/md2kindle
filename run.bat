@echo off
set SCRIPT_DIR=%~dp0
set VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%SCRIPT_DIR%md2kindle.py" %*
) else (
    echo [WARNING] No se encontro .venv. Usando python del sistema...
    python "%SCRIPT_DIR%md2kindle.py" %*
)

if "%~1"=="" (
    echo.
    echo Pulse Enter para salir...
    pause >nul
)
