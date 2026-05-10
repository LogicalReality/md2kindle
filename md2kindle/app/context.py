"""Helpers compartidos para la capa de aplicación."""

from md2kindle.core.config import AppConfig


def config_kwargs(explicit_config: bool, app_config: AppConfig) -> dict:
    """Pasa AppConfig solo cuando el caller lo inyectó explícitamente."""
    return {"app_config": app_config} if explicit_config else {}
