"""Configuración centralizada de logging para md2kindle.

Reemplaza los ~40 print() distribuidos por todos los módulos.
--silent se resuelve con un solo setLevel(WARNING) en lugar de
'if not p["silent"]: print(...)' en 15 lugares.
"""

import logging
import sys


def setup_logging(silent: bool = False) -> None:
    """Configura el logging global de la aplicación.

    Args:
        silent: Si True, solo muestra WARNING y superiores.
    """
    level = logging.WARNING if silent else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    # Configurar el logger raíz del paquete
    root_logger = logging.getLogger("md2kindle")
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Evitar propagación al root logger (duplicar mensajes)
    root_logger.propagate = False
