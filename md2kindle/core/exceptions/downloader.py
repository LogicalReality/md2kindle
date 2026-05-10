"""Downloader domain exceptions."""

from .base import MD2KindleError

class DownloadError(MD2KindleError):
    """Raised when Mangadex download fails."""
    pass
