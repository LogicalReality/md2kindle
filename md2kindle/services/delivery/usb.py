"""Entrega automática a dispositivos Kindle conectados por USB."""

import os
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

def get_kindle_drive():
    """Busca un drive de Kindle conectado en Windows como Almacenamiento Masivo."""
    if os.name != 'nt':
        return None
    
    import string
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    
    for drive in drives:
        has_documents = os.path.exists(os.path.join(drive, 'documents'))
        has_system = os.path.exists(os.path.join(drive, 'system'))
        
        if has_documents and has_system:
            vol_name = get_volume_name(drive).lower()
            if vol_name == "kindle":
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
