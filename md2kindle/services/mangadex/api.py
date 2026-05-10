"""Fachada de compatibilidad para consultas a la API de MangaDex."""

import logging
from md2kindle.services.mangadex.client import get_manga, get_chapter, get_aggregate
from md2kindle.services.mangadex.parser import extract_uuid_from_url, parse_chapter_data, parse_manga_data, parse_aggregate_data
from md2kindle.services.mangadex.resolver import build_chapter_lang_map

logger = logging.getLogger(__name__)

def get_manga_title_options(url):
    """Consulta la API de MangaDex para obtener títulos, autor real y sugerencias de contexto"""
    suggestions: dict[str, str | None] = {"mode": None, "start": None, "vol": None, "lang": None}
    try:
        link_type, uuid = extract_uuid_from_url(url)
        if not link_type or not uuid:
            return [], "MangaDex", suggestions, None

        manga_uuid = uuid

        if link_type == "chapter":
            logger.info("Detectada URL de capítulo. Buscando manga asociado...")
            chap_data = get_chapter(uuid)
            if chap_data:
                start, vol, lang, rel_manga_uuid = parse_chapter_data(chap_data)
                
                suggestions["mode"] = "c"
                suggestions["start"] = start
                suggestions["vol"] = vol
                suggestions["lang"] = lang
                
                if rel_manga_uuid:
                    manga_uuid = rel_manga_uuid

        manga_data = get_manga(manga_uuid)
        if not manga_data:
            return [], "MangaDex", suggestions, manga_uuid

        unique_options, author_name = parse_manga_data(manga_data)

        return unique_options, author_name, suggestions, manga_uuid
    except Exception as e:
        logger.error("Error inesperado al procesar URL: %s", e)
        return [], "MangaDex", suggestions, None

def get_manga_aggregate(manga_uuid, lang):
    """Obtiene la estructura completa de Tomos y Capítulos desde MangaDex"""
    try:
        data = get_aggregate(manga_uuid, lang)
        if data:
            return parse_aggregate_data(data)
        return {}
    except Exception as e:
        logger.warning("No se pudo obtener la estructura de auditoría: %s", e)
        return {}

__all__ = ["get_manga_title_options", "get_manga_aggregate", "build_chapter_lang_map"]
