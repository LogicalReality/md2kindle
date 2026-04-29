"""Interfaz CLI y modo interactivo — solo parsing de parámetros.

La orquestación del pipeline está en pipeline.py.
cli.py → PipelineParams → pipeline.run()
"""

import logging
import os
import sys
import argparse
import shutil

from md2kindle.models import PipelineParams
from md2kindle.config import (
    clear_screen,
    DEFAULT_LANGUAGE,
    MANGADEX_DL_PATH,
    KCC_C2E_PATH,
)
from md2kindle.mangadex import get_manga_title_options
from md2kindle.log_config import setup_logging
from md2kindle import pipeline

logger = logging.getLogger(__name__)


def resolve_parameters() -> PipelineParams:
    """Resuelve los parámetros del script (CLI -> Inferencia -> Interactivo)"""
    parser = argparse.ArgumentParser(description="MangaDex to Kindle CLI Converter")
    parser.add_argument("url", nargs="?", help="URL de MangaDex (manga o capítulo)")
    parser.add_argument("--title", help="Nombre de la carpeta del manga")
    parser.add_argument("--lang", help="Idioma (es-la, en, es)")
    parser.add_argument(
        "--mode", choices=["v", "c"], help="Modo: v (volumen) o c (capítulo)"
    )
    parser.add_argument("--start", help="Número inicial (volumen o capítulo)")
    parser.add_argument("--end", help="Número final (volumen o capítulo)")
    parser.add_argument(
        "--skip-oneshots", action="store_true", help="Omitir capítulos oneshot"
    )
    parser.add_argument(
        "--silent", action="store_true", help="Modo silencioso (menos logs)"
    )
    parser.add_argument(
        "--telegram", action="store_true", help="Enviar archivos generados a Telegram"
    )

    args, unknown = parser.parse_known_args()

    # 1. ¿Estamos en modo CLI puro o interactivo?
    is_interactive = len(sys.argv) <= 1

    # URL (Requerido o Interactivo)
    url = args.url
    if not url and is_interactive:
        clear_screen()
        print("=========================================")
        print(" MangaDex -> Kindle Converter (md2kindle)")
        print("=========================================")
        url = input("\n> URL de MangaDex: ").strip()
    elif not url:
        print("[ERROR] Se requiere la --url en modo no interactivo.")
        sys.exit(1)

    # Inferencia inteligente desde la URL
    options, author_name, suggestions, manga_uuid = get_manga_title_options(url)

    # Redirección Canónica
    download_url = f"https://mangadex.org/title/{manga_uuid}" if manga_uuid else url

    # --- Título / Carpeta ---
    title = args.title
    if not title:
        if is_interactive and options:
            print(f"\nAutor(es) detectado(s): {author_name}")
            print("Selecciona el nombre para la carpeta del manga:")
            for i, opt in enumerate(options, 1):
                label_display = f"[{opt['label']}]"
                print(f"  {i}. {label_display:<18} {opt['title']}")
            print(
                f"  {len(options) + 1}. [Manual]           Escribir nombre personalizado..."
            )

            choice = input(f"\nSelecciona una opción [1]: ").strip()
            if not choice:
                title = options[0]["title"]
            elif choice.isdigit() and 1 <= int(choice) <= len(options):
                title = options[int(choice) - 1]["title"]
            else:
                title = (
                    input("> Nombre de la carpeta: ").strip()
                    if choice.lower() != str(len(options) + 1)
                    else input("> Nombre de la carpeta: ").strip()
                )
        elif options:
            title = options[0]["title"]  # Autopick el primero en CLI
        else:
            title = manga_uuid if manga_uuid else "Manga_Sin_Nombre"

    # --- Idioma con Fallback Inteligente ---
    # Prioridad: es-la -> en -> es
    lang_priority = ["es-la", "en", "es"]
    lang = args.lang

    if not lang:
        suggested_lang = suggestions.get("lang")
        if (
            requested_lang := suggested_lang
            if suggested_lang in lang_priority
            else None
        ):
            lang = requested_lang
        elif is_interactive:
            print(f"\n[Fallback] Idioma sugerido: {DEFAULT_LANGUAGE}")
            lang_input = input(f"> Idioma [Enter para '{DEFAULT_LANGUAGE}']: ").strip()
            lang = lang_input if lang_input else DEFAULT_LANGUAGE
        else:
            lang = DEFAULT_LANGUAGE

    # --- Modo y Rangos ---
    mode = args.mode
    if not mode:
        mode = suggestions.get("mode") or "v"
        if is_interactive:
            mode_input = input(f"> Modo [(v)ol / (c)ap] [{mode}]: ").strip().lower()
            if mode_input:
                mode = "v" if mode_input in ["v", "vol"] else "c"

    start = args.start
    if not start:
        sug_start = suggestions.get("start") if mode == "c" else suggestions.get("vol")
        if is_interactive:
            start_prompt = (
                f"> Número inicial" + (f" [{sug_start}]" if sug_start else "") + ": "
            )
            start = input(start_prompt).strip() or sug_start
        else:
            start = sug_start if sug_start else "1"

    end = args.end
    if not end:
        if is_interactive:
            end = input(f"> Número final [Enter para '{start}']: ").strip() or start
        else:
            end = start

    skip_oneshots = (
        args.skip_oneshots
        if not is_interactive
        else (
            input("> ¿Excluir capítulos 'Oneshot' / Promocionales? [S/n]: ")
            .strip()
            .lower()
            != "n"
        )
    )
    silent = args.silent

    return PipelineParams(
        url=download_url,
        title=title,
        lang=lang,
        mode=mode,
        start=start,
        end=end,
        author=author_name,
        manga_uuid=manga_uuid,
        skip_oneshots=skip_oneshots,
        silent=silent,
        telegram=args.telegram,
    )


def main():
    # Verificación de binarios mejorada (Considera PATH)
    has_md_dl = os.path.exists(MANGADEX_DL_PATH) or shutil.which("mangadex-dl")
    has_kcc = os.path.exists(KCC_C2E_PATH) or shutil.which("kcc-c2e")

    if not has_md_dl or not has_kcc:
        print(f"[ERROR] No se encontraron los binarios necesarios.")
        print(f"  MangaDex-DL: {'OK' if has_md_dl else 'FALTA'}")
        print(f"  KCC-C2E: {'OK' if has_kcc else 'FALTA'}")
        return

    params = resolve_parameters()

    # Configurar logging DESPUÉS de resolver parámetros (necesitamos saber si --silent)
    setup_logging(silent=params.silent)

    pipeline.run(params)
