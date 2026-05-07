"""Orquestación del pipeline de descarga, conversión y entrega.

Extraído de cli.py para separar la lógica de ejecución del parsing de argumentos.
cli.py construye PipelineParams → pipeline.run() ejecuta.
"""

import logging
import os
import glob
import shutil

from md2kindle.config import APP_CONFIG, AppConfig
from md2kindle.converter import convert_with_kcc
from md2kindle.delivery.service import deliver_files
from md2kindle.mangadex import (
    get_manga_aggregate,
    build_chapter_lang_map,
    parse_range,
    download_manga,
    download_volume_mixed,
    audit_and_cleanup,
)
from md2kindle.models import PipelineParams

logger = logging.getLogger(__name__)


def _config_kwargs(explicit_config: bool, app_config: AppConfig) -> dict:
    """Pasa AppConfig solo cuando el caller lo inyectó explícitamente."""
    return {"app_config": app_config} if explicit_config else {}


def process_volume_flow(
    params: PipelineParams, vol: str, base_path: str,
    aggregate_data: dict, fallback_aggregates: dict, lang_priority: list[str],
    app_config: AppConfig | None = None,
) -> list[str]:
    """Procesa un volumen individual: descarga → auditoría → conversión y retorna archivos.

    Usa fallback per-chapter: si el idioma principal no tiene todos los capítulos
    del volumen, descarga los faltantes del siguiente idioma en la cadena de prioridad.
    """
    explicit_config = app_config is not None
    app_config = app_config or APP_CONFIG
    config_kwargs = _config_kwargs(explicit_config, app_config)

    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.title, f"Vol {vol}")
    expected_output_dir = os.path.join(app_config.output_folder_kcc, rel_path)
    mobi_name = f"{params.title} Vol. {vol}.mobi"
    mobi_file = os.path.join(expected_output_dir, mobi_name)

    if os.path.exists(mobi_file):
        logger.info("%s ya existe. Saltando descarga y conversión...", mobi_name)
        return [mobi_file]

    folder = os.path.join(base_path, f"Vol {vol}")
    os.makedirs(folder, exist_ok=True)

    # --- SALTAR DESCARGA SI YA HAY CBZ ---
    existing_cbzs = glob.glob(os.path.join(folder, "*.cbz"))

    if existing_cbzs:
        logger.info("CBZ para Vol %s ya presente. Saltando descarga...", vol)
    else:
        # Construir mapa capítulo→idioma para fallback granular
        chapter_map, is_mixed = build_chapter_lang_map(
            vol, params.lang, aggregate_data, fallback_aggregates, lang_priority,
        )

        if is_mixed and chapter_map:
            # Descarga mixta: múltiples idiomas por capítulo
            download_ok = download_volume_mixed(
                params.url,
                folder,
                chapter_map,
                params.skip_oneshots,
                vol=vol,
                **config_kwargs,
            )
            if not download_ok:
                return []
        else:
            # Descarga normal: un solo idioma
            # Si el mapa determinó que todo viene de un fallback, usar ese idioma
            download_lang = params.lang
            if chapter_map:
                unique_lang = set(chapter_map.values())
                if len(unique_lang) == 1:
                    resolved_lang = next(iter(unique_lang))
                    if resolved_lang != params.lang:
                        logger.info(
                            "Vol %s no hallado en '%s'. Usando fallback: '%s'",
                            vol, params.lang, resolved_lang,
                        )
                        download_lang = resolved_lang

            download_ok = download_manga(
                params.url,
                folder,
                download_lang,
                "v",
                vol,
                vol,
                params.skip_oneshots,
                **config_kwargs,
            )
            if not download_ok:
                return []

    # Auditoría (limpia archivos basura si es necesario) y Conversión
    audit_and_cleanup(
        folder, aggregate_data, "v", vol, vol, params.skip_oneshots,
    )

    cbz_files = glob.glob(os.path.join(folder, "*.cbz"))
    if not cbz_files:
        logger.warning("No se generaron archivos .cbz para el Vol %s. Limpiando...", vol)
        shutil.rmtree(folder, ignore_errors=True)
        return []

    mobi_list = convert_with_kcc(
        folder, params.author, params.title, vol_hint=vol, **config_kwargs
    )
    return mobi_list or []



def process_chapter_flow(
    params: PipelineParams,
    base_path: str,
    aggregate_data: dict,
    app_config: AppConfig | None = None,
) -> list[str]:
    """Procesa un rango de capítulos: descarga → auditoría → conversión y retorna archivos."""
    explicit_config = app_config is not None
    app_config = app_config or APP_CONFIG
    config_kwargs = _config_kwargs(explicit_config, app_config)
    suffix = f"Cap {params.start}" + (
        f"-{params.end}" if params.start != params.end else ""
    )
    folder = os.path.join(base_path, suffix)

    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.title, suffix)
    expected_output_dir = os.path.join(app_config.output_folder_kcc, rel_path)
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
            download_ok = download_manga(
                params.url,
                folder,
                params.lang,
                "c",
                params.start,
                params.end,
                params.skip_oneshots,
                **config_kwargs,
            )
            if not download_ok:
                return []
            
            # Renombrar "All chapters.cbz" a un nombre más descriptivo
            all_ch_cbz = os.path.join(folder, "All chapters.cbz")
            if os.path.exists(all_ch_cbz):
                os.rename(all_ch_cbz, os.path.join(folder, f"{suffix}.cbz"))

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

        mobi_list = convert_with_kcc(
            folder, params.author, params.title, vol_hint=suffix, **config_kwargs
        )
        return mobi_list or []
        
        return []



def run(params: PipelineParams, app_config: AppConfig | None = None) -> None:
    """Ejecuta el pipeline completo con los parámetros resueltos."""
    explicit_config = app_config is not None
    app_config = app_config or APP_CONFIG
    config_kwargs = _config_kwargs(explicit_config, app_config)
    base_path = os.path.join(app_config.output_folder_manga, params.title)

    aggregate_data = {}
    fallback_aggregates = {}
    lang_priority = ["es-la", "en", "es"]
    if params.lang in lang_priority:
        lang_priority.remove(params.lang)

    if params.manga_uuid:
        logger.info("Consultando estructura de MangaDex para auditoría y fallbacks...")
        aggregate_data = get_manga_aggregate(params.manga_uuid, params.lang)

        for fb_lang in lang_priority:
            fb_data = get_manga_aggregate(params.manga_uuid, fb_lang)
            if fb_data:
                fallback_aggregates[fb_lang] = fb_data

    all_mobi_files = []

    if params.mode == "v":
        volumes = parse_range(params.start, params.end)
        logger.info("Detectado modo VOLUMEN. Procesando %d tomo(s) individualmente...", len(volumes))

        for vol in volumes:
            generated = process_volume_flow(
                params,
                vol,
                base_path,
                aggregate_data,
                fallback_aggregates,
                lang_priority,
                **config_kwargs,
            )
            all_mobi_files.extend(generated)
    else:
        if not aggregate_data:
            for fb_lang in lang_priority:
                if fb_lang in fallback_aggregates:
                    logger.info("Idioma '%s' sin datos. Usando fallback global: '%s'", params.lang, fb_lang)
                    params.lang = fb_lang
                    aggregate_data = fallback_aggregates[fb_lang]
                    break

        generated = process_chapter_flow(
            params, base_path, aggregate_data, **config_kwargs
        )
        all_mobi_files.extend(generated)

    deliver_files(all_mobi_files, params, **config_kwargs)

    logger.info("=========================================")
    logger.info(
        " Proceso Finalizado. Archivos generados en:\n %s",
        app_config.output_folder_kcc,
    )
    logger.info("=========================================")
