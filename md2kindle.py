import os
import subprocess
import glob
import re
import json
import urllib.request
import urllib.parse

# ==========================================
# CONFIGURACIÓN
# ==========================================
# Rutas a los ejecutables
MANGADEX_DL_PATH = r"C:\mangadex-dl\mangadex-dl.exe"
KCC_C2E_PATH = r"C:\Antigravity\md2kindle\kcc_c2e_9.6.2.exe"

# Carpetas de destino
OUTPUT_FOLDER_MANGA = r"C:\Manga"
OUTPUT_FOLDER_KCC = r"C:\KCC Output"

# Ajustes de KCC (Kindle Comic Converter)
KCC_PROFILE = "KO"  # KO = Kindle Oasis 2/3 / Paperwhite 12
KCC_FORMAT = "MOBI" # Formato Dual MOBI/AZW3
KCC_CUSTOM_ARGS = ["-m", "-r", "1", "-u"] 
# Para ver la lista completa de argumentos validos, consulta el README.md

# Ajustes generales
DELETE_CBZ_AFTER_CONVERSION = False 
DEFAULT_LANGUAGE = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE = True 
# Consulta el README.md para mas detalles sobre estos ajustes.
# ==========================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def sanitize_filename(filename):
    """Elimina caracteres no permitidos en nombres de archivos de Windows"""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

def get_api_data(url):
    """Llamada genérica a la API con User-Agent para evitar bloqueos"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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
            chap_data = get_api_data(f"https://api.mangadex.org/chapter/{uuid}?includes[]=manga")
            if chap_data and "data" in chap_data:
                attributes = chap_data["data"]["attributes"]
                suggestions["mode"] = "c"
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
            return [], "MangaDex", suggestions
            
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
            "es": "Spanish"
        }
        
        # Título principal y alternativos
        main_title = data.get("title", {})
        for lang, value in main_title.items():
            if lang in lang_map:
                options.append({"label": lang_map[lang], "title": sanitize_filename(value)})
        
        alt_titles = data.get("altTitles", [])
        for alt in alt_titles:
            for lang, value in alt.items():
                if lang in lang_map:
                    options.append({"label": lang_map[lang], "title": sanitize_filename(value)})
        
        # Unificar y Ordenar
        seen = set()
        unique_options = []
        for opt in options:
            if opt["title"].lower() not in seen:
                seen.add(opt["title"].lower())
                unique_options.append(opt)
        
        priority = ["ja-ro", "en", "es-la", "es"]
        unique_options.sort(key=lambda x: priority.index(next(k for k, v in lang_map.items() if v == x["label"])) if any(v == x["label"] for v in lang_map.values()) else 99)

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

def get_user_input():
    clear_screen()
    print("=========================================")
    print(" MangaDex -> Kindle Converter (md2kindle)")
    print("=========================================")
    
    url_input = input("\n> URL de MangaDex: ").strip()
    
    # Detección de títulos y sugerencias desde MangaDex
    options, author_name, suggestions, manga_uuid = get_manga_title_options(url_input)
    title_folder = ""

    # Redirección Canónica: Si tenemos el UUID, usamos la URL de /title/ para la descarga
    # Esto garantiza que mangadex-dl pueda ver toda la obra y no solo un capítulo.
    url = f"https://mangadex.org/title/{manga_uuid}" if manga_uuid else url_input
    
    if options:
        print(f"\nAutor(es) detectado(s): {author_name}")
        print("Selecciona el nombre para la carpeta del manga:")
        for i, opt in enumerate(options, 1):
            label_display = f"[{opt['label']}]"
            print(f"  {i}. {label_display:<18} {opt['title']}")
        print(f"  {len(options) + 1}. [Manual]           Escribir nombre personalizado...")
        
        choice = input(f"\nSelecciona una opción [1]: ").strip()
        
        if not choice:
            title_folder = options[0]["title"]
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(options):
                title_folder = options[idx-1]["title"]
            else:
                title_folder = input("> Nombre de la carpeta: ").strip()
                while not title_folder and not manga_uuid:
                    title_folder = input("> El nombre no puede estar vacío. Inténtalo de nuevo: ").strip()
        else:
            title_folder = choice
    else:
        title_folder = input("\n> Nombre de la carpeta del manga (ej. Berserk): ").strip()
        while not title_folder and not manga_uuid:
            title_folder = input("> El nombre no puede estar vacío. Inténtalo de nuevo: ").strip()

    # --- FALLBACK DE TÍTULO (Resiliencia ante nombres prohibidos en Windows) ---
    if not title_folder:
        if manga_uuid:
            title_folder = manga_uuid
            print(f"\n[!] Título inválido o vacío tras sanitización. Usando UUID como fallback.")
            print(f"[*] Carpeta destino: {title_folder}")
        else:
            title_folder = "Manga_Sin_Nombre"
            print(f"\n[!] No se pudo obtener título ni UUID. Usando genérico: {title_folder}")
    
    # Lógica de Idioma Inteligente
    detected_lang = suggestions.get("lang")
    lang_to_use = DEFAULT_LANGUAGE
    
    if detected_lang and detected_lang != DEFAULT_LANGUAGE:
        print(f"\n[!] Aviso: Esta URL apunta a un capítulo en '{detected_lang}'.")
        print(f"    Tu configuración predeterminada es '{DEFAULT_LANGUAGE}'.")
        choice_lang = input(f"> ¿Deseas cambiar a '{detected_lang}' para esta descarga? [s/N]: ").strip().lower()
        if choice_lang == 's':
            lang_to_use = detected_lang
            print(f"[*] Idioma temporal cambiado a: {lang_to_use}")

    lang = input(f"> Idioma [Presiona Enter para '{lang_to_use}']: ").strip()
    if not lang:
        lang = lang_to_use

    # Uso de sugerencias para modo y valores
    sug_mode = suggestions["mode"] or "v"
    mode_prompt = f"> ¿Volumen o Capítulo? [(v)ol / (c)ap] [{sug_mode}]: "
    mode = input(mode_prompt).strip().lower()
    if not mode:
        mode = sug_mode
    
    while mode not in ['v', 'c', 'vol', 'cap']:
        mode = input("> Opción no válida. Usa 'v' o 'c': ").strip().lower()
    mode = 'v' if mode in ['v', 'vol'] else 'c'

    sug_start = suggestions["start"] if mode == 'c' else suggestions["vol"]
    start_prompt = f"> Número inicial" + (f" [{sug_start}]" if sug_start else "") + ": "
    start_val = input(start_prompt).strip()
    if not start_val and sug_start:
        start_val = sug_start
        
    end_val = input(f"> Número final [Enter para '{start_val}']: ").strip()
    if not end_val:
        end_val = start_val
        
    skip_oneshots = input("> ¿Excluir capítulos 'Oneshot' / Promocionales? [S/n]: ").strip().lower() != 'n'
        
    return url, title_folder, lang, mode, start_val, end_val, author_name, manga_uuid, skip_oneshots

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

def audit_and_cleanup(target_path, aggregate_data, mode, start_val, end_val, skip_oneshots):
    """
    Realiza una auditoría inteligente y limpia huérfanos bajados por error.
    Usa la estructura real informada por la API de MangaDex.
    """
    if not aggregate_data:
        return # Si no hay datos de la API, fall in safe mode (no borrar nada)
        
    expected_chapters = set()
    
    if mode == 'v':
        volumes_to_check = parse_range(start_val, end_val)
        for expected_vol in volumes_to_check:
            # Buscar la key exacta del volumen ("1", "S1", "none")
            vol_data = aggregate_data.get(expected_vol)
            if not vol_data:
                # Intento fallback para tratar "1.0" como "1" o viceversa
                fallback_key = str(int(float(expected_vol))) if expected_vol.replace('.','',1).isdigit() and expected_vol.endswith('.0') else expected_vol
                vol_data = aggregate_data.get(fallback_key)
            
            if vol_data and "chapters" in vol_data:
                for ch_dict in vol_data["chapters"].values():
                    # Solo añadir si no hemos decidido ignorar unoshoots
                    is_oneshot = ch_dict.get("chapter") == "none" or ch_dict.get("chapter") is None
                    if is_oneshot and skip_oneshots:
                        continue
                    # La key del diccionario es casi siempre el numero del capitulo
                    if ch_dict.get("chapter") != "none":
                        expected_chapters.add(str(ch_dict.get("chapter")))

    else: # Modo Capítulo
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
            if local_chap.replace('.','',1).isdigit():
                if "." in local_chap:
                    local_chap_clean = str(float(local_chap)).rstrip('0').rstrip('.')
                    if local_chap_clean == "": local_chap_clean = "0"
                else:
                    local_chap_clean = str(int(local_chap))
            else:
                local_chap_clean = local_chap # "none" u otros strings

            found_chapters.add(local_chap_clean)
            
            # Limpieza (Orphans) segun Whitelist de la API
            # Solo limpiamos si logramos extraer una lista de expecteds valida
            if expected_chapters and local_chap_clean not in expected_chapters:
                # Advertencia: Si es un Oneshot ("none") y el usuario no pidio borrarlos, no truncar
                if local_chap_clean == "none" and not skip_oneshots:
                    pass
                else:
                    print(f"[-] Eliminando capítulo extra no relacionado al objetivo: {filename}")
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
            print(f"[!] ADVERTENCIA: La API esperaba los siguientes capítulos para el/los volumen(es) solicitado(s), pero no se encontraron (posible censura o falta de traducción):")
            # Ordenar si es numerico
            sorted_missing = sorted(list(missing), key=lambda x: float(x) if x.replace('.','',1).isdigit() else 999)
            print(f"    Faltantes: {sorted_missing}")
        else:
            print(f"[OK] Todos los capítulos esperados según la API están presentes.")

def download_manga(url, target_path, lang, mode, start_val, end_val, skip_oneshots):
    if mode == 'v':
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
        "--save-as", save_as,
        "--language", lang
    ]
    
    # Aplicamos el filtro de oneshots de forma dinamica segun el prompt del usuario
    if skip_oneshots:
        cmd.append("--no-oneshot-chapter")
    
    # Añadimos el resto de parámetros al final
    cmd.extend(range_args)
    cmd.extend(["--path", target_path])
    
    print(f"\n[*] Ejecutando descarga en: {target_path}")
    print(f"[*] Comando MANGADEX-DL: {subprocess.list2cmdline(cmd)}\n")
    
    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"\n[!] Excepción al ejecutar mangadex-dl: {e}")
        return False

def convert_with_kcc(target_path, author="MangaDex"):
    """Convierte archivos CBZ en Kindle-friendly formats reflejando la estructura original"""
    search_pattern = os.path.join(target_path, "**", "*.cbz")
    cbz_files = glob.glob(search_pattern, recursive=True)
    
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

    for cbz_file in cbz_files:
        print(f"\n[+] Procesando con KCC: {os.path.basename(cbz_file)}")
        cmd = [
            KCC_C2E_PATH,
            "-p", KCC_PROFILE,
            "-f", KCC_FORMAT,
            "-o", final_output,
            "-a", author  # Inyección del autor real
        ] + KCC_CUSTOM_ARGS + [cbz_file]
        
        try:
            print(f"[*] Guardando en: {final_output}")
            result = subprocess.run(cmd)
            if result.returncode == 0 and DELETE_CBZ_AFTER_CONVERSION:
                os.remove(cbz_file)
        except Exception as e:
            print(f"\n[!] Excepción al ejecutar KCC: {e}")

def main():
    if not os.path.exists(MANGADEX_DL_PATH) or not os.path.exists(KCC_C2E_PATH):
        print("[ERROR] No se encontraron los ejecutables.")
        return
        
    url, title, lang, mode, start, end, author, manga_uuid, skip_oneshots = get_user_input()
    base_path = os.path.join(OUTPUT_FOLDER_MANGA, title)
    
    # FASE 2: Obtener data de auditoria preventivamente
    aggregate_data = {}
    if manga_uuid:
        print(f"\n[*] Consultando estructura de MangaDex para auditoría...")
        aggregate_data = get_manga_aggregate(manga_uuid, lang)

    if mode == 'v':
        volumes = parse_range(start, end)
        
        # --- VALIDACIÓN PREVIA ---
        if aggregate_data:
            invalid_vols = [v for v in volumes if v not in aggregate_data]
            if invalid_vols:
                print(f"\n[!] ADVERTENCIA: Los siguientes volúmenes no aparecen en MangaDex: {invalid_vols}")
                available = sorted(list(aggregate_data.keys()), key=lambda x: float(x) if x.replace('.','',1).isdigit() else 999)
                print(f"    Opciones disponibles: {available}")
                confirm = input("> ¿Deseas intentar la descarga de todos modos? [s/N]: ").strip().lower()
                if confirm != 's':
                    print("[*] Operación cancelada por el usuario.")
                    return

        print(f"\n[*] Detectado modo VOLUMEN. Procesando {len(volumes)} tomo(s) individualmente...")
        for vol in volumes:
            folder = os.path.join(base_path, f"Vol {vol}")
            os.makedirs(folder, exist_ok=True)
            if download_manga(url, folder, lang, 'v', vol, vol, skip_oneshots):
                # Limpieza y auditoría inteligente (reemplaza el regex viejo)
                audit_and_cleanup(folder, aggregate_data, 'v', vol, vol, skip_oneshots)
                convert_with_kcc(folder, author)
    else:
        # Modo Capítulo: Agrupado
        suffix = f"Cap {start}" + (f"-{end}" if start != end else "")
        folder = os.path.join(base_path, suffix)
        
        # --- VALIDACIÓN PREVIA (CAPÍTULOS) ---
        # (Opcional, pero para capítulos es más complejo por los rangos)
        
        os.makedirs(folder, exist_ok=True)
        print(f"\n[*] Detectado modo CAPÍTULO. Agrupando rango {start}-{end}...")
        if download_manga(url, folder, lang, 'c', start, end, skip_oneshots):
            audit_and_cleanup(folder, aggregate_data, 'c', start, end, skip_oneshots)
            convert_with_kcc(folder, author)

    print(f"\n=========================================")
    print(f" Proceso Finalizado. Archivos generados en:\n {OUTPUT_FOLDER_KCC}")
    print(f"=========================================\n")

if __name__ == "__main__":
    main()
