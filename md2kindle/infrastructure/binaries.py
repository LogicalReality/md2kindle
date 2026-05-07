"""Detección de binarios externos."""

from dataclasses import dataclass
import glob
import os
import shutil


@dataclass(frozen=True)
class BinaryPaths:
    """Rutas resueltas para comandos externos."""

    mangadex_dl: str
    kcc_c2e: str
    ffsend: str


def find_binary(pattern, subfolder=None, *, root_dir=None, bin_dir=None):
    """Busca un binario portable usando wildcards.

    Si hay varios, devuelve el último por orden lexicográfico descendente,
    preservando el comportamiento histórico del proyecto.
    """
    root_dir = root_dir or os.getcwd()
    bin_dir = bin_dir or os.path.join(root_dir, "bin")

    search_dirs = [
        os.path.join(bin_dir, subfolder) if subfolder else bin_dir,
        os.path.join(root_dir, subfolder) if subfolder else root_dir,
    ]

    for directory in search_dirs:
        matches = glob.glob(os.path.join(directory, pattern))
        if matches:
            return sorted(matches, reverse=True)[0]
    return None


def resolve_binaries(*, root_dir, os_name=None) -> BinaryPaths:
    """Resuelve binarios locales o desde PATH."""
    os_name = os_name or os.name

    mangadex_local = find_binary(
        "mangadex-dl*.exe", "mangadex-dl", root_dir=root_dir
    )
    kcc_local = find_binary("kcc*c2e*.exe", root_dir=root_dir) or find_binary(
        "kcc*.exe", root_dir=root_dir
    )
    ffsend_local = find_binary("ffsend*.exe", root_dir=root_dir)

    return BinaryPaths(
        mangadex_dl=(
            mangadex_local
            if mangadex_local and os_name == "nt"
            else (shutil.which("mangadex-dl") or "mangadex-dl")
        ),
        kcc_c2e=(
            kcc_local
            if kcc_local and os_name == "nt"
            else (shutil.which("kcc-c2e") or "kcc-c2e")
        ),
        ffsend=(
            ffsend_local
            if ffsend_local and os_name == "nt"
            else (shutil.which("ffsend") or "ffsend")
        ),
    )
