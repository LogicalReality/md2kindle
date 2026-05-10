"""Flujo de procesamiento para volúmenes individuales."""

import logging
import os
import glob
import shutil

from md2kindle.core.config import APP_CONFIG, AppConfig
from md2kindle.core.ports import Converter
from md2kindle.core.models import PipelineContext
from md2kindle.services.mangadex import (
    build_chapter_lang_map,
    download_manga,
    download_volume_mixed,
    audit_and_cleanup,
)

logger = logging.getLogger(__name__)


from md2kindle.app.context import config_kwargs as _config_kwargs


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
