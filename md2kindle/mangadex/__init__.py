"""Subpackage para integración con MangaDex (API + downloader)."""

from md2kindle.mangadex.api import (
    get_manga_title_options,
    get_manga_aggregate,
    build_chapter_lang_map,
)
from md2kindle.mangadex.downloader import (
    parse_range,
    download_manga,
    download_volume_mixed,
    audit_and_cleanup,
)

__all__ = [
    "get_manga_title_options",
    "get_manga_aggregate",
    "build_chapter_lang_map",
    "parse_range",
    "download_manga",
    "download_volume_mixed",
    "audit_and_cleanup",
]
