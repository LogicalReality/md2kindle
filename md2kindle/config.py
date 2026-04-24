"""Configuración central, constantes y detección de rutas."""

import os
import re
import shutil

IS_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

# ==========================================
# CONFIGURACIÓN
# ==========================================
# Configuración de Rutas (Detección en Cascada)
# Subimos un nivel porque este archivo vive en md2kindle/config.py
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Buscar en la raíz del proyecto (Modo Portable)
MANGADEX_LOCAL = os.path.join(SCRIPT_DIR, "mangadex-dl", "mangadex-dl.exe")
KCC_LOCAL = os.path.join(SCRIPT_DIR, "kcc_c2e_9.6.2.exe")

# 2. Fallbacks (PATH del sistema)
MANGADEX_DL_PATH = (
    MANGADEX_LOCAL
    if os.path.exists(MANGADEX_LOCAL)
    else (shutil.which("mangadex-dl") or "mangadex-dl")
)

KCC_C2E_PATH = (
    KCC_LOCAL
    if os.path.exists(KCC_LOCAL)
    else (shutil.which("kcc-c2e") or "kcc-c2e")
)

# Carpetas de destino (Siempre relativas al proyecto)
OUTPUT_FOLDER_MANGA = os.path.join(SCRIPT_DIR, "downloads")
OUTPUT_FOLDER_KCC = os.path.join(SCRIPT_DIR, "output")

# Ajustes de KCC (Kindle Comic Converter)
KCC_PROFILE = "KO"  # KO = Kindle Oasis 2/3 / Paperwhite 12
KCC_FORMAT = "MOBI"  # Formato Dual MOBI/AZW3
KCC_CUSTOM_ARGS = ["-m", "-r", "1", "-u"]
# Para ver la lista completa de argumentos validos, consulta el README.md

# Ajustes generales
DELETE_CBZ_AFTER_CONVERSION = False
DEFAULT_LANGUAGE = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE = True
# Consulta el README.md para mas detalles sobre estos ajustes.
# ==========================================


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def sanitize_filename(filename):
    """Elimina caracteres no permitidos en nombres de archivos de Windows"""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()
