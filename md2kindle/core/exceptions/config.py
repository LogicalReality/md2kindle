"""Configuration domain exceptions."""

from .base import MD2KindleError

class ConfigurationError(MD2KindleError):
    """Raised when environment or binary configuration is invalid."""
    pass
