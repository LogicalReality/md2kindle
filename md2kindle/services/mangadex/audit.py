"""Auditoría de integridad y limpieza de huérfanos bajados por error."""

import logging
import os
import glob
import re

from md2kindle.utils.ranges import parse_range

logger = logging.getLogger(__name__)


def audit_and_cleanup(
    target_path, aggregate_data, mode, start_val, end_val, skip_oneshots
):
    """
    Realiza una auditoría inteligente y limpia huérfanos bajados por error.
    Usa la estructura real informada por la API de MangaDex.
    """
    if not aggregate_data:
        return  # Si no hay datos de la API, fall in safe mode (no borrar nada)

    expected_chapters = set()

    if mode == "v":
        volumes_to_check = parse_range(start_val, end_val)
        for expected_vol in volumes_to_check:
            # Buscar la key exacta del volumen ("1", "S1", "none")
            vol_data = aggregate_data.get(expected_vol)
            if not vol_data:
                # Intento fallback para tratar "1.0" como "1" o viceversa
                fallback_key = (
                    str(int(float(expected_vol)))
                    if expected_vol.replace(".", "", 1).isdigit()
                    and expected_vol.endswith(".0")
                    else expected_vol
                )
                vol_data = aggregate_data.get(fallback_key)

            if vol_data and "chapters" in vol_data:
                for ch_dict in vol_data["chapters"].values():
                    # Solo añadir si no hemos decidido ignorar unoshoots
                    is_oneshot = (
                        ch_dict.get("chapter") == "none"
                        or ch_dict.get("chapter") is None
                    )
                    if is_oneshot and skip_oneshots:
                        continue
                    # La key del diccionario es casi siempre el numero del capitulo
                    if ch_dict.get("chapter") != "none":
                        expected_chapters.add(str(ch_dict.get("chapter")))

    else:  # Modo Capítulo
        chapters_to_check = parse_range(start_val, end_val)
        for expected_ch in chapters_to_check:
            expected_chapters.add(str(expected_ch))

    # Leer archivos locales
    all_cbz = glob.glob(os.path.join(target_path, "*.cbz"))
    found_chapters = set()

    logger.info("--- Auditoría de Integridad ---")

    for cbz_file in all_cbz:
        filename = os.path.basename(cbz_file)

        # mangadex-dl suele poner "- Ch. XX" o "Chapter XX" al final
        # Funciona con variaciones "Ch. 5", "Ch. 5.5", "Ch. none"
        match = re.search(r"Ch\.\s*([\d\.]+|none)\b", filename, re.IGNORECASE)
        if not match:
            match = re.search(r"Chapter\s*([\d\.]+|none)\b", filename, re.IGNORECASE)

        if match:
            local_chap = match.group(1)
            # Manejar ceros a la izquierda que mangadex-dl pudiera haber puesto
            if local_chap.replace(".", "", 1).isdigit():
                if "." in local_chap:
                    local_chap_clean = str(float(local_chap)).rstrip("0").rstrip(".")
                    if local_chap_clean == "":
                        local_chap_clean = "0"
                else:
                    local_chap_clean = str(int(local_chap))
            else:
                local_chap_clean = local_chap  # "none" u otros strings

            found_chapters.add(local_chap_clean)

            # Limpieza (Orphans) segun Whitelist de la API
            # Solo limpiamos si logramos extraer una lista de expecteds valida
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
                # El archivo Vol. X.cbz agrupa todo. Asumimos que contiene lo esperado
                # para evitar falsos positivos en el warning de faltantes.
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
