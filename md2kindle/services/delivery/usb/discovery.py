import os
import sys
import ntpath
import posixpath
import logging
import ctypes
from os.path import exists as path_exists

logger = logging.getLogger(__name__)

def get_volume_name(drive_letter):
    """Obtiene el nombre del volumen usando la API de Windows."""
    try:
        kernel32 = ctypes.windll.kernel32
        volume_name_buf = ctypes.create_unicode_buffer(1024)
        kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive_letter),
            volume_name_buf,
            ctypes.sizeof(volume_name_buf),
            None, None, None, None, 0
        )
        return volume_name_buf.value
    except Exception as e:
        logger.debug("No se pudo leer nombre de volumen para %s: %s", drive_letter, e)
        return ""

def get_potential_mount_points() -> list[str]:
    """Devuelve una lista de rutas base donde podrían estar montados discos externos según el OS."""
    points = []
    if os.name == 'nt':
        import string
        points = [f"{d}:\\" for d in string.ascii_uppercase if path_exists(f"{d}:\\")]
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            if path_exists("/Volumes"):
                for d in os.listdir("/Volumes"):
                    full_path = posixpath.join("/Volumes", d)
                    if os.path.isdir(full_path):
                        points.append(full_path)
        else: # Linux
            bases = ["/media", "/run/media", "/mnt"]
            for base in bases:
                if path_exists(base):
                    for d in os.listdir(base):
                        full_path = posixpath.join(base, d)
                        if os.path.isdir(full_path):
                            if base in ("/media", "/run/media") and not d.lower() == "kindle":
                                try:
                                    for sub in os.listdir(full_path):
                                        sub_path = posixpath.join(full_path, sub)
                                        if os.path.isdir(sub_path):
                                            points.append(sub_path)
                                except PermissionError:
                                    pass
                            points.append(full_path)
    return points

def get_kindle_drive():
    """Busca un drive o directorio de Kindle conectado mediante firma de directorios."""
    drives = get_potential_mount_points()
    
    for drive in drives:
        if os.name == 'posix':
            has_documents = path_exists(posixpath.join(drive, 'documents'))
            has_system = path_exists(posixpath.join(drive, 'system'))
        else:
            has_documents = path_exists(ntpath.join(drive, 'documents'))
            has_system = path_exists(ntpath.join(drive, 'system'))
        
        if has_documents and has_system:
            if os.name == 'nt':
                vol_name = get_volume_name(drive).lower()
                if vol_name == "kindle":
                    return drive
            else:
                dir_name = os.path.basename(drive).lower()
                if "kindle" in dir_name:
                    return drive
            
    return None
