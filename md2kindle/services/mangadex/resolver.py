"""Lógica de negocio para la resolución de capítulos y descargas."""

def build_chapter_lang_map(volume, primary_lang, primary_aggregate, fallback_aggregates, lang_priority):
    """Construye un mapa {capítulo → idioma} para un volumen usando todos los idiomas disponibles.

    Para cada capítulo del volumen, elige el primer idioma de la cadena de prioridad
    que lo tenga disponible. Esto permite descargas mixtas cuando el idioma principal
    no tiene todos los capítulos.
    """
    # 1. Recopilar TODOS los capítulos del volumen en todos los idiomas
    all_chapters = set()
    lang_chapters = {}  # {lang: set(chapter_nums)}

    # Idioma principal
    if primary_aggregate and volume in primary_aggregate:
        vol_data = primary_aggregate[volume]
        chapters = set(vol_data.get("chapters", {}).keys())
        lang_chapters[primary_lang] = chapters
        all_chapters.update(chapters)

    # Fallbacks
    for fb_lang in lang_priority:
        if fb_lang in fallback_aggregates and volume in fallback_aggregates[fb_lang]:
            vol_data = fallback_aggregates[fb_lang][volume]
            chapters = set(vol_data.get("chapters", {}).keys())
            lang_chapters[fb_lang] = chapters
            all_chapters.update(chapters)

    if not all_chapters:
        return {}, False

    # 2. Asignar cada capítulo al mejor idioma disponible
    full_priority = [primary_lang] + lang_priority
    chapter_map = {}

    for chapter in all_chapters:
        for lang in full_priority:
            if lang in lang_chapters and chapter in lang_chapters[lang]:
                chapter_map[chapter] = lang
                break

    # 3. Determinar si es mixto
    unique_langs = set(chapter_map.values())
    is_mixed = len(unique_langs) > 1

    return chapter_map, is_mixed
