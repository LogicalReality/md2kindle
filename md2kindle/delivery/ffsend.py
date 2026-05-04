"""Upload cifrado via ffsend (Firefox Send E2EE)."""

import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)


from md2kindle.config import FFSEND_PATH

def upload_to_ffsend(file_path):
    """Sube un archivo a ffsend (Firefox Send) - Encriptación de Extremo a Extremo"""
    # Verificamos si ffsend está instalado en el sistema o en la carpeta bin/
    ffsend_bin = FFSEND_PATH
    if ffsend_bin == "ffsend" and not shutil.which("ffsend"):
        ffsend_bin = None

    if not ffsend_bin:
        logger.error(
            "ffsend no encontrado en el PATH ni en la carpeta bin. Es obligatorio para archivos > 45MB."
        )
        return None

    url_host = "https://send.vis.ee"  # Instancia comunitaria estable
    logger.info("Subiendo a %s (Bóveda Cifrada E2EE)...", url_host)

    try:
        # Comando: ffsend upload <file> --downloads 5 --expiry 12h --host <host> --quiet --no-interact
        cmd = [
            ffsend_bin,
            "upload",
            file_path,
            "--downloads",
            "5",
            "--expiry",
            "12h",
            "--host",
            url_host,
            "--quiet",
            "--no-interact",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            link = result.stdout.strip()
            return link
        else:
            logger.error(
                "Error en ffsend (Code %d): %s", result.returncode, result.stderr
            )
            return None
    except Exception as e:
        logger.error("Excepción al ejecutar ffsend: %s", e)
        return None
