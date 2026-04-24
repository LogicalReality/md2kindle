"""Interfaz CLI, modo interactivo y orquestación principal."""

import os
import sys
import argparse
import shutil

from md2kindle.config import (
    clear_screen,
    DEFAULT_LANGUAGE,
    MANGADEX_DL_PATH,
    KCC_C2E_PATH,
    OUTPUT_FOLDER_MANGA,
    OUTPUT_FOLDER_KCC,
)
from md2kindle.api import get_manga_title_options, get_manga_aggregate
from md2kindle.downloader import parse_range, download_manga, audit_and_cleanup
from md2kindle.converter import convert_with_kcc
from md2kindle.delivery import send_to_telegram


def resolve_parameters():
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

    return {
        "url": download_url,
        "title": title,
        "lang": lang,
        "mode": mode,
        "start": start,
        "end": end,
        "author": author_name,
        "manga_uuid": manga_uuid,
        "skip_oneshots": skip_oneshots,
        "silent": silent,
        "telegram": args.telegram,
    }


def process_volume_flow(p, vol, base_path, aggregate_data):
    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(p["title"], f"Vol {vol}")
    expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
    # El nombre del CBZ suele ser "Vol. X.cbz" -> "Vol. X.mobi"
    mobi_name = f"Vol. {vol}.mobi"
    mobi_file = os.path.join(expected_output_dir, mobi_name)

    if os.path.exists(mobi_file):
        if not p["silent"]:
            print(f"[*] {mobi_name} ya existe. Saltando descarga y conversión...")
        if p["telegram"]:
            send_to_telegram(mobi_file)
        return

    folder = os.path.join(base_path, f"Vol {vol}")
    os.makedirs(folder, exist_ok=True)
    if download_manga(
        p["url"], folder, p["lang"], "v", vol, vol, p["skip_oneshots"]
    ):
        audit_and_cleanup(
            folder, aggregate_data, "v", vol, vol, p["skip_oneshots"]
        )
        mobi_list = convert_with_kcc(folder, p["author"], p["title"])
        if p["telegram"] and mobi_list:
            for m in mobi_list:
                send_to_telegram(m)


def process_chapter_flow(p, base_path, aggregate_data):
    suffix = f"Cap {p['start']}" + (
        f"-{p['end']}" if p["start"] != p["end"] else ""
    )
    folder = os.path.join(base_path, suffix)

    # --- SALTAR SI YA EXISTE ---
    rel_path = os.path.join(p["title"], suffix)
    expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
    # En modo capitulo agrupado, KCC genera un MOBI con el nombre de la carpeta
    mobi_file = os.path.join(expected_output_dir, suffix + ".mobi")

    if os.path.exists(mobi_file):
        if not p["silent"]:
            print(f"[*] {suffix}.mobi ya existe. Saltando descarga y conversión...")
        if p["telegram"]:
            send_to_telegram(mobi_file)
    else:
        os.makedirs(folder, exist_ok=True)
        if not p["silent"]:
            print(
                f"\n[*] Detectado modo CAPÍTULO. Agrupando rango {p['start']}-{p['end']}..."
            )
        if download_manga(
            p["url"],
            folder,
            p["lang"],
            "c",
            p["start"],
            p["end"],
            p["skip_oneshots"],
        ):
            audit_and_cleanup(
                folder,
                aggregate_data,
                "c",
                p["start"],
                p["end"],
                p["skip_oneshots"],
            )
            mobi_list = convert_with_kcc(folder, p["author"], p["title"])
            if p["telegram"] and mobi_list:
                for m in mobi_list:
                    send_to_telegram(m)


def main():
    # Verificación de binarios mejorada (Considera PATH)
    has_md_dl = os.path.exists(MANGADEX_DL_PATH) or shutil.which("mangadex-dl")
    has_kcc = os.path.exists(KCC_C2E_PATH) or shutil.which("kcc-c2e")

    if not has_md_dl or not has_kcc:
        print(f"[ERROR] No se encontraron los binarios necesarios.")
        print(f"  MangaDex-DL: {'OK' if has_md_dl else 'FALTA'}")
        print(f"  KCC-C2E: {'OK' if has_kcc else 'FALTA'}")
        return

    p = resolve_parameters()
    base_path = os.path.join(OUTPUT_FOLDER_MANGA, p["title"])

    # FASE 2: Obtener data de auditoria preventivamente
    aggregate_data = {}
    if p["manga_uuid"]:
        if not p["silent"]:
            print(f"\n[*] Consultando estructura de MangaDex para auditoría...")
        aggregate_data = get_manga_aggregate(p["manga_uuid"], p["lang"])

    # --- Lógica de Fallback de Idioma Automático ---
    if p["manga_uuid"] and not aggregate_data:
        fallback_list = ["es-la", "en", "es"]
        if p["lang"] in fallback_list:
            fallback_list.remove(p["lang"])

        for fb_lang in fallback_list:
            if not p["silent"]:
                print(
                    f"[*] Idioma '{p['lang']}' no disponible o sin capítulos. Probando fallback: {fb_lang}..."
                )
            aggregate_data = get_manga_aggregate(p["manga_uuid"], fb_lang)
            if aggregate_data:
                p["lang"] = fb_lang
                break

    if p["mode"] == "v":
        volumes = parse_range(p["start"], p["end"])

        # --- VALIDACIÓN PREVIA ---
        if aggregate_data:
            invalid_vols = [v for v in volumes if v not in aggregate_data]
            if invalid_vols:
                if not p["silent"]:
                    print(
                        f"\n[!] ADVERTENCIA: Los siguientes volúmenes no aparecen en MangaDex ({p['lang']}): {invalid_vols}"
                    )
                    available = sorted(
                        list(aggregate_data.keys()),
                        key=lambda x: (
                            float(x) if x.replace(".", "", 1).isdigit() else 999
                        ),
                    )
                    print(f"    Opciones disponibles: {available}")
                    is_interactive = len(sys.argv) <= 1
                    if is_interactive:
                        confirm = (
                            input(
                                "> ¿Deseas intentar la descarga de todos modos? [s/N]: "
                            )
                            .strip()
                            .lower()
                        )
                        if confirm != "s":
                            print("[*] Operación cancelada por el usuario.")
                            return

        if not p["silent"]:
            print(
                f"\n[*] Detectado modo VOLUMEN. Procesando {len(volumes)} tomo(s) individualmente..."
            )
        for vol in volumes:
            process_volume_flow(p, vol, base_path, aggregate_data)
    else:
        process_chapter_flow(p, base_path, aggregate_data)

    if not p["silent"]:
        print(f"\n=========================================")
        print(f" Proceso Finalizado. Archivos generados en:\n {OUTPUT_FOLDER_KCC}")
        print(f"=========================================\n")
