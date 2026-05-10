"""Modelos de datos tipados para el pipeline de md2kindle."""

from dataclasses import dataclass
from .manga import MangaContext
from .chapter import DownloadRange
from .delivery import DeliveryOptions

@dataclass
class PipelineContext:
    """Parámetros resueltos para la ejecución del pipeline.

    Contiene el contexto completo dividido por dominio.
    """
    manga: MangaContext
    range: DownloadRange
    delivery: DeliveryOptions
    silent: bool
