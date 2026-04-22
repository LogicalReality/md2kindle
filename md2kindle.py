import os
import subprocess
import glob
import re
import json
import urllib.request
import urllib.parse
import argparse
import sys
import shutil
import requests

IS_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

# ==========================================
# CONFIGURACIÓN
# ==========================================
# Configuración Estática (Windows Local)
MANGADEX_DL_PATH_WIN = r"C:\mangadex-dl\mangadex-dl.exe"
KCC_C2E_PATH_WIN = r"C:\Antigravity\md2kindle\kcc_c2e_9.6.2.exe"

# Búsqueda Dinámica (Nube / Linux)
MANGADEX_DL_PATH = (
    MANGADEX_DL_PATH_WIN
    if os.path.exists(MANGADEX_DL_PATH_WIN)
    else (shutil.which("mangadex-dl") or "mangadex-dl")
)
KCC_C2E_PATH = (
    KCC_C2E_PATH_WIN
    if os.path.exists(KCC_C2E_PATH_WIN)
    else (shutil.which("kcc-c2e") or "kcc-c2e")
)

# Carpetas de destino (Con fallback relativo para la nube)
OUTPUT_FOLDER_MANGA = (
    r"C:\Manga"
    if os.path.exists(r"C:\Manga")
    else os.path.join(os.getcwd(), "downloads")
)
OUTPUT_FOLDER_KCC = (
    r"C:\KCC Output"
    if os.path.exists(r"C:\KCC Output")
    else os.path.join(os.getcwd(), "output")
)

# Ajustes de KCC (Kindle Comic Converter)
KCC_PROFILE = "KO"  # KO = Kindle Oasis 2/3 / Paperwhite 12
KCC_FORMAT = "MOBI"  # Formato Dual MOBI/AZW3
KCC_CUSTOM_ARGS = ["-m", "-r", "1", "-u"]
# Para ver la lista completa de argumentos validos, consulta el README.md

# Ajustes generales
DELETE_CBZ_AFTER_CONVERSION = False
DEFAULT_LANGUAGE = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE = True
# Consulta el README.md para mas detalles sobre estos ajustes.
# ==========================================


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def sanitize_filename(filename):
    """Elimina caracteres no permitidos en nombres de archivos de Windows"""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()


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
            print(f"[*] Detectada URL de capítulo. Buscando manga asociado...")
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
        print(f"[!] Error inesperado al procesar URL: {e}")
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
        print(f"[!] Aviso: No se pudo obtener la estructura de auditoría: {e}")
        return {}


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


def format_manga_title(file_path):
    rel_path = os.path.relpath(file_path, OUTPUT_FOLDER_KCC)
    parts = rel_path.split(os.sep)
    manga = parts[0]
    filename = parts[-1].replace(".mobi", "")
    vol_match = re.search(r"(Vol\.?\s*\d+)", filename, re.IGNORECASE)
    vol = vol_match.group(1) if vol_match else filename
    return manga, vol


def upload_to_ffsend(file_path):
    """Sube un archivo a ffsend (Firefox Send) - Encriptación de Extremo a Extremo"""
    # Verificamos si ffsend está instalado en el sistema
    ffsend_bin = shutil.which("ffsend")
    if not ffsend_bin:
        print(
            "[!] ffsend no encontrado en el PATH. Es obligatorio para archivos > 45MB."
        )
        return None

    url_host = "https://send.vis.ee"  # Instancia comunitaria estable
    print(f"[*] Subiendo a {url_host} (Bóveda Cifrada E2EE)...")

    try:
        # Comando: ffsend upload <file> --downloads 5 --expiry 12h --host <host> --quiet --no-interact
        cmd = [
            ffsend_bin,
            "upload",
            file_path,
            "--downloads",
            "5",
            "--expiry",
            "12h",
            "--host",
            url_host,
            "--quiet",
            "--no-interact",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            link = result.stdout.strip()
            return link
        else:
            print(f"[!] Error en ffsend (Code {result.returncode}): {result.stderr}")
            return None
    except Exception as e:
        print(f"[!] Excepción al ejecutar ffsend: {e}")
        return None


def send_to_telegram(file_path):
    """Envía el archivo generado a un chat de Telegram usando el Bot API o ffsend si es pesado"""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print(
            "[!] Error: No se encontraron las variables de entorno TELEGRAM_TOKEN o TELEGRAM_CHAT_ID."
        )
        return False

    file_size = os.path.getsize(file_path)
    # Umbral de 45 MB para evitar el límite de 50MB de Telegram
    MAX_DIRECT_SIZE = 45 * 1024 * 1024

    if file_size >= MAX_DIRECT_SIZE:
        print(
            f"[!] Archivo detectado como pesado ({file_size / (1024 * 1024):.2f} MB)."
        )
        # Método único de alta privacidad: ffsend (E2EE)
        link = upload_to_ffsend(file_path)

        if link:
            manga, vol = format_manga_title(file_path)
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
            msg = f"📖 **{manga}** - {vol}\n\n🔒 Enlace seguro (archivo de {size_str}). Expira en 12h:\n\n🔗 [DESCARGAR AHORA]({link})"
            url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(
                url_msg,
                data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            )
            print("[OK] Enlace de descarga cifrado enviado a Telegram.")
            return True
        else:
            print("[!] Error: No se pudo generar el enlace cifrado.")
            return False

    print(
        f"[*] Enviando directamente a Telegram: {os.path.basename(file_path)} ({file_size / (1024 * 1024):.2f} MB)..."
    )
    url = f"https://api.telegram.org/bot{token}/sendDocument"

    try:
        manga, vol = format_manga_title(file_path)
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {
                "chat_id": chat_id,
                "caption": f"📖 **{manga}** - {vol}",
            }
            response = requests.post(url, data=data, files=files)

        if response.status_code == 200:
            print("[OK] Enviado con éxito a Telegram.")
            return True
        elif response.status_code == 413:
            print(
                "[!] Telegram rechazó el archivo por tamaño (413). Reintentando con Bóveda Cifrada..."
            )
            link = upload_to_ffsend(file_path)
            if link:
                manga, vol = format_manga_title(file_path)
                msg = f"📖 **{manga}** - {vol}\n\n🔒 Enlace seguro:\n{link}"
                url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url_msg, data={"chat_id": chat_id, "text": msg})
                return True
            else:
                return False
        else:
            print(f"[!] Error al enviar (Status {response.status_code}).")
            return False
    except Exception as e:
        print(f"[!] Excepción al contactar con Telegram: {e}")
        return False


def parse_range(start, end):
    """Convierte un rango de strings en una lista. Soporta decimales (25.5) y alfanuméricos (S1)"""
    try:
        s = float(start)
        e = float(end)
        if s == e:
            return [start]

        # Generamos lista de enteros si son exactos, de lo contrario solo retornamos los extremos
        if s.is_integer() and e.is_integer():
            return [str(i) for i in range(int(s), int(e) + 1)]
        else:
            return [start, end]
    except ValueError:
        # Si no es un número (ej. "S1", "Extra"), devolvemos como literal.
        if start == end:
            return [start]
        return [start]


def audit_and_cleanup(
    target_path, aggregate_data, mode, start_val, end_val, skip_oneshots
):
    """
    Realiza una auditoría inteligente y limpia huérfanos bajados por error.
    Usa la estructura real informada por la API de MangaDex.
    """
    if not aggregate_data:
        return  # Si no hay datos de la API, fall in safe mode (no borrar nada)

    expected_chapters = set()

    if mode == "v":
        volumes_to_check = parse_range(start_val, end_val)
        for expected_vol in volumes_to_check:
            # Buscar la key exacta del volumen ("1", "S1", "none")
            vol_data = aggregate_data.get(expected_vol)
            if not vol_data:
                # Intento fallback para tratar "1.0" como "1" o viceversa
                fallback_key = (
                    str(int(float(expected_vol)))
                    if expected_vol.replace(".", "", 1).isdigit()
                    and expected_vol.endswith(".0")
                    else expected_vol
                )
                vol_data = aggregate_data.get(fallback_key)

            if vol_data and "chapters" in vol_data:
                for ch_dict in vol_data["chapters"].values():
                    # Solo añadir si no hemos decidido ignorar unoshoots
                    is_oneshot = (
                        ch_dict.get("chapter") == "none"
                        or ch_dict.get("chapter") is None
                    )
                    if is_oneshot and skip_oneshots:
                        continue
                    # La key del diccionario es casi siempre el numero del capitulo
                    if ch_dict.get("chapter") != "none":
                        expected_chapters.add(str(ch_dict.get("chapter")))

    else:  # Modo Capítulo
        chapters_to_check = parse_range(start_val, end_val)
        for expected_ch in chapters_to_check:
            expected_chapters.add(str(expected_ch))

    # Leer archivos locales
    all_cbz = glob.glob(os.path.join(target_path, "*.cbz"))
    found_chapters = set()

    print("\n--- Auditoría de Integridad ---")

    for cbz_file in all_cbz:
        filename = os.path.basename(cbz_file)

        # mangadex-dl suele poner "- Ch. XX" o "Chapter XX" al final
        # Funciona con variaciones "Ch. 5", "Ch. 5.5", "Ch. none"
        match = re.search(r"Ch\.\s*([\d\.]+|none)\b", filename, re.IGNORECASE)
        if not match:
            match = re.search(r"Chapter\s*([\d\.]+|none)\b", filename, re.IGNORECASE)

        if match:
            local_chap = match.group(1)
            # Manejar ceros a la izquierda que mangadex-dl pudiera haber puesto
            if local_chap.replace(".", "", 1).isdigit():
                if "." in local_chap:
                    local_chap_clean = str(float(local_chap)).rstrip("0").rstrip(".")
                    if local_chap_clean == "":
                        local_chap_clean = "0"
                else:
                    local_chap_clean = str(int(local_chap))
            else:
                local_chap_clean = local_chap  # "none" u otros strings

            found_chapters.add(local_chap_clean)

            # Limpieza (Orphans) segun Whitelist de la API
            # Solo limpiamos si logramos extraer una lista de expecteds valida
            if expected_chapters and local_chap_clean not in expected_chapters:
                # Advertencia: Si es un Oneshot ("none") y el usuario no pidio borrarlos, no truncar
                if local_chap_clean == "none" and not skip_oneshots:
                    pass
                else:
                    print(
                        f"[-] Eliminando capítulo extra no relacionado al objetivo: {filename}"
                    )
                    try:
                        os.remove(cbz_file)
                    except Exception as e:
                        print(f"[!] Error al borrar {filename}: {e}")
        else:
            # Si mangadex-dl lo descargo como volumen completo sin separar por capítulos
            pass

    # Auditoria de Faltantes (Aviso no bloqueante)
    if expected_chapters:
        missing = expected_chapters - found_chapters
        if missing:
            print(
                f"[!] ADVERTENCIA: La API esperaba los siguientes capítulos para el/los volumen(es) solicitado(s), pero no se encontraron (posible censura o falta de traducción):"
            )
            # Ordenar si es numerico
            sorted_missing = sorted(
                list(missing),
                key=lambda x: float(x) if x.replace(".", "", 1).isdigit() else 999,
            )
            print(f"    Faltantes: {sorted_missing}")
        else:
            print(f"[OK] Todos los capítulos esperados según la API están presentes.")


def download_manga(url, target_path, lang, mode, start_val, end_val, skip_oneshots):
    if mode == "v":
        save_as = "cbz-volume"
        range_args = ["--start-volume", start_val, "--end-volume", end_val]
    else:
        # Descarga capítulos en un solo archivo CBZ
        save_as = "cbz-single"
        range_args = ["--start-chapter", start_val, "--end-chapter", end_val]

    # Construcción dinámica del comando para evitar errores de posición (como el de --language)
    cmd = [
        MANGADEX_DL_PATH,
        url,
        "--save-as",
        save_as,
        "--language",
        lang,
    ]

    # Aplicamos el filtro de oneshots de forma dinamica segun el prompt del usuario
    if skip_oneshots:
        cmd.append("--no-oneshot-chapter")

    # Añadimos el resto de parámetros al final
    cmd.extend(range_args)
    cmd.extend(["--path", target_path])

    print(f"\n[*] Ejecutando descarga en: {target_path}")
    print(f"[+] Descargando manga...")

    try:
        result = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print(f"[OK] Descarga completada")
            return True
        else:
            print(f"[ERROR] Falló la descarga")
            return False
    except Exception as e:
        print(f"\n[!] Excepción al ejecutar mangadex-dl: {e}")
        return False


def convert_with_kcc(target_path, author="MangaDex", title=None):
    """Convierte archivos CBZ en Kindle-friendly formats reflejando la estructura original"""
    search_pattern = os.path.join(target_path, "**", "*.cbz")
    cbz_files = glob.glob(search_pattern, recursive=True)

    generated_files = []  # Seguimiento de archivos para envío

    if not cbz_files:
        cbz_files = glob.glob(os.path.join(target_path, "*.cbz"))
        if not cbz_files:
            return

    # Calcular ruta de salida replicando la estructura de carpetas
    try:
        rel_path = os.path.relpath(target_path, OUTPUT_FOLDER_MANGA)
        final_output = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
        os.makedirs(final_output, exist_ok=True)
    except Exception as e:
        print(f"[!] Error al crear carpeta de salida en KCC: {e}")
        final_output = OUTPUT_FOLDER_KCC
        rel_path = target_path

    # Extraer nombre de manga y volumen del path para metadatos
    manga_title = title
    if not manga_title:
        try:
            path_parts = rel_path.split(os.sep)
            manga_title = path_parts[0]
        except Exception:
            manga_title = "Manga"

    for cbz_file in cbz_files:
        print(f"\n[+] Procesando con KCC: {os.path.basename(cbz_file)}")

        # Extraer volumen del nombre del CBZ (ej: "Vol. 39.cbz" -> "Vol. 39")
        cbz_basename = os.path.splitext(os.path.basename(cbz_file))[0]
        vol_match = re.search(r"(Vol\.?\s*\d+)", cbz_basename, re.IGNORECASE)
        vol_str = vol_match.group(1) if vol_match else cbz_basename

        # Formatear titulo completo para metadatos del MOBI
        mobi_title = f"{manga_title} {vol_str}"

        cmd = (
            [
                KCC_C2E_PATH,
                "-p",
                KCC_PROFILE,
                "-f",
                KCC_FORMAT,
                "-o",
                final_output,
                "-a",
                author,  # Inyección del autor real
                "-t",
                mobi_title,  # Inyección del título completo
            ]
            + KCC_CUSTOM_ARGS
            + [cbz_file]
        )

        try:
            print(f"[*] Guardando en: {final_output}")
            result = subprocess.run(
                cmd, stderr=subprocess.DEVNULL if IS_CI else subprocess.PIPE
            )
            if result.returncode == 0:
                # Localizar el archivo generado (.mobi)
                filename_no_ext = os.path.splitext(os.path.basename(cbz_file))[0]
                mobi_file = os.path.join(final_output, filename_no_ext + ".mobi")
                if os.path.exists(mobi_file):
                    # Renombrar archivo con título completo
                    manga, vol = format_manga_title(mobi_file)
                    new_name = f"{manga} {vol}.mobi"
                    new_path = os.path.join(final_output, new_name)
                    if new_name != os.path.basename(mobi_file):
                        os.rename(mobi_file, new_path)
                        mobi_file = new_path
                    generated_files.append(mobi_file)

                if DELETE_CBZ_AFTER_CONVERSION:
                    os.remove(cbz_file)
        except Exception as e:
            print(f"\n[!] Excepción al ejecutar KCC: {e}")

    return generated_files


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
    # Si no hay capítulos en el idioma actual, probamos los otros en la lista
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
                    # En modo no interactivo, seguimos adelante si el usuario lo pidió por CLI (no hay confirmación)
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
            # --- SALTAR SI YA EXISTE ---
            rel_path = os.path.join(p["title"], f"Vol {vol}")
            expected_output_dir = os.path.join(OUTPUT_FOLDER_KCC, rel_path)
            # El nombre del CBZ suele ser "Vol. X.cbz" -> "Vol. X.mobi"
            mobi_name = f"Vol. {vol}.mobi"
            mobi_file = os.path.join(expected_output_dir, mobi_name)

            if os.path.exists(mobi_file):
                if not p["silent"]:
                    print(
                        f"[*] {mobi_name} ya existe. Saltando descarga y conversión..."
                    )
                if p["telegram"]:
                    send_to_telegram(mobi_file)
                continue

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
    else:
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

    if not p["silent"]:
        print(f"\n=========================================")
        print(f" Proceso Finalizado. Archivos generados en:\n {OUTPUT_FOLDER_KCC}")
        print(f"=========================================\n")


if __name__ == "__main__":
    main()
