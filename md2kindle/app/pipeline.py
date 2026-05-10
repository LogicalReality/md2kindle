"""Orquestación del pipeline de descarga, conversión y entrega.

Extraído de cli.py para separar la lógica de ejecución del parsing de argumentos.
cli.py construye PipelineParams → pipeline.run() ejecuta.
"""

import logging
import os
import glob
import shutil

from md2kindle.core.config import APP_CONFIG, AppConfig
from md2kindle.core.ports import Converter, Deliverer
from md2kindle.services.converter import KccConverter
from md2kindle.services.delivery.manager import DeliveryManager
from md2kindle.services.mangadex import (
    get_manga_aggregate,
    build_chapter_lang_map,
    parse_range,
    download_manga,
    download_volume_mixed,
    audit_and_cleanup,
)
from md2kindle.core.models import PipelineContext

logger = logging.getLogger(__name__)


def _config_kwargs(explicit_config: bool, app_config: AppConfig) -> dict:
    """Pasa AppConfig solo cuando el caller lo inyectó explícitamente."""
    return {"app_config": app_config} if explicit_config else {}


def process_volume_flow(
    params: PipelineContext, vol: str, base_path: str,
    aggregate_data: dict, fallback_aggregates: dict, lang_priority: list[str],
    converter: Converter,
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
    rel_path = os.path.join(params.manga.title, f"Vol {vol}")
    expected_output_dir = os.path.join(app_config.output_folder_kcc, rel_path)
    mobi_name = f"{params.manga.title} Vol. {vol}.mobi"
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
            vol, params.manga.lang, aggregate_data, fallback_aggregates, lang_priority,
        )

        if is_mixed and chapter_map:
            # Descarga mixta: múltiples idiomas por capítulo
            download_ok = download_volume_mixed(
                params.manga.url,
                folder,
                chapter_map,
                params.range.skip_oneshots,
                vol=vol,
                **config_kwargs,
            )
            if not download_ok:
                return []
        else:
            # Descarga normal: un solo idioma
            # Si el mapa determinó que todo viene de un fallback, usar ese idioma
            download_lang = params.manga.lang
            if chapter_map:
                unique_lang = set(chapter_map.values())
                if len(unique_lang) == 1:
                    resolved_lang = next(iter(unique_lang))
                    if resolved_lang != params.manga.lang:
                        logger.info(
                            "Vol %s no hallado en '%s'. Usando fallback: '%s'",
                            vol, params.manga.lang, resolved_lang,
                        )
                        download_lang = resolved_lang

            download_ok = download_manga(
                params.manga.url,
                folder,
                download_lang,
                "v",
                vol,
                vol,
                params.range.skip_oneshots,
                **config_kwargs,
            )
            if not download_ok:
                return []

    # Auditoría (limpia archivos basura si es necesario) y Conversión
    audit_and_cleanup(
        folder, aggregate_data, "v", vol, vol, params.range.skip_oneshots,
    )

    cbz_files = glob.glob(os.path.join(folder, "*.cbz"))
    if not cbz_files:
        logger.warning("No se generaron archivos .cbz para el Vol %s. Limpiando...", vol)
        shutil.rmtree(folder, ignore_errors=True)
        return []

    mobi_list = converter.convert(
        target_path=folder,
        author=params.manga.author,
        title=params.manga.title,
        vol_hint=vol,
    )
    return mobi_list or []



def process_chapter_flow(
    params: PipelineContext,
    base_path: str,
    aggregate_data: dict,
    converter: Converter,
    app_config: AppConfig | None = None,
) -> list[str]:
    """Procesa un rango de capítulos: descarga → auditoría → conversión y retorna archivos."""
    explicit_config = app_config is not None
    app_config = app_config or APP_CONFIG
    config_kwargs = _config_kwargs(explicit_config, app_config)
    suffix = f"Cap {params.range.start}" + (
        f"-{params.range.end}" if params.range.start != params.range.end else ""
    )
    folder = os.path.join(base_path, suffix)

    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(params.manga.title, suffix)
    expected_output_dir = os.path.join(app_config.output_folder_kcc, rel_path)
    # El conversor renombra el archivo para incluir el título de la serie
    mobi_name = f"{params.manga.title} {suffix}.mobi"
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
                params.manga.url,
                folder,
                params.manga.lang,
                "c",
                params.range.start,
                params.range.end,
                params.range.skip_oneshots,
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
            params.range.start,
            params.range.end,
            params.range.skip_oneshots,
        )

        cbz_files = glob.glob(os.path.join(folder, "*.cbz"))
        if not cbz_files:
            logger.warning("No se generaron archivos .cbz para el rango de capítulos. Limpiando...")
            shutil.rmtree(folder, ignore_errors=True)
            return []

        mobi_list = converter.convert(
            target_path=folder,
            author=params.manga.author,
            title=params.manga.title,
            vol_hint=suffix,
        )
        return mobi_list or []



def run(
    params: PipelineContext,
    converter: Converter | None = None,
    deliverer: Deliverer | None = None,
    app_config: AppConfig | None = None,
) -> None:
    """Ejecuta el pipeline completo con los parámetros resueltos."""
    explicit_config = app_config is not None
    app_config = app_config or APP_CONFIG
    converter = converter or KccConverter(app_config)
    deliverer = deliverer or DeliveryManager(app_config)

    config_kwargs = _config_kwargs(explicit_config, app_config)
    base_path = os.path.join(app_config.output_folder_manga, params.manga.title)

    aggregate_data = {}
    fallback_aggregates = {}
    # La lista de idiomas candidatos viene de la configuración, no del código
    lang_priority = [lang for lang in app_config.language_fallback_pool if lang != params.manga.lang]

    if params.manga.manga_uuid:
        logger.info("Consultando estructura de MangaDex para auditoría y fallbacks...")
        aggregate_data = get_manga_aggregate(params.manga.manga_uuid, params.manga.lang)

        for fb_lang in lang_priority:
            fb_data = get_manga_aggregate(params.manga.manga_uuid, fb_lang)
            if fb_data:
                fallback_aggregates[fb_lang] = fb_data

    all_mobi_files = []

    if params.range.mode == "v":
        volumes = parse_range(params.range.start, params.range.end)
        logger.info("Detectado modo VOLUMEN. Procesando %d tomo(s) individualmente...", len(volumes))

        for vol in volumes:
            generated = process_volume_flow(
                params,
                vol,
                base_path,
                aggregate_data,
                fallback_aggregates,
                lang_priority,
                converter=converter,
                **config_kwargs,
            )
            all_mobi_files.extend(generated)
    else:
        # Evitar mutar params: usar variable local para el idioma resuelto
        resolved_lang = params.manga.lang
        if not aggregate_data:
            for fb_lang in lang_priority:
                if fb_lang in fallback_aggregates:
                    logger.info("Idioma '%s' sin datos. Usando fallback global: '%s'", params.manga.lang, fb_lang)
                    resolved_lang = fb_lang
                    aggregate_data = fallback_aggregates[fb_lang]
                    break

        # Construir contexto ajustado sin mutar el original
        chapter_params = params
        if resolved_lang != params.manga.lang:
            from dataclasses import replace
            chapter_params = replace(params, manga=replace(params.manga, lang=resolved_lang))

        generated = process_chapter_flow(
            chapter_params, base_path, aggregate_data, converter=converter, **config_kwargs
        )
        all_mobi_files.extend(generated)

    deliverer.deliver(all_mobi_files, params)

    logger.info("=========================================")
    logger.info(
        " Proceso Finalizado. Archivos generados en:\n %s",
        app_config.output_folder_kcc,
    )
    logger.info("=========================================")
