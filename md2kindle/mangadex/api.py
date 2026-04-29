"""Consultas a la API de MangaDex."""

import logging
import re
import json
import urllib.request
import urllib.parse

from md2kindle.config import sanitize_filename

logger = logging.getLogger(__name__)


def get_api_data(url):
    """Llamada genérica a la API con User-Agent para evitar bloqueos"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        # Silencioso para no romper el flujo principal si la API falla
        return None


def get_manga_title_options(url):
    """Consulta la API de MangaDex para obtener títulos, autor real y sugerencias de contexto"""
    suggestions = {"mode": None, "start": None, "vol": None, "lang": None}
    try:
        # 1. Validación y Extracción de UUID/Tipo
        # Soporta: /title/UUID, /manga/UUID, /chapter/UUID y versiones numéricas legacy
        match = re.search(r"(title|manga|chapter)/([a-f0-9-]{36}|[0-9]+)", url)
        if not match:
            return [], "MangaDex", suggestions, None

        link_type = match.group(1)
        uuid = match.group(2)
        manga_uuid = uuid

        # 2. Si es un capítulo, obtener primero el ID del manga y datos del capítulo
        if link_type == "chapter":
            logger.info("Detectada URL de capítulo. Buscando manga asociado...")
            chap_data = get_api_data(
                f"https://api.mangadex.org/chapter/{uuid}?includes[]=manga"
            )
            if chap_data and "data" in chap_data:
                attributes = chap_data["data"]["attributes"]
                suggestions["mode"] = "c"  # type: ignore
                suggestions["start"] = attributes.get("chapter")
                suggestions["vol"] = attributes.get("volume")
                suggestions["lang"] = attributes.get("translatedLanguage")

                # Buscar el ID del manga en las relaciones
                for rel in chap_data["data"]["relationships"]:
                    if rel["type"] == "manga":
                        manga_uuid = rel["id"]
                        break

        # 3. Consultar datos del Manga
        api_url = f"https://api.mangadex.org/manga/{manga_uuid}?includes[]=author"
        res = get_api_data(api_url)
        if not res or "data" not in res:
            return [], "MangaDex", suggestions, None

        res_data = res["data"]
        data = res_data["attributes"]
        relationships = res_data.get("relationships", [])

        # 4. Extraer Nombres de Autores (Multiautor)
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

        # Título principal y alternativos
        main_title = data.get("title", {})
        for lang, value in main_title.items():
            if lang in lang_map:
                options.append(
                    {"label": lang_map[lang], "title": sanitize_filename(value)}
                )

        alt_titles = data.get("altTitles", [])
        for alt in alt_titles:
            for lang, value in alt.items():
                if lang in lang_map:
                    options.append(
                        {"label": lang_map[lang], "title": sanitize_filename(value)}
                    )

        # Unificar y Ordenar
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

        return unique_options, author_name, suggestions, manga_uuid
    except Exception as e:
        logger.error("Error inesperado al procesar URL: %s", e)
        return [], "MangaDex", suggestions, None


def get_manga_aggregate(manga_uuid, lang):
    """Obtiene la estructura completa de Tomos y Capítulos desde MangaDex"""
    try:
        api_url = f"https://api.mangadex.org/manga/{manga_uuid}/aggregate?translatedLanguage[]={lang}"
        data = get_api_data(api_url)
        if data and data.get("result") == "ok":
            return data.get("volumes", {})
        return {}
    except Exception as e:
        logger.warning("No se pudo obtener la estructura de auditoría: %s", e)
        return {}
