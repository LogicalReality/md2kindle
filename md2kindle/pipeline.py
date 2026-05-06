"""Orquestación del pipeline de descarga, conversión y entrega.

Extraído de cli.py para separar la lógica de ejecución del parsing de argumentos.
cli.py construye PipelineParams → pipeline.run() ejecuta.
"""

import html
import logging
import os
import sys
import glob
import shutil

from md2kindle.config import OUTPUT_FOLDER_MANGA, OUTPUT_FOLDER_KCC
from md2kindle.converter import convert_with_kcc
from md2kindle.delivery import send_to_telegram, send_to_usb
from md2kindle.delivery.d1 import log_download
from md2kindle.delivery.r2 import send_to_r2
from md2kindle.delivery.telegram import send_message
from md2kindle.mangadex import (
    get_manga_aggregate,
    parse_range,
    download_manga,
    audit_and_cleanup,
)
from md2kindle.models import PipelineParams, format_manga_title

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
            manga, vol = format_manga_title(mobi_file, OUTPUT_FOLDER_KCC)
            log_download(manga, vol, params.lang, mobi_file, "usb")

    # 2. Si se pidió R2 por flag, subir y enviar link por Telegram
    if params.r2:
        for mobi_file in mobi_files:
            manga, vol = format_manga_title(mobi_file, OUTPUT_FOLDER_KCC)
            url = send_to_r2(mobi_file, manga, vol)
            if url:
                safe_manga = html.escape(manga)
                safe_vol = html.escape(vol)
                safe_url = html.escape(url)
                msg_html = f"✅ ¡<b>{safe_manga}</b> {safe_vol} subido a R2!\n\n👉 <a href='{safe_url}'>Descargar Manga</a>"
                send_message(msg_html, parse_mode="HTML")
                log_download(manga, vol, params.lang, mobi_file, "r2")
            else:
                logger.warning(f"Fallo al subir {mobi_file} a R2. Haciendo fallback a Telegram clásico.")
                send_to_telegram(mobi_file)
                log_download(manga, vol, params.lang, mobi_file, "telegram")
        return

    # 3. Si se pidió Telegram por flag (envío directo del archivo)
    if params.telegram:
        for mobi_file in mobi_files:
            send_to_telegram(mobi_file)
            manga, vol = format_manga_title(mobi_file, OUTPUT_FOLDER_KCC)
            log_download(manga, vol, params.lang, mobi_file, "telegram")
        return

    # 4. Si NO se detectó Kindle y es interactivo, preguntar UNA vez por todo el lote
    if not usb_detected:
        is_interactive = len(sys.argv) <= 1
        if is_interactive:
            print(f"\n> Se generaron {len(mobi_files)} archivos pero no se detectó un Kindle.")
            fallback = input(f"> ¿Deseas subir el lote ({len(mobi_files)} archivos) a Cloudflare R2 y enviar el link por Telegram? [S/n/t] ('t' para archivo directo) [Enter para 'S']: ").strip().lower()
            if fallback == 't':
                for mobi_file in mobi_files:
                    send_to_telegram(mobi_file)
                    manga, vol = format_manga_title(mobi_file, OUTPUT_FOLDER_KCC)
                    log_download(manga, vol, params.lang, mobi_file, "telegram")
            elif fallback != 'n':
                for mobi_file in mobi_files:
                    manga, vol = format_manga_title(mobi_file, OUTPUT_FOLDER_KCC)
                    url = send_to_r2(mobi_file, manga, vol)
                    if url:
                        safe_manga = html.escape(manga)
                        safe_vol = html.escape(vol)
                        safe_url = html.escape(url)
                        msg_html = f"✅ ¡<b>{safe_manga}</b> {safe_vol} subido a R2!\n\n👉 <a href='{safe_url}'>Descargar Manga</a>"
                        send_message(msg_html, parse_mode="HTML")
                        log_download(manga, vol, params.lang, mobi_file, "r2")



def process_volume_flow(
    params: PipelineParams, vol: str, base_path: str, aggregate_data: dict
) -> list[str]:
    """Procesa un volumen individual: descarga → auditoría → conversión y retorna archivos."""
    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.title, f"Vol {vol}")
    expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
    # El conversor (KCC) renombra el archivo final para incluir el nombre de la serie.
    mobi_name = f"{params.title} Vol. {vol}.mobi"
    mobi_file = os.path.join(expected_output_dir, mobi_name)

    if os.path.exists(mobi_file):
        logger.info("%s ya existe. Saltando descarga y conversión...", mobi_name)
        return [mobi_file]

    folder = os.path.join(base_path, f"Vol {vol}")
    os.makedirs(folder, exist_ok=True)

    # 2. --- SALTAR DESCARGA SI YA HAY CBZ ---
    existing_cbzs = glob.glob(os.path.join(folder, "*.cbz"))
    
    if existing_cbzs:
        logger.info("CBZ para Vol %s ya presente. Saltando descarga...", vol)
        # Procedemos directamente a auditoría y conversión
    else:
        if not download_manga(
            params.url, folder, params.lang, "v", vol, vol, params.skip_oneshots
        ):
            return []

    # Auditoría (limpia archivos basura si es necesario) y Conversión
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
    # El conversor renombra el archivo para incluir el título de la serie
    mobi_name = f"{params.title} {suffix}.mobi"
    mobi_file = os.path.join(expected_output_dir, mobi_name)

    if os.path.exists(mobi_file):
        logger.info("%s.mobi ya existe. Saltando descarga y conversión...", suffix)
        return [mobi_file]
    else:

        # 2. --- SALTAR DESCARGA SI YA HAY CBZ ---
        existing_cbzs = glob.glob(os.path.join(folder, "*.cbz"))

        if existing_cbzs:
            logger.info("Archivos CBZ para el rango %s ya presentes. Saltando descarga...", suffix)
        else:
            if not download_manga(
                params.url,
                folder,
                params.lang,
                "c",
                params.start,
                params.end,
                params.skip_oneshots,
            ):
                return []

        # Auditoría y Conversión
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
