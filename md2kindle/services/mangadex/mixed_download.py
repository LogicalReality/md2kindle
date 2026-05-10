"""Orquestación de descargas mixtas por idioma y empaquetado final."""

import logging
import os
import subprocess
import shutil
import zipfile

from md2kindle.core.config import APP_CONFIG, AppConfig
from md2kindle.core.exceptions import DownloadError

logger = logging.getLogger(__name__)


def _group_contiguous_ranges(chapters):
    """Agrupa capítulos en rangos contiguos para minimizar llamadas a mangadex-dl.

    Chapters como ['51','52','53','55','56'] → [('51','53'), ('55','56')]
    """
    if not chapters:
        return []

    def sort_key(ch):
        try:
            return float(ch)
        except ValueError:
            return 999

    sorted_chs = sorted(chapters, key=sort_key)
    ranges = []
    start = sorted_chs[0]
    prev = sorted_chs[0]

    for ch in sorted_chs[1:]:
        try:
            gap = float(ch) - float(prev)
        except ValueError:
            gap = 999
        if gap > 1.0:
            ranges.append((start, prev))
            start = ch
        prev = ch

    ranges.append((start, prev))
    return ranges


def download_volume_mixed(
    url,
    target_path,
    chapter_lang_map,
    skip_oneshots=False,
    vol=None,
    app_config: AppConfig | None = None,
):
    """Descarga un volumen usando múltiples idiomas según el mapa capítulo→idioma.

    Agrupa capítulos por idioma, encuentra rangos contiguos dentro de cada grupo,
    y ejecuta mangadex-dl una vez por rango para minimizar llamadas.

    Args:
        url: URL del manga en MangaDex.
        target_path: Carpeta destino para los CBZ.
        chapter_lang_map: Dict {chapter_num: lang} del mapa de capítulos.
        skip_oneshots: Si se deben saltar oneshots.

    Returns:
        True si al menos una descarga fue exitosa.
    """
    app_config = app_config or APP_CONFIG

    # 1. Agrupar capítulos por idioma
    lang_groups: dict[str, list[str]] = {}
    for chapter, lang in chapter_lang_map.items():
        lang_groups.setdefault(lang, []).append(chapter)

    # 2. Log resumen
    summary_parts = []
    for lang in sorted(lang_groups.keys()):
        chs = sorted(lang_groups[lang], key=lambda x: float(x) if x.replace(".", "", 1).isdigit() else 999)
        if len(chs) <= 3:
            ch_str = ", ".join(chs)
        else:
            ch_str = f"{chs[0]}-{chs[-1]}"
        summary_parts.append(f"{ch_str} ({lang})")
    logger.info("Descarga mixta: %s", " | ".join(summary_parts))

    # 3. Descargar cada grupo
    any_success = False
    for lang, chapters in lang_groups.items():
        ranges = _group_contiguous_ranges(chapters)
        for start_ch, end_ch in ranges:
            cmd = [
                app_config.binaries.mangadex_dl,
                url,
                "--save-as", "raw",
                "--language", lang,
                "--start-chapter", start_ch,
                "--end-chapter", end_ch,
            ]
            if skip_oneshots:
                cmd.append("--no-oneshot-chapter")
            cmd.extend(["--path", target_path])

            logger.info("Descargando caps %s-%s en '%s'...", start_ch, end_ch, lang)
            try:
                result = subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                if result.returncode == 0:
                    any_success = True
                else:
                    logger.warning("Falló descarga de caps %s-%s en '%s'", start_ch, end_ch, lang)
            except Exception as e:
                logger.error("Excepción al descargar caps %s-%s: %s", start_ch, end_ch, e)
                raise DownloadError(f"Fallo crítico en descarga de caps {start_ch}-{end_ch}: {e}") from e

    # 4. Empaquetar todo en un único CBZ para que KCC lo procese como un volumen
    if any_success:
        cbz_name = f"Vol {vol}.cbz" if vol else "All chapters.cbz"
        cbz_path = os.path.join(target_path, cbz_name)
        if os.path.exists(cbz_path):
            os.remove(cbz_path)

        # Comprimir las carpetas raw en el zip
        try:
            with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        if file == cbz_name:
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, target_path)
                        zipf.write(file_path, arcname)

            # Eliminar las carpetas y archivos raw (Ch. X, cover.jpg, etc.)
            for item in os.listdir(target_path):
                if item == cbz_name:
                    continue
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info("Empaquetado exitoso: %s", cbz_path)
        except Exception as e:
            logger.error("Error al empaquetar CBZ mixto: %s", e)
            raise DownloadError(f"Fallo al empaquetar volumen mixto: {e}") from e

    return any_success
