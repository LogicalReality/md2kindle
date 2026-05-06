"""Entrega de archivos via Telegram Bot API."""

import logging
import os
import requests

from md2kindle.models import format_manga_title
from md2kindle.config import OUTPUT_FOLDER_KCC
from md2kindle.delivery.ffsend import upload_to_ffsend

logger = logging.getLogger(__name__)


def send_message(text: str, parse_mode: str = None) -> bool:
    """Envía un mensaje de texto simple a Telegram."""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error("No se encontraron las variables de entorno TELEGRAM_TOKEN o TELEGRAM_CHAT_ID.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logger.info("Mensaje enviado con éxito a Telegram.")
            return True
        else:
            logger.error(f"Error al enviar mensaje (Status {response.status_code}): {response.text}")
            return False
    except Exception as e:
        logger.error(f"Excepción al contactar con Telegram: {e}")
        return False


def send_to_telegram(file_path):
    """Envía el archivo generado a un chat de Telegram usando el Bot API o ffsend si es pesado"""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error(
            "No se encontraron las variables de entorno TELEGRAM_TOKEN o TELEGRAM_CHAT_ID."
        )
        return False

    file_size = os.path.getsize(file_path)
    # Umbral de 45 MB para evitar el límite de 50MB de Telegram
    MAX_DIRECT_SIZE = 45 * 1024 * 1024

    if file_size >= MAX_DIRECT_SIZE:
        logger.warning(
            "Archivo detectado como pesado (%.2f MB).",
            file_size / (1024 * 1024),
        )
        # Método único de alta privacidad: ffsend (E2EE)
        link = upload_to_ffsend(file_path)

        if link:
            manga, vol = format_manga_title(file_path, OUTPUT_FOLDER_KCC)
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
            msg = f"📖 **{manga}** - {vol}\n\n🔒 Enlace seguro (archivo de {size_str}). Expira en 12h:\n\n🔗 [DESCARGAR AHORA]({link})"
            url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(
                url_msg,
                data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            )
            logger.info("Enlace de descarga cifrado enviado a Telegram.")
            return True
        else:
            logger.error("No se pudo generar el enlace cifrado.")
            return False

    logger.info(
        "Enviando directamente a Telegram: %s (%.2f MB)...",
        os.path.basename(file_path),
        file_size / (1024 * 1024),
    )
    url = f"https://api.telegram.org/bot{token}/sendDocument"

    try:
        manga, vol = format_manga_title(file_path, OUTPUT_FOLDER_KCC)
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {
                "chat_id": chat_id,
                "caption": f"📖 **{manga}** - {vol}",
            }
            response = requests.post(url, data=data, files=files)

        if response.status_code == 200:
            logger.info("Enviado con éxito a Telegram.")
            return True
        elif response.status_code == 413:
            logger.warning(
                "Telegram rechazó el archivo por tamaño (413). Reintentando con Bóveda Cifrada..."
            )
            link = upload_to_ffsend(file_path)
            if link:
                manga, vol = format_manga_title(file_path, OUTPUT_FOLDER_KCC)
                msg = f"📖 **{manga}** - {vol}\n\n🔒 Enlace seguro:\n{link}"
                url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url_msg, data={"chat_id": chat_id, "text": msg})
                return True
            else:
                return False
        else:
            logger.error("Error al enviar (Status %d).", response.status_code)
            return False
    except Exception as e:
        logger.error("Excepción al contactar con Telegram: %s", e)
        return False
