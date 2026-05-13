import os
import shutil
import logging
from shutil import copy2 as shutil_copy2

logger = logging.getLogger(__name__)

def copy_to_mass_storage(files: list[str], kindle_drive: str, manga_title: str) -> bool:
    """Copia archivos a un Kindle montado como unidad de disco."""
    dest_folder = os.path.join(kindle_drive, 'documents', 'Manga', manga_title)
    os.makedirs(dest_folder, exist_ok=True)
    
    logger.info("Kindle detectado en %s (Almacenamiento Masivo). Copiando %d archivo(s)...", kindle_drive, len(files))
    success_count = 0
    for f in files:
        dest_path = os.path.join(dest_folder, os.path.basename(f))
        try:
            shutil_copy2(f, dest_path)
            success_count += 1
        except Exception as e:
            logger.error("Error al copiar %s al Kindle: %s", f, e)
    
    return success_count > 0
