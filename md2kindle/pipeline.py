"""Orquestación del pipeline de descarga, conversión y entrega.

Extraído de cli.py para separar la lógica de ejecución del parsing de argumentos.
cli.py construye PipelineParams → pipeline.run() ejecuta.
"""

import logging
import os
import sys
import glob
import shutil

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


def deliver_batch(mobi_files: list[str], params: PipelineParams) -> None:
    """Entrega un lote de archivos. Intenta USB primero; si falla, ofrece Telegram una sola vez."""
    if not mobi_files:
        return

    # 1. Intentar USB para todos
    usb_detected = False
    for mobi_file in mobi_files:
        if send_to_usb(mobi_file, params.title):
            usb_detected = True

    # 2. Si se pidió Telegram por flag, enviar todos
    if params.telegram:
        for mobi_file in mobi_files:
            send_to_telegram(mobi_file)
        return

    # 3. Si NO se detectó Kindle y es interactivo, preguntar UNA vez por todo el lote
    if not usb_detected:
        is_interactive = len(sys.argv) <= 1
        if is_interactive:
            print(f"\n> Se generaron {len(mobi_files)} archivos pero no se detectó un Kindle.")
            fallback = input(f"> ¿Deseas enviar todo el lote ({len(mobi_files)} archivos) por Telegram? [S/n] [Enter para 'S']: ").strip().lower()
            if fallback != 'n':
                for mobi_file in mobi_files:
                    send_to_telegram(mobi_file)



def process_volume_flow(
    params: PipelineParams, vol: str, base_path: str, aggregate_data: dict
) -> list[str]:
    """Procesa un volumen individual: descarga → auditoría → conversión y retorna archivos."""
    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.title, f"Vol {vol}")
    expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
    # El nombre del CBZ suele ser "Vol. X.cbz" -> "Vol. X.mobi"
    mobi_name = f"Vol. {vol}.mobi"
    mobi_file = os.path.join(expected_output_dir, mobi_name)

    if os.path.exists(mobi_file):
        logger.info("%s ya existe. Saltando descarga y conversión...", mobi_name)
        return [mobi_file]

    folder = os.path.join(base_path, f"Vol {vol}")
    os.makedirs(folder, exist_ok=True)
    if download_manga(
        params.url, folder, params.lang, "v", vol, vol, params.skip_oneshots
    ):
        audit_and_cleanup(
            folder, aggregate_data, "v", vol, vol, params.skip_oneshots
        )
        
        cbz_files = glob.glob(os.path.join(folder, "*.cbz"))
        if not cbz_files:
            logger.warning("No se generaron archivos .cbz para el Vol %s. Limpiando...", vol)
            shutil.rmtree(folder, ignore_errors=True)
            return []

        mobi_list = convert_with_kcc(folder, params.author, params.title)
        return mobi_list or []
    
    return []



def process_chapter_flow(
    params: PipelineParams, base_path: str, aggregate_data: dict
) -> list[str]:
    """Procesa un rango de capítulos: descarga → auditoría → conversión y retorna archivos."""
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
        return [mobi_file]
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

            cbz_files = glob.glob(os.path.join(folder, "*.cbz"))
            if not cbz_files:
                logger.warning("No se generaron archivos .cbz para el rango de capítulos. Limpiando...")
                shutil.rmtree(folder, ignore_errors=True)
                return []

            mobi_list = convert_with_kcc(folder, params.author, params.title)
            return mobi_list or []
        
        return []



def run(params: PipelineParams) -> None:
    """Ejecuta el pipeline completo con los parámetros resueltos."""
    base_path = os.path.join(OUTPUT_FOLDER_MANGA, params.title)

    aggregate_data = {}
    fallback_aggregates = {}
    fallback_list = ["es-la", "en", "es"]
    if params.lang in fallback_list:
        fallback_list.remove(params.lang)

    if params.manga_uuid:
        logger.info("Consultando estructura de MangaDex para auditoría y fallbacks...")
        aggregate_data = get_manga_aggregate(params.manga_uuid, params.lang)
        
        for fb_lang in fallback_list:
            fb_data = get_manga_aggregate(params.manga_uuid, fb_lang)
            if fb_data:
                fallback_aggregates[fb_lang] = fb_data

    all_mobi_files = []

    if params.mode == "v":
        volumes = parse_range(params.start, params.end)
        logger.info("Detectado modo VOLUMEN. Procesando %d tomo(s) individualmente...", len(volumes))

        for vol in volumes:
            current_lang = params.lang
            current_agg = aggregate_data

            if current_agg and vol in current_agg:
                pass
            else:
                found = False
                for fb_lang in fallback_list:
                    if fb_lang in fallback_aggregates and vol in fallback_aggregates[fb_lang]:
                        logger.info("Vol %s no hallado en '%s'. Usando fallback: '%s'", vol, params.lang, fb_lang)
                        current_lang = fb_lang
                        current_agg = fallback_aggregates[fb_lang]
                        found = True
                        break
                
                if not found and params.manga_uuid:
                    logger.warning("Vol %s no encontrado en MangaDex (ni principal ni fallbacks). Intentando igual...", vol)

            original_lang = params.lang
            params.lang = current_lang
            generated = process_volume_flow(params, vol, base_path, current_agg)
            params.lang = original_lang
            
            all_mobi_files.extend(generated)
    else:
        if not aggregate_data:
            for fb_lang in fallback_list:
                if fb_lang in fallback_aggregates:
                    logger.info("Idioma '%s' sin datos. Usando fallback global: '%s'", params.lang, fb_lang)
                    params.lang = fb_lang
                    aggregate_data = fallback_aggregates[fb_lang]
                    break
                    
        generated = process_chapter_flow(params, base_path, aggregate_data)
        all_mobi_files.extend(generated)

    deliver_batch(all_mobi_files, params)

    logger.info("=========================================")
    logger.info(" Proceso Finalizado. Archivos generados en:\n %s", OUTPUT_FOLDER_KCC)
    logger.info("=========================================")
