"""Descarga básica de manga."""

import logging
import subprocess

from md2kindle.core.config import APP_CONFIG, AppConfig
from md2kindle.core.exceptions import DownloadError

logger = logging.getLogger(__name__)


def download_manga(
    url,
    target_path,
    lang,
    mode,
    start_val,
    end_val,
    skip_oneshots,
    app_config: AppConfig | None = None,
):
    app_config = app_config or APP_CONFIG

    if mode == "v":
        save_as = "cbz-volume"
        range_args = ["--start-volume", start_val, "--end-volume", end_val]
    else:
        # Descarga capítulos en un solo archivo CBZ
        save_as = "cbz-single"
        range_args = ["--start-chapter", start_val, "--end-chapter", end_val]

    # Construcción dinámica del comando para evitar errores de posición (como el de --language)
    cmd = [
        app_config.binaries.mangadex_dl,
        url,
        "--save-as",
        save_as,
        "--language",
        lang,
    ]

    # Aplicamos el filtro de oneshots de forma dinamica segun el prompt del usuario
    if skip_oneshots:
        cmd.append("--no-oneshot-chapter")

    # Añadimos el resto de parámetros al final
    cmd.extend(range_args)
    cmd.extend(["--path", target_path])

    logger.info("Ejecutando descarga en: %s", target_path)
    logger.info("Descargando manga...")

    try:
        result = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            logger.info("Descarga completada")
            return True
        else:
            logger.error("Falló la descarga")
            return False
    except Exception as e:
        logger.error("Excepción al ejecutar mangadex-dl: %s", e)
        raise DownloadError(f"Fallo crítico al ejecutar mangadex-dl: {e}") from e
