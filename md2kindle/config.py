"""Configuración central y compatibilidad con constantes históricas."""

from dataclasses import dataclass, field
import os
import re
import warnings

from md2kindle.infrastructure.binaries import BinaryPaths, resolve_binaries

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Silenciar avisos de dependencias de requests (comunes en entornos CI/experimental)
warnings.filterwarnings("ignore", message=".*urllib3.*match a supported version.*")


@dataclass(frozen=True)
class AppConfig:
    """Configuración explícita de aplicación.

    Las constantes al final del archivo quedan como capa de compatibilidad.
    Código nuevo debería recibir `AppConfig` por parámetro.
    """

    root_dir: str
    binaries: BinaryPaths
    output_folder_manga: str
    output_folder_kcc: str
    kcc_profile: str = "KO"  # KO = Kindle Oasis 2/3 / Paperwhite 12
    kcc_format: str = "MOBI"  # Formato Dual MOBI/AZW3
    kcc_custom_args: list[str] = field(default_factory=lambda: ["-m", "-r", "1", "-u"])
    delete_cbz_after_conversion: bool = False
    default_language: str = "es-la"
    skip_oneshots_on_volume_mode: bool = True
    is_ci: bool = False


def load_config(root_dir=None) -> AppConfig:
    """Construye configuración explícita desde entorno y filesystem."""
    root_dir = root_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return AppConfig(
        root_dir=root_dir,
        binaries=resolve_binaries(root_dir=root_dir),
        output_folder_manga=os.path.join(root_dir, "downloads"),
        output_folder_kcc=os.path.join(root_dir, "output"),
        is_ci=os.environ.get("CI") == "true"
        or os.environ.get("GITHUB_ACTIONS") == "true",
    )


APP_CONFIG = load_config()

# Constantes históricas: preservan imports existentes mientras migramos módulos.
SCRIPT_DIR = APP_CONFIG.root_dir
BIN_DIR = os.path.join(SCRIPT_DIR, "bin")
MANGADEX_DL_PATH = APP_CONFIG.binaries.mangadex_dl
KCC_C2E_PATH = APP_CONFIG.binaries.kcc_c2e
FFSEND_PATH = APP_CONFIG.binaries.ffsend
OUTPUT_FOLDER_MANGA = APP_CONFIG.output_folder_manga
OUTPUT_FOLDER_KCC = APP_CONFIG.output_folder_kcc
KCC_PROFILE = APP_CONFIG.kcc_profile
KCC_FORMAT = APP_CONFIG.kcc_format
KCC_CUSTOM_ARGS = APP_CONFIG.kcc_custom_args
DELETE_CBZ_AFTER_CONVERSION = APP_CONFIG.delete_cbz_after_conversion
DEFAULT_LANGUAGE = APP_CONFIG.default_language
SKIP_ONESHOTS_ON_VOLUME_MODE = APP_CONFIG.skip_oneshots_on_volume_mode
IS_CI = APP_CONFIG.is_ci


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def sanitize_filename(filename):
    """Elimina caracteres no permitidos en nombres de archivos de Windows"""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()
