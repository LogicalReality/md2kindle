"""Conversión de archivos CBZ a formatos Kindle usando KCC."""

import os
import subprocess
import glob
import re

from md2kindle.config import (
    KCC_C2E_PATH,
    KCC_PROFILE,
    KCC_FORMAT,
    KCC_CUSTOM_ARGS,
    OUTPUT_FOLDER_MANGA,
    OUTPUT_FOLDER_KCC,
    DELETE_CBZ_AFTER_CONVERSION,
    IS_CI,
)
from md2kindle.delivery import format_manga_title


def convert_with_kcc(target_path, author="MangaDex", title=None):
    """Convierte archivos CBZ en Kindle-friendly formats reflejando la estructura original"""
    search_pattern = os.path.join(target_path, "**", "*.cbz")
    cbz_files = glob.glob(search_pattern, recursive=True)

    generated_files = []  # Seguimiento de archivos para envío

    if not cbz_files:
        cbz_files = glob.glob(os.path.join(target_path, "*.cbz"))
        if not cbz_files:
            return

    # Calcular ruta de salida replicando la estructura de carpetas
    try:
        rel_path = os.path.relpath(target_path, OUTPUT_FOLDER_MANGA)
        final_output = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
        os.makedirs(final_output, exist_ok=True)
    except Exception as e:
        print(f"[!] Error al crear carpeta de salida en KCC: {e}")
        final_output = OUTPUT_FOLDER_KCC
        rel_path = target_path

    # Extraer nombre de manga y volumen del path para metadatos
    manga_title = title
    if not manga_title:
        try:
            path_parts = rel_path.split(os.sep)
            manga_title = path_parts[0]
        except Exception:
            manga_title = "Manga"

    for cbz_file in cbz_files:
        print(f"\n[+] Procesando con KCC: {os.path.basename(cbz_file)}")

        # Extraer volumen del nombre del CBZ (ej: "Vol. 39.cbz" -> "Vol. 39")
        cbz_basename = os.path.splitext(os.path.basename(cbz_file))[0]
        vol_match = re.search(r"(Vol\.?\s*\d+)", cbz_basename, re.IGNORECASE)
        vol_str = vol_match.group(1) if vol_match else cbz_basename

        # Formatear titulo completo para metadatos del MOBI
        mobi_title = f"{manga_title} {vol_str}"

        cmd = (
            [
                KCC_C2E_PATH,
                "-p",
                KCC_PROFILE,
                "-f",
                KCC_FORMAT,
                "-o",
                final_output,
                "-a",
                author,  # Inyección del autor real
                "-t",
                mobi_title,  # Inyección del título completo
            ]
            + KCC_CUSTOM_ARGS
            + [cbz_file]
        )

        try:
            print(f"[*] Guardando en: {final_output}")
            result = subprocess.run(
                cmd, stderr=subprocess.DEVNULL if IS_CI else subprocess.PIPE
            )
            if result.returncode == 0:
                # Localizar el archivo generado (.mobi)
                filename_no_ext = os.path.splitext(os.path.basename(cbz_file))[0]
                mobi_file = os.path.join(final_output, filename_no_ext + ".mobi")
                if os.path.exists(mobi_file):
                    # Renombrar archivo con título completo
                    manga, vol = format_manga_title(mobi_file)
                    new_name = f"{manga} {vol}.mobi"
                    new_path = os.path.join(final_output, new_name)
                    if new_name != os.path.basename(mobi_file):
                        os.rename(mobi_file, new_path)
                        mobi_file = new_path
                    generated_files.append(mobi_file)

                if DELETE_CBZ_AFTER_CONVERSION:
                    os.remove(cbz_file)
        except Exception as e:
            print(f"\n[!] Excepción al ejecutar KCC: {e}")

    return generated_files
