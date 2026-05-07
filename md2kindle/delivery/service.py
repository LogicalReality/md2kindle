"""Delivery orchestration for generated Kindle files."""

import html
import logging
import os
import sys
from collections.abc import Callable

from md2kindle.config import APP_CONFIG, AppConfig
from md2kindle.delivery.d1 import log_download
from md2kindle.delivery.r2 import send_to_r2
from md2kindle.delivery.telegram import send_message, send_to_telegram
from md2kindle.delivery.usb import send_to_usb
from md2kindle.models import PipelineParams, format_manga_title

logger = logging.getLogger(__name__)


def ask_fallback_choice(
    file_count: int, input_func: Callable[[str], str] = input
) -> str:
    """Ask how to deliver files when no Kindle was detected."""
    fallback = input_func(
        f"> ¿Deseas subir el lote ({file_count} archivos) a Cloudflare R2 y enviar el link por Telegram? "
        "[S/n/t] ('t' para archivo directo) [Enter para 'S']: "
    ).strip().lower()

    if fallback == "t":
        return "telegram"
    if fallback == "n":
        return "none"
    return "r2"


def send_r2_link_to_telegram(manga: str, vol: str, mobi_file: str, url: str) -> None:
    """Send a Cloudflare R2 download link to Telegram."""
    size_mb = os.path.getsize(mobi_file) / (1024 * 1024)
    safe_manga = html.escape(manga)
    safe_vol = html.escape(vol)
    safe_url = html.escape(url)
    msg_html = (
        f"📖 <b>{safe_manga}</b> - {safe_vol}\n\n"
        f"🔒 Cloudflare R2 (archivo de {size_mb:.2f} MB). Expira en 7d:\n\n"
        f"🔗 <a href='{safe_url}'>DESCARGAR AHORA</a>"
    )
    send_message(msg_html, parse_mode="HTML")


def _deliver_via_telegram(
    mobi_file: str, params: PipelineParams, app_config: AppConfig
) -> None:
    if app_config is APP_CONFIG:
        send_to_telegram(mobi_file)
    else:
        send_to_telegram(mobi_file, app_config=app_config)
    manga, vol = format_manga_title(mobi_file, app_config.output_folder_kcc)
    log_download(manga, vol, params.lang, mobi_file, "telegram")


def _deliver_via_r2(mobi_file: str, params: PipelineParams, app_config: AppConfig) -> None:
    manga, vol = format_manga_title(mobi_file, app_config.output_folder_kcc)
    url = send_to_r2(mobi_file, manga, vol)
    if url:
        send_r2_link_to_telegram(manga, vol, mobi_file, url)
        log_download(manga, vol, params.lang, mobi_file, "r2")
        return

    logger.warning(
        "Fallo al subir %s a R2. Haciendo fallback a Telegram clásico.",
        mobi_file,
    )
    _deliver_via_telegram(mobi_file, params, app_config)


def deliver_files(
    mobi_files: list[str],
    params: PipelineParams,
    input_func: Callable[[str], str] = input,
    app_config: AppConfig | None = None,
) -> None:
    """Entrega un lote de archivos.

    Intenta USB primero; si falla, usa R2/Telegram por flag o por fallback
    interactivo.
    """
    app_config = app_config or APP_CONFIG

    if not mobi_files:
        return

    usb_detected = False
    for mobi_file in mobi_files:
        if send_to_usb(mobi_file, params.title):
            usb_detected = True
            manga, vol = format_manga_title(mobi_file, app_config.output_folder_kcc)
            log_download(manga, vol, params.lang, mobi_file, "usb")

    if params.r2:
        for mobi_file in mobi_files:
            _deliver_via_r2(mobi_file, params, app_config)
        return

    if params.telegram:
        for mobi_file in mobi_files:
            _deliver_via_telegram(mobi_file, params, app_config)
        return

    if usb_detected:
        return

    is_interactive = len(sys.argv) <= 1
    if not is_interactive:
        return

    print(f"\n> Se generaron {len(mobi_files)} archivos pero no se detectó un Kindle.")
    choice = ask_fallback_choice(len(mobi_files), input_func)
    if choice == "telegram":
        for mobi_file in mobi_files:
            _deliver_via_telegram(mobi_file, params, app_config)
    elif choice == "r2":
        for mobi_file in mobi_files:
            _deliver_via_r2(mobi_file, params, app_config)
