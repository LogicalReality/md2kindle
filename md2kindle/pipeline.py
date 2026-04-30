"""Orquestación del pipeline de descarga, conversión y entrega.

Extraído de cli.py para separar la lógica de ejecución del parsing de argumentos.
cli.py construye PipelineParams → pipeline.run() ejecuta.
"""

import logging
import os
import sys

from md2kindle.models import PipelineParams
from md2kindle.config import OUTPUT_FOLDER_MANGA, OUTPUT_FOLDER_KCC
from md2kindle.mangadex import (
    get_manga_aggregate,
    parse_range,
    download_manga,
    audit_and_cleanup,
)
from md2kindle.converter import convert_with_kcc
from md2kindle.delivery import send_to_telegram, send_to_usb

logger = logging.getLogger(__name__)


def process_volume_flow(
    params: PipelineParams, vol: str, base_path: str, aggregate_data: dict
) -> None:
    """Procesa un volumen individual: descarga → auditoría → conversión → envío."""
    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.title, f"Vol {vol}")
    expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
    # El nombre del CBZ suele ser "Vol. X.cbz" -> "Vol. X.mobi"
    mobi_name = f"Vol. {vol}.mobi"
    mobi_file = os.path.join(expected_output_dir, mobi_name)

    if os.path.exists(mobi_file):
        logger.info("%s ya existe. Saltando descarga y conversión...", mobi_name)
        send_to_usb(mobi_file, params.title)
        if params.telegram:
            send_to_telegram(mobi_file)
        return

    folder = os.path.join(base_path, f"Vol {vol}")
    os.makedirs(folder, exist_ok=True)
    if download_manga(
        params.url, folder, params.lang, "v", vol, vol, params.skip_oneshots
    ):
        audit_and_cleanup(
            folder, aggregate_data, "v", vol, vol, params.skip_oneshots
        )
        mobi_list = convert_with_kcc(folder, params.author, params.title)
        if mobi_list:
            for m in mobi_list:
                send_to_usb(m, params.title)
                if params.telegram:
                    send_to_telegram(m)


def process_chapter_flow(
    params: PipelineParams, base_path: str, aggregate_data: dict
) -> None:
    """Procesa un rango de capítulos: descarga → auditoría → conversión → envío."""
    suffix = f"Cap {params.start}" + (
        f"-{params.end}" if params.start != params.end else ""
    )
    folder = os.path.join(base_path, suffix)

    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.title, suffix)
    expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
    # En modo capitulo agrupado, KCC genera un MOBI con el nombre de la carpeta
    mobi_file = os.path.join(expected_output_dir, suffix + ".mobi")

    if os.path.exists(mobi_file):
        logger.info("%s.mobi ya existe. Saltando descarga y conversión...", suffix)
        send_to_usb(mobi_file, params.title)
        if params.telegram:
            send_to_telegram(mobi_file)
    else:
        os.makedirs(folder, exist_ok=True)
        logger.info(
            "Detectado modo CAPÍTULO. Agrupando rango %s-%s...",
            params.start,
            params.end,
        )
        if download_manga(
            params.url,
            folder,
            params.lang,
            "c",
            params.start,
            params.end,
            params.skip_oneshots,
        ):
            audit_and_cleanup(
                folder,
                aggregate_data,
                "c",
                params.start,
                params.end,
                params.skip_oneshots,
            )
            mobi_list = convert_with_kcc(folder, params.author, params.title)
            if mobi_list:
                for m in mobi_list:
                    send_to_usb(m, params.title)
                    if params.telegram:
                        send_to_telegram(m)


def run(params: PipelineParams) -> None:
    """Ejecuta el pipeline completo con los parámetros resueltos."""
    base_path = os.path.join(OUTPUT_FOLDER_MANGA, params.title)

    # Obtener data de auditoria preventivamente
    aggregate_data = {}
    if params.manga_uuid:
        logger.info("Consultando estructura de MangaDex para auditoría...")
        aggregate_data = get_manga_aggregate(params.manga_uuid, params.lang)

    # --- Lógica de Fallback de Idioma Automático ---
    if params.manga_uuid and not aggregate_data:
        fallback_list = ["es-la", "en", "es"]
        if params.lang in fallback_list:
            fallback_list.remove(params.lang)

        for fb_lang in fallback_list:
            logger.info(
                "Idioma '%s' no disponible o sin capítulos. Probando fallback: %s...",
                params.lang,
                fb_lang,
            )
            aggregate_data = get_manga_aggregate(params.manga_uuid, fb_lang)
            if aggregate_data:
                params.lang = fb_lang
                break

    if params.mode == "v":
        volumes = parse_range(params.start, params.end)

        # --- VALIDACIÓN PREVIA ---
        if aggregate_data:
            invalid_vols = [v for v in volumes if v not in aggregate_data]
            if invalid_vols:
                logger.warning(
                    "Los siguientes volúmenes no aparecen en MangaDex (%s): %s",
                    params.lang,
                    invalid_vols,
                )
                available = sorted(
                    list(aggregate_data.keys()),
                    key=lambda x: (
                        float(x) if x.replace(".", "", 1).isdigit() else 999
                    ),
                )
                logger.warning("    Opciones disponibles: %s", available)
                is_interactive = len(sys.argv) <= 1
                if is_interactive:
                    confirm = (
                        input(
                            "> ¿Deseas intentar la descarga de todos modos? [s/N]: "
                        )
                        .strip()
                        .lower()
                    )
                    if confirm != "s":
                        logger.info("Operación cancelada por el usuario.")
                        return

        logger.info(
            "Detectado modo VOLUMEN. Procesando %d tomo(s) individualmente...",
            len(volumes),
        )
        for vol in volumes:
            process_volume_flow(params, vol, base_path, aggregate_data)
    else:
        process_chapter_flow(params, base_path, aggregate_data)

    logger.info("=========================================")
    logger.info(" Proceso Finalizado. Archivos generados en:\n %s", OUTPUT_FOLDER_KCC)
    logger.info("=========================================")
