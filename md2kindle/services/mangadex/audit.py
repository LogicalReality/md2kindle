"""Auditoría de integridad y limpieza de huérfanos bajados por error."""

import logging
import os
import glob
import re

from md2kindle.utils.ranges import parse_range

logger = logging.getLogger(__name__)


def _normalize_chapter_number(val):
    """
    Normaliza números de capítulo (ej. '5.0' -> '5', '05' -> '5').
    Maneja el caso especial 'none'.
    """
    if not val:
        return ""

    if not isinstance(val, str):
        val = str(val)

    if val.lower() == "none":
        return "none"

    try:
        if "." in val:
            # Colapsar ceros a la derecha y puntos sobrantes
            clean = str(float(val)).rstrip("0").rstrip(".")
            return clean if clean != "" else "0"
        return str(int(val))
    except (ValueError, TypeError):
        return val.lower() if isinstance(val, str) else val


def audit_and_cleanup(
    target_path, aggregate_data, mode, start_val, end_val, skip_oneshots
):
    """
    Realiza una auditoría inteligente y limpia huérfanos bajados por error.
    Usa la estructura real informada por la API de MangaDex.
    """
    expected_chapters = set()

    if mode == "v":
        if not aggregate_data:
            logger.warning("Modo Volumen: Sin datos de la API. Safe Mode activado (sin limpieza).")
            return

        volumes_to_check = parse_range(start_val, end_val)
        for expected_vol in volumes_to_check:
            # Buscar la key exacta del volumen ("1", "S1", "none")
            vol_data = aggregate_data.get(expected_vol)
            if not vol_data:
                # Intento fallback para tratar "1.0" como "1" o viceversa
                fallback_key = _normalize_chapter_number(expected_vol)
                vol_data = aggregate_data.get(fallback_key)

            if vol_data and "chapters" in vol_data:
                for ch_dict in vol_data["chapters"].values():
                    # Solo añadir si no hemos decidido ignorar oneshoots
                    is_oneshot = (
                        ch_dict.get("chapter") == "none"
                        or ch_dict.get("chapter") is None
                    )
                    if is_oneshot and skip_oneshots:
                        continue
                    # Normalizar antes de añadir a la whitelist
                    ch_val = str(ch_dict.get("chapter", "none"))
                    expected_chapters.add(_normalize_chapter_number(ch_val))

    else:  # Modo Capítulo
        chapters_to_check = parse_range(start_val, end_val)
        for expected_ch in chapters_to_check:
            expected_chapters.add(_normalize_chapter_number(str(expected_ch)))

    # Leer archivos locales
    all_cbz = glob.glob(os.path.join(target_path, "*.cbz"))
    found_chapters = set()

    logger.info("--- Auditoría de Integridad ---")

    for cbz_file in all_cbz:
        filename = os.path.basename(cbz_file)

        # Patrón robusto para capítulos decimales y enteros
        # mangadex-dl suele poner "- Ch. XX" o "Chapter XX" al final
        pattern = r"(?:Ch\.|Chapter)\s*(\d+(?:\.\d+)?|none)\b"
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            local_chap_raw = match.group(1)
            local_chap_clean = _normalize_chapter_number(local_chap_raw)
            found_chapters.add(local_chap_clean)

            # Limpieza (Orphans) segun Whitelist
            if expected_chapters and local_chap_clean not in expected_chapters:
                # Advertencia: Si es un Oneshot ("none") y el usuario no pidio borrarlos, no truncar
                if local_chap_clean == "none" and not skip_oneshots:
                    pass
                else:
                    logger.info(
                        "Eliminando capítulo extra no relacionado al objetivo: %s",
                        filename,
                    )
                    try:
                        os.remove(cbz_file)
                    except Exception as e:
                        logger.error("Error al borrar %s: %s", filename, e)
        else:
            # Si mangadex-dl lo descargo como volumen completo sin separar por capítulos
            if mode == "v":
                found_chapters.update(expected_chapters)

    if expected_chapters:

        missing = expected_chapters - found_chapters
        if missing:
            logger.warning(
                "La API esperaba los siguientes capítulos para el/los volumen(es) solicitado(s), "
                "pero no se encontraron (posible censura o falta de traducción):"
            )
            # Ordenar si es numerico
            sorted_missing = sorted(
                list(missing),
                key=lambda x: float(x) if x.replace(".", "", 1).isdigit() else 999,
            )
            logger.warning("    Faltantes: %s", sorted_missing)
        else:
            logger.info(
                "Todos los capítulos esperados según la API están presentes."
            )
