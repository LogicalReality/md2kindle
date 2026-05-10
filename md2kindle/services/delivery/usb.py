"""Entrega automática a dispositivos Kindle conectados por USB."""

import os
import sys
import ntpath
import posixpath
import shutil
import logging

logger = logging.getLogger(__name__)

import ctypes
import subprocess

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
        points = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            if os.path.exists("/Volumes"):
                for d in os.listdir("/Volumes"):
                    full_path = posixpath.join("/Volumes", d)
                    if os.path.isdir(full_path):
                        points.append(full_path)
        else: # Linux
            bases = ["/media", "/run/media", "/mnt"]
            for base in bases:
                if os.path.exists(base):
                    for d in os.listdir(base):
                        # En Linux /media suele tener el usuario adentro, iteramos un nivel más si es el caso
                        full_path = posixpath.join(base, d)
                        if os.path.isdir(full_path):
                            if base in ("/media", "/run/media") and not d.lower() == "kindle":
                                # Probablemente sea el directorio del usuario, buscar adentro
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
        # Cross-platform path join for checking signatures
        if os.name == 'posix':
            has_documents = os.path.exists(posixpath.join(drive, 'documents'))
            has_system = os.path.exists(posixpath.join(drive, 'system'))
        else:
            has_documents = os.path.exists(ntpath.join(drive, 'documents'))
            has_system = os.path.exists(ntpath.join(drive, 'system'))
        
        if has_documents and has_system:
            if os.name == 'nt':
                vol_name = get_volume_name(drive).lower()
                if vol_name == "kindle":
                    return drive
            else:
                # On POSIX, check if the mount point directory name contains 'kindle'
                dir_name = os.path.basename(drive).lower()
                if "kindle" in dir_name:
                    return drive
            
    return None

def copy_via_mtp(file_path, manga_title):
    """Copia un archivo al Kindle usando el protocolo MTP a través de PowerShell COM."""
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    try {{
        $shell = New-Object -ComObject Shell.Application
        $computer = $shell.NameSpace(17)
        $kindle = $computer.Items() | Where-Object {{ $_.Name -match "Kindle" }}
        if (-not $kindle) {{ exit 1 }}
        
        $internal = $kindle.GetFolder.Items() | Where-Object {{ $_.Name -match "Internal Storage" -or $_.Name -match "Almacenamiento interno" }}
        if (-not $internal) {{ exit 1 }}
        
        $docs = $internal.GetFolder.Items() | Where-Object {{ $_.Name -match "documents" }}
        if (-not $docs) {{ exit 1 }}
        
        $mangaFolder = $docs.GetFolder.Items() | Where-Object {{ $_.Name -eq "Manga" }}
        if (-not $mangaFolder) {{
            $docs.GetFolder.NewFolder("Manga")
            Start-Sleep -Seconds 1
            $mangaFolder = $docs.GetFolder.Items() | Where-Object {{ $_.Name -eq "Manga" }}
        }}
        
        $titleFolder = $mangaFolder.GetFolder.Items() | Where-Object {{ $_.Name -eq "{manga_title}" }}
        if (-not $titleFolder) {{
            $mangaFolder.GetFolder.NewFolder("{manga_title}")
            Start-Sleep -Seconds 1
            $titleFolder = $mangaFolder.GetFolder.Items() | Where-Object {{ $_.Name -eq "{manga_title}" }}
        }}
        
        $titleFolder.GetFolder.CopyHere("{os.path.abspath(file_path)}", 1044)
        Start-Sleep -Seconds 3
        exit 0
    }} catch {{
        exit 2
    }}
    """
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
    return result.returncode == 0

def send_to_usb(file_path, manga_title):
    """Copia el archivo generado al Kindle si está conectado."""
    # 1. Intentar como Almacenamiento Masivo (Letra de unidad)
    kindle_drive = get_kindle_drive()
    
    if kindle_drive:
        dest_folder = os.path.join(kindle_drive, 'documents', 'Manga', manga_title)
        os.makedirs(dest_folder, exist_ok=True)
        # Use os.path.basename for the file path, but in tests if file_path is Windows style ("C:\..."), 
        # os.path.basename might fail on Linux. To be truly robust, we extract filename manually if needed,
        # but os.path.basename is the correct native approach.
        # Wait, if file_path is passed from another module, it's already an absolute native path.
        dest_path = os.path.join(dest_folder, os.path.basename(file_path))
        
        logger.info("Kindle detectado en %s (Almacenamiento Masivo). Copiando archivo...", kindle_drive)
        try:
            shutil.copy2(file_path, dest_path)
            logger.info("Copia al Kindle completada con éxito.")
            return True
        except Exception as e:
            logger.error("Error al copiar al Kindle por USB: %s", e)
            return False
            
    # 2. Intentar como Dispositivo Portátil (MTP) - Común en Paperwhite Signature Edition
    if os.name == 'nt':
        logger.info("Buscando Kindle como Dispositivo Portátil (MTP)...")
        if copy_via_mtp(file_path, manga_title):
            logger.info("Copia al Kindle (MTP) completada con éxito.")
            return True
            
    return False
