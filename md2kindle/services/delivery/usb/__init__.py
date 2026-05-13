import os
import sys
import shutil
import logging
from md2kindle.core.config import AppConfig

# Re-exportamos para mantener compatibilidad con tests y lógica interna
from .discovery import get_kindle_drive, get_potential_mount_points, get_volume_name
from .mass_storage import copy_to_mass_storage
from .mtp import copy_via_mtp

logger = logging.getLogger(__name__)

def send_to_usb(file_path_or_list: str | list[str], manga_title: str, app_config: AppConfig | None = None) -> bool:
    """Copia uno o varios archivos al Kindle si está conectado (USB o MTP)."""
    files = [file_path_or_list] if isinstance(file_path_or_list, str) else file_path_or_list
    if not files:
        return False

    # 1. Intentar como Almacenamiento Masivo (Letra de unidad o punto de montaje)
    kindle_drive = get_kindle_drive()
    if kindle_drive:
        return copy_to_mass_storage(files, kindle_drive, manga_title)

    # 2. Intentar como Dispositivo Portátil (MTP) - Solo en Windows y si no es CI
    if os.name == 'nt' and not os.environ.get('CI'):
        logger.info("Buscando Kindle como Dispositivo Portátil (MTP) para %d archivo(s)...", len(files))
        if copy_via_mtp(files, manga_title):
            logger.info("Copia al Kindle (MTP) completada con éxito.")
            return True

    return False
