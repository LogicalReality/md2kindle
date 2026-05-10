"""Subpackage de entrega — Telegram y ffsend."""

from md2kindle.services.delivery.manager import deliver_files
from md2kindle.services.delivery.telegram import send_to_telegram
from md2kindle.services.delivery.usb import send_to_usb

__all__ = ["send_to_telegram", "send_to_usb", "deliver_files"]
