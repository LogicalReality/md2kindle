"""Converter domain exceptions."""

from .base import MD2KindleError

class ConversionError(MD2KindleError):
    """Raised when KCC conversion fails."""
    pass
