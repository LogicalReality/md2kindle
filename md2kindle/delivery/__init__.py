"""Subpackage de entrega — Telegram y ffsend."""

from md2kindle.delivery.telegram import send_to_telegram
from md2kindle.delivery.usb import send_to_usb

__all__ = ["send_to_telegram", "send_to_usb"]
