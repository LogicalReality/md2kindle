"""Entrega de archivos via Telegram y ffsend (E2EE)."""

import os
import re
import shutil
import subprocess
import requests

from md2kindle.config import OUTPUT_FOLDER_KCC


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
