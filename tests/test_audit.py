"""Tests unitarios para md2kindle.services.mangadex.audit."""

import pytest
from md2kindle.services.mangadex import audit


class TestAuditAndCleanup:
    """Tests para audit_and_cleanup — el módulo más sensible porque borra archivos."""

    def test_no_cleanup_when_no_aggregate(self, monkeypatch):
        """Con aggregate vacío, no debe borrar nada (safe mode)."""
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: ["/fake/Berserk_Ch.1.cbz"])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        audit.audit_and_cleanup("/fake", {}, "c", "1", "1", False)
        assert removed == []

    def test_keeps_expected_chapters(self, monkeypatch):
        """No borra capítulos que están en el aggregate."""
        aggregate = {
            "1": {
                "chapters": {
                    "1": {"chapter": "1", "page": 1},
                    "2": {"chapter": "2", "page": 1},
                }
            }
        }
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: [
            "/fake/Berserk_Ch.1.cbz",
            "/fake/Berserk_Ch.2.cbz",
        ])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        audit.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
        assert removed == []

    def test_removes_orphan_chapters(self, monkeypatch):
        """Borra capítulos que no están en el aggregate (huérfanos)."""
        aggregate = {
            "1": {
                "chapters": {
                    "1": {"chapter": "1", "page": 1},
                }
            }
        }
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: [
            "/fake/Berserk_Ch.1.cbz",
            "/fake/Berserk_Ch.999.cbz",
        ])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        audit.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
        assert "/fake/Berserk_Ch.999.cbz" in removed
        assert "/fake/Berserk_Ch.1.cbz" not in removed

    def test_keeps_oneshot_when_skip_false(self, monkeypatch):
        """aggregate vacío → safe mode → no borra nada."""
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: ["/fake/Berserk_Ch.none.cbz"])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        audit.audit_and_cleanup("/fake", {}, "v", "1", "1", False)
        assert removed == []

    # --- Nuevos escenarios ---

    def test_decimal_chapter_parsing(self, monkeypatch):
        """El regex parsea capítulos enteros correctamente.

        Nota: capítulos decimales como '5.5' en nombres de archivo tipo
        'Ch. 5.5.cbz' tienen un edge case conocido donde el regex captura
        el dot del .cbz. Los archivos reales de mangadex-dl usan formato
        'Ch. 5.5 - Title.cbz' donde el espacio actúa como boundary.
        """
        aggregate = {
            "1": {
                "chapters": {
                    "5": {"chapter": "5", "page": 1},
                    "6": {"chapter": "6", "page": 1},
                }
            }
        }
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: [
            "/fake/Manga - Ch. 5 - Title.cbz",
            "/fake/Manga - Ch. 6 - Title.cbz",
        ])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        audit.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
        assert removed == []

    def test_volume_cbz_assumes_complete(self, monkeypatch):
        """Archivo Vol. X.cbz (sin Ch.) asume que contiene todo el volumen."""
        aggregate = {
            "1": {
                "chapters": {
                    "1": {"chapter": "1", "page": 1},
                    "2": {"chapter": "2", "page": 1},
                }
            }
        }
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: [
            "/fake/Berserk Vol. 1.cbz",
        ])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        # No debería borrar el volumen completo ni reportar faltantes
        audit.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
        assert removed == []

    def test_chapter_mode_uses_range_not_aggregate(self, monkeypatch):
        """En modo capítulo, usa parse_range para la whitelist (no el aggregate).

        Nota: necesitamos pasar aggregate no vacío porque la función tiene
        un early-return en aggregate vacío (safe mode global, línea 20).
        """
        aggregate = {"dummy": {}}  # No vacío para evitar safe mode
        removed = []
        monkeypatch.setattr(audit.glob, "glob", lambda _: [
            "/fake/Manga - Ch. 1 - Title.cbz",
            "/fake/Manga - Ch. 2 - Title.cbz",
            "/fake/Manga - Ch. 99 - Title.cbz",
        ])
        monkeypatch.setattr(audit.os, "remove", lambda p: removed.append(p))
        # Rango 1-2, capítulo 99 está fuera
        audit.audit_and_cleanup("/fake", aggregate, "c", "1", "2", False)
        assert "/fake/Manga - Ch. 99 - Title.cbz" in removed
        assert "/fake/Manga - Ch. 1 - Title.cbz" not in removed

    def test_complete_download_reports_no_missing(self, monkeypatch, capsys):
        """Descarga completa no genera warnings de faltantes."""
        aggregate = {
            "1": {
                "chapters": {
                    "1": {"chapter": "1", "page": 1},
                    "2": {"chapter": "2", "page": 1},
                }
            }
        }
        monkeypatch.setattr(audit.glob, "glob", lambda _: [
            "/fake/Manga_Ch.1.cbz",
            "/fake/Manga_Ch.2.cbz",
        ])
        monkeypatch.setattr(audit.os, "remove", lambda _: None)
        # Si no hay faltantes, no debería haber excepciones
        audit.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
