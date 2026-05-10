from dataclasses import dataclass

@dataclass
class MangaContext:
    url: str
    title: str
    lang: str
    author: str
    manga_uuid: str | None
