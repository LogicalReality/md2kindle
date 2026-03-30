import os
import subprocess
import glob

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
# -m: Manga mode (Der a Izq)
# -r 1: Rotate double spreads (Páginas dobles)
# -u: Upscale manteniendo Aspect Ratio

# Ajustes generales
DELETE_CBZ_AFTER_CONVERSION = False # ¡Cambiar a True si deseas borrar los .cbz originales!
DEFAULT_LANGUAGE = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE = True # Omitir capítulos marcados como "oneshot" (pilotos/especiales) en Tomos.
# ==========================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_user_input():
    clear_screen()
    print("=========================================")
    print(" MangaDex -> Kindle Converter (md2kindle)")
    print("=========================================")
    
    url = input("\n> URL de MangaDex: ").strip()
    
    title_folder = input("> Nombre de la carpeta del manga (ej. Berserk): ").strip()
    
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
        
    return url, title_folder, lang, mode, start_val, end_val

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
        
    cmd = [
        MANGADEX_DL_PATH,
        url,
        "--save-as", save_as,
        "--language", lang,
        *range_args,
        "--path", target_path
    ]
    
    # Solo aplicamos el filtro de oneshots si está activo en la configuración
    if mode == 'v' and SKIP_ONESHOTS_ON_VOLUME_MODE:
        cmd.insert(5, "--no-oneshot-chapter")
    
    print(f"\n[*] Ejecutando descarga en: {target_path}")
    print(f"[*] Comando MANGADEX-DL: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"\n[!] Excepción al ejecutar mangadex-dl: {e}")
        return False

def convert_with_kcc(target_path):
    search_pattern = os.path.join(target_path, "**", "*.cbz")
    cbz_files = glob.glob(search_pattern, recursive=True)
    
    if not cbz_files:
        cbz_files = glob.glob(os.path.join(target_path, "*.cbz"))
        if not cbz_files:
            return
    
    for cbz_file in cbz_files:
        print(f"\n[+] Procesando con KCC: {os.path.basename(cbz_file)}")
        cmd = [
            KCC_C2E_PATH,
            "-p", KCC_PROFILE,
            "-f", KCC_FORMAT,
            "-o", OUTPUT_FOLDER_KCC
        ] + KCC_CUSTOM_ARGS + [cbz_file]
        
        try:
            result = subprocess.run(cmd)
            if result.returncode == 0 and DELETE_CBZ_AFTER_CONVERSION:
                os.remove(cbz_file)
        except Exception as e:
            print(f"\n[!] Excepción al ejecutar KCC: {e}")

def main():
    if not os.path.exists(MANGADEX_DL_PATH) or not os.path.exists(KCC_C2E_PATH):
        print("[ERROR] No se encontraron los ejecutables.")
        return
        
    url, title, lang, mode, start, end = get_user_input()
    base_path = os.path.join(OUTPUT_FOLDER_MANGA, title)

    if mode == 'v':
        volumes = parse_range(start, end)
        print(f"\n[*] Detectado modo VOLUMEN. Procesando {len(volumes)} tomo(s) individualmente...")
        for vol in volumes:
            folder = os.path.join(base_path, f"Vol {vol}")
            os.makedirs(folder, exist_ok=True)
            if download_manga(url, folder, lang, 'v', vol, vol):
                # --- Limpieza de capítulos huérfanos (Orphans) ---
                # Borramos cualquier CBZ que no sea "Vol. {vol}" para evitar capítulos sueltos adelantados
                all_cbz = glob.glob(os.path.join(folder, "*.cbz"))
                for cbz_file in all_cbz:
                    filename = os.path.basename(cbz_file).lower()
                    # Si el archivo no contiene "vol" seguido del número, es un huérfano (ej: Berserk Ch 383)
                    # O si explícitamente dice "no volume"
                    expected_pattern = f"vol {vol}"
                    if expected_pattern.lower() not in filename or "no volume" in filename:
                        print(f"[-] Eliminando capítulo huérfano/extra: {os.path.basename(cbz_file)}")
                        os.remove(cbz_file)
                
                convert_with_kcc(folder)
    else:
        # Modo Capítulo: Agrupado
        suffix = f"Cap {start}" + (f"-{end}" if start != end else "")
        folder = os.path.join(base_path, suffix)
        os.makedirs(folder, exist_ok=True)
        print(f"\n[*] Detectado modo CAPÍTULO. Agrupando rango {start}-{end}...")
        if download_manga(url, folder, lang, 'c', start, end):
            convert_with_kcc(folder)

    print(f"\n=========================================")
    print(f" Proceso Finalizado. Archivos generados en:\n {OUTPUT_FOLDER_KCC}")
    print(f"=========================================\n")

if __name__ == "__main__":
    main()
