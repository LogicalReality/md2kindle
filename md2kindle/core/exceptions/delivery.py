"""Delivery domain exceptions."""

from .base import MD2KindleError

class DeliveryError(MD2KindleError):
    """Raised when a delivery service fails."""
    pass
