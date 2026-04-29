"""Modelos de datos tipados para el pipeline de md2kindle."""

import os
import re
from dataclasses import dataclass


@dataclass
class PipelineParams:
    """Parámetros resueltos para la ejecución del pipeline.

    Reemplaza el dict anónimo que se pasaba entre cli.py y los módulos.
    Cada campo tiene tipo explícito — un typo genera AttributeError en dev.
    """

    url: str
    title: str
    lang: str
    mode: str  # "v" (volumen) | "c" (capítulo)
    start: str
    end: str
    author: str
    manga_uuid: str | None
    skip_oneshots: bool
    silent: bool
    telegram: bool


def format_manga_title(file_path: str, output_folder_kcc: str) -> tuple[str, str]:
    """Extrae el nombre del manga y el volumen desde la ruta del archivo.

    Movido aquí desde delivery.py para romper la dependencia circular
    converter.py → delivery.py.

    Args:
        file_path: Ruta absoluta al archivo .mobi generado.
        output_folder_kcc: Ruta base de la carpeta de output de KCC.

    Returns:
        Tupla (manga_name, volume_string).
    """
    rel_path = os.path.relpath(file_path, output_folder_kcc)
    parts = rel_path.split(os.sep)
    manga = parts[0]
    filename = parts[-1].replace(".mobi", "")
    vol_match = re.search(r"(Vol\.?\s*\d+)", filename, re.IGNORECASE)
    vol = vol_match.group(1) if vol_match else filename
    return manga, vol
