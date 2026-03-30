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

def get_manga_title_options(url):
    """Consulta la API de MangaDex para obtener títulos y autor real"""
    try:
        # Extraer UUID de la URL (ej. https://mangadex.org/title/UUID/slug)
        match = re.search(r"title/([a-f0-9-]{36})", url)
        if not match:
            return [], "MangaDex"
        
        uuid = match.group(1)
        # Incluimos la relación del autor para obtener su nombre real
        api_url = f"https://api.mangadex.org/manga/{uuid}?includes[]=author"
        
        print(f"[*] Consultando datos en MangaDex API...")
        with urllib.request.urlopen(api_url) as response:
            res_data = json.loads(response.read().decode())["data"]
            data = res_data["attributes"]
            relationships = res_data.get("relationships", [])
        
        # Extraer nombre del autor
        # Fallback: Usamos "MangaDex" por defecto por si el manga no tiene autor registrado en la base de datos (evita crasheos)
        author_name = "MangaDex"
        for rel in relationships:
            if rel["type"] == "author" and "attributes" in rel:
                author_name = rel["attributes"]["name"] # Sobrescribe con el autor real
                break
            
        options = []
        # Títulos a buscar (Prioridades y Etiquetas)
        lang_map = {
            "ja-ro": "Romaji",
            "en": "English",
            "es-la": "Spanish (Latino)",
            "es": "Spanish"
        }
        
        # 1. Título principal
        main_title = data.get("title", {})
        for lang, value in main_title.items():
            if lang in lang_map:
                options.append({"label": lang_map[lang], "title": sanitize_filename(value)})
        
        # 2. Títulos alternativos
        alt_titles = data.get("altTitles", [])
        for alt in alt_titles:
            for lang, value in alt.items():
                if lang in lang_map:
                    options.append({"label": lang_map[lang], "title": sanitize_filename(value)})
        
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_options = []
        for opt in options:
            if opt["title"].lower() not in seen:
                seen.add(opt["title"].lower())
                unique_options.append(opt)
        
        # Ordenar por prioridad de idioma según el mapa
        priority = ["ja-ro", "en", "es-la", "es"]
        unique_options.sort(key=lambda x: priority.index(next(k for k, v in lang_map.items() if v == x["label"])) if any(v == x["label"] for v in lang_map.values()) else 99)

        return unique_options, author_name
    except Exception as e:
        print(f"[!] Error al consultar API de MangaDex: {e}")
        return [], "MangaDex"

def get_user_input():
    clear_screen()
    print("=========================================")
    print(" MangaDex -> Kindle Converter (md2kindle)")
    print("=========================================")
    
    url = input("\n> URL de MangaDex: ").strip()
    
    # Detección de títulos desde MangaDex
    options, author_name = get_manga_title_options(url)
    title_folder = ""
    
    if options:
        print(f"\nAutor detectado: {author_name}")
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
        else:
            # Si el usuario escribió un nombre directamente en lugar de un número
            title_folder = choice
    else:
        title_folder = input("\n> Nombre de la carpeta del manga (ej. Berserk): ").strip()
    
    lang = input(f"> Idioma [Presiona Enter para usar default '{DEFAULT_LANGUAGE}']: ").strip()
    if not lang:
        lang = DEFAULT_LANGUAGE

    mode = input("> ¿Descargar por Volumen o Capítulo? [(v)olumen / (c)apitulo]: ").strip().lower()
    while mode not in ['v', 'c']:
        print("Opción no válida. Usa 'v' para volumen o 'c' para capítulo.")
        mode = input("> ¿Descargar por Volumen o Capítulo? [(v)olumen / (c)apitulo]: ").strip().lower()
    
    start_val = input("> Número inicial (ej. 25 o 10): ").strip()
    end_val = input(f"> Número final [Presiona Enter si es solo el {start_val}]: ").strip()
    
    if not end_val:
        end_val = start_val
        
    return url, title_folder, lang, mode, start_val, end_val, author_name

def parse_range(start, end):
    """Convierte un rango de strings en una lista de floats (soporta 25.5 etc)"""
    try:
        s = float(start)
        e = float(end)
        if s == e:
            return [start]
        
        # Generamos lista de enteros si son exactos, de lo contrario solo retornamos el rango original
        if s.is_integer() and e.is_integer():
            return [str(i) for i in range(int(s), int(e) + 1)]
        else:
            return [start, end] # Fallback simple
    except:
        return [start]

def download_manga(url, target_path, lang, mode, start_val, end_val):
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
    
    # Solo aplicamos el filtro de oneshots si está activo en la configuración
    if mode == 'v' and SKIP_ONESHOTS_ON_VOLUME_MODE:
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
        
    url, title, lang, mode, start, end, author = get_user_input()
    base_path = os.path.join(OUTPUT_FOLDER_MANGA, title)

    if mode == 'v':
        volumes = parse_range(start, end)
        print(f"\n[*] Detectado modo VOLUMEN. Procesando {len(volumes)} tomo(s) individualmente...")
        for vol in volumes:
            folder = os.path.join(base_path, f"Vol {vol}")
            os.makedirs(folder, exist_ok=True)
            if download_manga(url, folder, lang, 'v', vol, vol):
                # --- Limpieza de capítulos huérfanos (Orphans) ---
                all_cbz = glob.glob(os.path.join(folder, "*.cbz"))
                vol_pattern = rf"vol\.?\s*0*{vol}\b"
                
                for cbz_file in all_cbz:
                    filename = os.path.basename(cbz_file).lower()
                    is_valid_volume = re.search(vol_pattern, filename, re.IGNORECASE)
                    
                    if not is_valid_volume or "no volume" in filename:
                        print(f"[-] Eliminando capítulo huérfano/extra: {os.path.basename(cbz_file)}")
                        os.remove(cbz_file)
                
                convert_with_kcc(folder, author)
    else:
        # Modo Capítulo: Agrupado
        suffix = f"Cap {start}" + (f"-{end}" if start != end else "")
        folder = os.path.join(base_path, suffix)
        os.makedirs(folder, exist_ok=True)
        print(f"\n[*] Detectado modo CAPÍTULO. Agrupando rango {start}-{end}...")
        if download_manga(url, folder, lang, 'c', start, end):
            convert_with_kcc(folder, author)

    print(f"\n=========================================")
    print(f" Proceso Finalizado. Archivos generados en:\n {OUTPUT_FOLDER_KCC}")
    print(f"=========================================\n")

if __name__ == "__main__":
    main()
