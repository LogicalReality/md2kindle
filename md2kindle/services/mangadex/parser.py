"""Lógica de extracción de datos de las respuestas de MangaDex."""

import logging
import re
from md2kindle.core.config import sanitize_filename

logger = logging.getLogger(__name__)

def extract_uuid_from_url(url: str) -> tuple[str, str] | tuple[None, None]:
    """Extrae el tipo de enlace y el UUID de una URL de MangaDex."""
    match = re.search(r"(title|manga|chapter)/([a-f0-9-]{36}|[0-9]+)", url)
    if not match:
        return None, None
    return match.group(1), match.group(2)

def parse_chapter_data(chap_data: dict) -> tuple[str | None, str | None, str | None, str | None]:
    """Extrae start, vol, lang y manga_uuid de los datos de un capítulo."""
    if not chap_data or "data" not in chap_data:
        return None, None, None, None
        
    attributes = chap_data["data"].get("attributes", {})
    start = attributes.get("chapter")
    vol = attributes.get("volume")
    lang = attributes.get("translatedLanguage")
    
    manga_uuid = None
    for rel in chap_data["data"].get("relationships", []):
        if rel["type"] == "manga":
            manga_uuid = rel["id"]
            break
            
    return start, vol, lang, manga_uuid

def parse_manga_data(manga_data: dict) -> tuple[list[dict], str]:
    """Extrae opciones de títulos y el autor de los datos de un manga."""
    if not manga_data or "data" not in manga_data:
        return [], "MangaDex"
        
    res_data = manga_data["data"]
    data = res_data.get("attributes", {})
    relationships = res_data.get("relationships", [])

    authors = []
    for rel in relationships:
        if rel["type"] == "author" and "attributes" in rel:
            authors.append(rel["attributes"]["name"])

    author_name = " & ".join(authors) if authors else "MangaDex"

    options = []
    lang_map = {
        "ja-ro": "Romaji",
        "en": "English",
        "es-la": "Spanish (Latino)",
        "es": "Spanish",
    }

    main_title = data.get("title", {})
    for lang, value in main_title.items():
        if lang in lang_map:
            options.append({"label": lang_map[lang], "title": sanitize_filename(value)})

    alt_titles = data.get("altTitles", [])
    for alt in alt_titles:
        for lang, value in alt.items():
            if lang in lang_map:
                options.append({"label": lang_map[lang], "title": sanitize_filename(value)})

    seen = set()
    unique_options = []
    for opt in options:
        if opt["title"].lower() not in seen:
            seen.add(opt["title"].lower())
            unique_options.append(opt)

    priority = ["ja-ro", "en", "es-la", "es"]
    unique_options.sort(
        key=lambda x: (
            priority.index(next(k for k, v in lang_map.items() if v == x["label"]))
            if any(v == x["label"] for v in lang_map.values())
            else 99
        )
    )

    return unique_options, author_name

def parse_aggregate_data(data: dict) -> dict:
    """Extrae los volúmenes del payload de aggregate."""
    if data and data.get("result") == "ok":
        volumes = data.get("volumes", {})
        return volumes if isinstance(volumes, dict) else {}
    return {}
