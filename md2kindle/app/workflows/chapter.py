"""Flujo de procesamiento para capítulos o rangos de capítulos."""

import logging
import os
import glob
import shutil

from md2kindle.core.config import APP_CONFIG, AppConfig
from md2kindle.core.ports import Converter
from md2kindle.core.models import PipelineContext
from md2kindle.services.mangadex import (
    download_manga,
    audit_and_cleanup,
)

logger = logging.getLogger(__name__)


from md2kindle.app.context import config_kwargs as _config_kwargs


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
