"""Configuración central, constantes y detección de rutas."""

import os
import re
import shutil
import warnings

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Silenciar avisos de dependencias de requests (comunes en entornos CI/experimental)
warnings.filterwarnings("ignore", message=".*urllib3.*match a supported version.*")

IS_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

# ==========================================
# CONFIGURACIÓN
# ==========================================
# Configuración de Rutas (Detección en Cascada)
# Subimos un nivel porque este archivo vive en md2kindle/config.py
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Buscar en carpetas conocidas (Modo Portable)
BIN_DIR = os.path.join(SCRIPT_DIR, "bin")

import glob

def find_binary(pattern, subfolder=None):
    """Busca un binario usando wildcards. Si hay varios, devuelve el último (mayor versión)."""
    search_dirs = [
        os.path.join(BIN_DIR, subfolder) if subfolder else BIN_DIR,
        os.path.join(SCRIPT_DIR, subfolder) if subfolder else SCRIPT_DIR
    ]
    
    for d in search_dirs:
        matches = glob.glob(os.path.join(d, pattern))
        if matches:
            # Ordenamos para asegurar que kcc_c2e_10.1.2.exe vaya después de kcc_c2e_9.6.2.exe
            return sorted(matches, reverse=True)[0]
    return None

MANGADEX_PATH_LOCAL = find_binary("mangadex-dl*.exe", "mangadex-dl")
KCC_PATH_LOCAL = find_binary("kcc*c2e*.exe") or find_binary("kcc*.exe")
FFSEND_PATH_LOCAL = find_binary("ffsend*.exe")

# 2. Fallbacks (PATH del sistema)
MANGADEX_DL_PATH = (
    MANGADEX_PATH_LOCAL
    if MANGADEX_PATH_LOCAL and os.name == "nt"
    else (shutil.which("mangadex-dl") or "mangadex-dl")
)

KCC_C2E_PATH = (
    KCC_PATH_LOCAL
    if KCC_PATH_LOCAL and os.name == "nt"
    else (shutil.which("kcc-c2e") or "kcc-c2e")
)

FFSEND_PATH = (
    FFSEND_PATH_LOCAL
    if FFSEND_PATH_LOCAL and os.name == "nt"
    else (shutil.which("ffsend") or "ffsend")
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
