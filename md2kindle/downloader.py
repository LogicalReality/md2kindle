"""Descarga de manga y auditoría de integridad."""

import os
import subprocess
import glob
import re

from md2kindle.config import MANGADEX_DL_PATH


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
