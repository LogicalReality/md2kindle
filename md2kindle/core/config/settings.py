"""Configuración central y compatibilidad con constantes históricas."""

from dataclasses import dataclass, field
import os
import re
import warnings

from md2kindle.core.config.binaries import BinaryPaths, resolve_binaries

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
    language_fallback_pool: list[str] = field(default_factory=lambda: ["es-la", "en", "es"])
    skip_oneshots_on_volume_mode: bool = True
    is_ci: bool = False
    # Telegram
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    # R2
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    # D1 (Observabilidad)
    d1_account_id: str | None = None
    d1_database_id: str | None = None
    d1_api_token: str | None = None


def load_config(root_dir=None) -> AppConfig:
    """Construye configuración explícita desde entorno y filesystem."""
    root_dir = root_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return AppConfig(
        root_dir=root_dir,
        binaries=resolve_binaries(root_dir=root_dir),
        output_folder_manga=os.path.join(root_dir, "downloads"),
        output_folder_kcc=os.path.join(root_dir, "output"),
        is_ci=os.environ.get("CI") == "true"
        or os.environ.get("GITHUB_ACTIONS") == "true",
        # Credentials
        telegram_bot_token=os.environ.get("TELEGRAM_TOKEN"),
        telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID"),
        r2_account_id=os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
        r2_access_key_id=os.environ.get("R2_ACCESS_KEY_ID"),
        r2_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY"),
        r2_bucket_name=os.environ.get("R2_BUCKET_NAME"),
        d1_account_id=os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
        d1_database_id=os.environ.get("D1_DATABASE_ID"),
        d1_api_token=os.environ.get("D1_API_TOKEN"),
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
