"""Cliente HTTP puro para MangaDex API."""

import logging
import json
import urllib.request

logger = logging.getLogger(__name__)

def fetch_json(url: str) -> dict | None:
    """Llamada genérica a la API con User-Agent para evitar bloqueos"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        # Silencioso para no romper el flujo principal si la API falla
        return None

def get_manga(manga_uuid: str) -> dict | None:
    api_url = f"https://api.mangadex.org/manga/{manga_uuid}?includes[]=author"
    return fetch_json(api_url)

def get_chapter(chapter_uuid: str) -> dict | None:
    api_url = f"https://api.mangadex.org/chapter/{chapter_uuid}?includes[]=manga"
    return fetch_json(api_url)

def get_aggregate(manga_uuid: str, lang: str) -> dict | None:
    api_url = f"https://api.mangadex.org/manga/{manga_uuid}/aggregate?translatedLanguage[]={lang}"
    return fetch_json(api_url)
