"""Orquestación del pipeline de descarga, conversión y entrega.

Extraído de cli.py para separar la lógica de ejecución del parsing de argumentos.
cli.py construye PipelineParams → pipeline.run() ejecuta.
"""

import logging
import os

from md2kindle.core.config import APP_CONFIG, AppConfig
from md2kindle.core.ports import Converter, Deliverer
from md2kindle.services.converter import KccConverter
from md2kindle.services.delivery.manager import DeliveryManager
from md2kindle.services.mangadex import (
    get_manga_aggregate,
)
from md2kindle.utils.ranges import parse_range
from md2kindle.core.models import PipelineContext
from md2kindle.app.workflows import process_volume_flow, process_chapter_flow

logger = logging.getLogger(__name__)


from md2kindle.app.context import config_kwargs as _config_kwargs


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
