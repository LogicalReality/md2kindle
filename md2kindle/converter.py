"""Conversión de archivos CBZ a formatos Kindle usando KCC."""

import logging
import os
import subprocess
import glob
import re

from md2kindle.config import APP_CONFIG, AppConfig
from md2kindle.models import format_manga_title

logger = logging.getLogger(__name__)


def convert_with_kcc(
    target_path,
    author="MangaDex",
    title=None,
    vol_hint=None,
    app_config: AppConfig | None = None,
):
    """Convierte archivos CBZ en Kindle-friendly formats reflejando la estructura original"""
    app_config = app_config or APP_CONFIG
    search_pattern = os.path.join(target_path, "**", "*.cbz")
    cbz_files = glob.glob(search_pattern, recursive=True)

    generated_files = []  # Seguimiento de archivos para envío

    if not cbz_files:
        cbz_files = glob.glob(os.path.join(target_path, "*.cbz"))
        if not cbz_files:
            return

    # Calcular ruta de salida replicando la estructura de carpetas
    try:
        rel_path = os.path.relpath(target_path, app_config.output_folder_manga)
        final_output = os.path.join(app_config.output_folder_kcc, rel_path)
        os.makedirs(final_output, exist_ok=True)
    except Exception as e:
        logger.error("Error al crear carpeta de salida en KCC: %s", e)
        final_output = app_config.output_folder_kcc
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
        logger.info("Procesando con KCC: %s", os.path.basename(cbz_file))

        # Extraer volumen del nombre del CBZ (ej: "Vol. 39.cbz" -> "Vol. 39")
        cbz_basename = os.path.splitext(os.path.basename(cbz_file))[0]
        vol_match = re.search(r"(Vol\.?\s*\d+)", cbz_basename, re.IGNORECASE)
        vol_str = vol_match.group(1) if vol_match else (f"Vol. {vol_hint}" if vol_hint else cbz_basename)

        # Formatear titulo completo para metadatos del MOBI
        mobi_title = f"{manga_title} {vol_str}"

        cmd = (
            [
                app_config.binaries.kcc_c2e,
                "-p",
                app_config.kcc_profile,
                "-f",
                app_config.kcc_format,
                "-o",
                final_output,
                "-a",
                author,  # Inyección del autor real
                "-t",
                mobi_title,  # Inyección del título completo
            ]
            + app_config.kcc_custom_args
            + [cbz_file]
        )

        try:
            logger.info("Guardando en: %s", final_output)
            logger.debug("Comando KCC: %s", cmd)
            result = subprocess.run(
                cmd, stderr=subprocess.DEVNULL if app_config.is_ci else subprocess.PIPE
            )
            if result.returncode == 0:
                # Localizar el archivo generado (.mobi)
                filename_no_ext = os.path.splitext(os.path.basename(cbz_file))[0]
                mobi_file = os.path.join(final_output, filename_no_ext + ".mobi")
                if os.path.exists(mobi_file):
                    # Renombrar archivo con título completo
                    manga, vol = format_manga_title(
                        mobi_file, app_config.output_folder_kcc
                    )
                    # Si format_manga_title no pudo extraer "Vol X", usar el hint
                    if vol_hint and not re.search(r"Vol\.?\s*\d+", vol, re.IGNORECASE):
                        if str(vol_hint).startswith("Cap") or str(vol_hint).startswith("Vol"):
                            vol = str(vol_hint)
                        else:
                            vol = f"Vol. {vol_hint}"
                    new_name = f"{manga} {vol}.mobi"
                    new_path = os.path.join(final_output, new_name)
                    if new_name != os.path.basename(mobi_file):
                        os.replace(mobi_file, new_path)
                        mobi_file = new_path
                    generated_files.append(mobi_file)

                if app_config.delete_cbz_after_conversion:
                    os.remove(cbz_file)
        except Exception as e:
            logger.error("Excepción al ejecutar KCC: %s", e)

    return generated_files
