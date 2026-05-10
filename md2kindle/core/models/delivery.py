import os
import re
from dataclasses import dataclass

@dataclass
class DeliveryOptions:
    telegram: bool
    r2: bool

def format_manga_title(file_path: str, output_folder_kcc: str) -> tuple[str, str]:
    """Extrae el nombre del manga y el volumen desde la ruta del archivo."""
    rel_path = os.path.relpath(file_path, output_folder_kcc)
    parts = rel_path.split(os.sep)
    manga = parts[0]
    filename = parts[-1].replace(".mobi", "")
    vol_match = re.search(r"(Vol\.?\s*\d+)", filename, re.IGNORECASE)
    vol = vol_match.group(1) if vol_match else filename
    return manga, vol
