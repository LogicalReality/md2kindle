"""Interfaces formales para los servicios del pipeline."""

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from md2kindle.core.models import PipelineContext

@runtime_checkable
class Converter(Protocol):
    """Protocolo para servicios de conversión (ej: KCC)."""

    def convert(
        self,
        target_path: str,
        author: str,
        title: str,
        vol_hint: str | None = None,
    ) -> list[str]:
        """Convierte archivos fuente a formato Kindle.
        
        Args:
            target_path: Carpeta con los archivos fuente (.cbz).
            author: Autor del manga para los metadatos.
            title: Título del manga para los metadatos.
            vol_hint: Hint opcional del volumen/capítulo.
            
        Returns:
            Lista de paths absolutos a los archivos generados.
        """
        ...

@runtime_checkable
class Deliverer(Protocol):
    """Protocolo para servicios de entrega (ej: USB, Telegram, R2)."""

    def deliver(
        self,
        files: list[str],
        context: "PipelineContext",
    ) -> None:
        """Entrega archivos al destino configurado.
        
        Args:
            files: Lista de paths absolutos a entregar.
            context: Contexto completo del pipeline.
        """
        ...
