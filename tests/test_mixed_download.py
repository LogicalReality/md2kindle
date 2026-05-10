"""Tests unitarios para md2kindle.services.mangadex.mixed_download."""

import pytest
from unittest.mock import patch, MagicMock
from md2kindle.services.mangadex.mixed_download import (
    _group_contiguous_ranges,
    download_volume_mixed,
)


class TestGroupContiguousRanges:
    """Tests para la agrupación de capítulos en rangos contiguos."""

    def test_contiguous_chapters(self):
        result = _group_contiguous_ranges(["1", "2", "3", "5", "6"])
        assert result == [("1", "3"), ("5", "6")]

    def test_empty_list(self):
        assert _group_contiguous_ranges([]) == []

    def test_single_chapter(self):
        result = _group_contiguous_ranges(["5"])
        assert result == [("5", "5")]

    def test_all_contiguous(self):
        result = _group_contiguous_ranges(["10", "11", "12", "13"])
        assert result == [("10", "13")]

    def test_all_disjoint(self):
        result = _group_contiguous_ranges(["1", "5", "10"])
        assert result == [("1", "1"), ("5", "5"), ("10", "10")]

    def test_unsorted_input(self):
        """Los capítulos desordenados se ordenan antes de agrupar."""
        result = _group_contiguous_ranges(["3", "1", "2"])
        assert result == [("1", "3")]

    def test_decimal_chapters(self):
        """Capítulos decimales respetan gaps > 1.0."""
        result = _group_contiguous_ranges(["1", "1.5", "2", "5"])
        # 1 → 1.5 (gap 0.5), 1.5 → 2 (gap 0.5), 2 → 5 (gap 3, break)
        assert result == [("1", "2"), ("5", "5")]


class TestDownloadVolumeMixed:
    """Tests para la orquestación de descargas multi-idioma."""

    def _make_config(self):
        config = MagicMock()
        config.binaries.mangadex_dl = "mangadex-dl"
        return config

    @patch("md2kindle.services.mangadex.mixed_download.zipfile.ZipFile")
    @patch("md2kindle.services.mangadex.mixed_download.os.path.exists", return_value=False)
    @patch("md2kindle.services.mangadex.mixed_download.os.walk", return_value=[])
    @patch("md2kindle.services.mangadex.mixed_download.os.listdir", return_value=[])
    @patch("md2kindle.services.mangadex.mixed_download.subprocess.run")
    def test_single_language_calls_subprocess_once(self, mock_run, *_):
        """Un solo idioma con rango contiguo genera una sola llamada."""
        mock_run.return_value = MagicMock(returncode=0)
        chapter_map = {"1": "en", "2": "en", "3": "en"}

        result = download_volume_mixed(
            "http://mangadex.org/title/123",
            "/tmp/test",
            chapter_map,
            vol="1",
            app_config=self._make_config(),
        )

        assert result is True
        assert mock_run.call_count == 1

    @patch("md2kindle.services.mangadex.mixed_download.zipfile.ZipFile")
    @patch("md2kindle.services.mangadex.mixed_download.os.path.exists", return_value=False)
    @patch("md2kindle.services.mangadex.mixed_download.os.walk", return_value=[])
    @patch("md2kindle.services.mangadex.mixed_download.os.listdir", return_value=[])
    @patch("md2kindle.services.mangadex.mixed_download.subprocess.run")
    def test_mixed_languages_calls_subprocess_per_group(self, mock_run, *_):
        """Dos idiomas con rangos contiguos generan 2 llamadas."""
        mock_run.return_value = MagicMock(returncode=0)
        chapter_map = {"1": "en", "2": "en", "3": "es-la"}

        result = download_volume_mixed(
            "http://mangadex.org/title/123",
            "/tmp/test",
            chapter_map,
            vol="1",
            app_config=self._make_config(),
        )

        assert result is True
        assert mock_run.call_count == 2

    @patch("md2kindle.services.mangadex.mixed_download.subprocess.run")
    def test_partial_failure_returns_true(self, mock_run):
        """Si un idioma falla pero otro tiene éxito, retorna True (empaquetado parchado)."""
        mock_run.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=0),
        ]
        chapter_map = {"1": "en", "2": "es-la"}

        with patch("md2kindle.services.mangadex.mixed_download.zipfile.ZipFile"), \
             patch("md2kindle.services.mangadex.mixed_download.os.path.exists", return_value=False), \
             patch("md2kindle.services.mangadex.mixed_download.os.walk", return_value=[]), \
             patch("md2kindle.services.mangadex.mixed_download.os.listdir", return_value=[]):
            result = download_volume_mixed(
                "http://mangadex.org/title/123",
                "/tmp/test",
                chapter_map,
                vol="1",
                app_config=self._make_config(),
            )

        assert result is True

    @patch("md2kindle.services.mangadex.mixed_download.subprocess.run")
    def test_total_failure_returns_false(self, mock_run):
        """Si todos los grupos fallan, retorna False (sin empaquetado)."""
        mock_run.return_value = MagicMock(returncode=1)
        chapter_map = {"1": "en", "2": "es-la"}

        result = download_volume_mixed(
            "http://mangadex.org/title/123",
            "/tmp/test",
            chapter_map,
            vol="1",
            app_config=self._make_config(),
        )

        assert result is False

    @patch("md2kindle.services.mangadex.mixed_download.zipfile.ZipFile")
    @patch("md2kindle.services.mangadex.mixed_download.os.path.exists", return_value=False)
    @patch("md2kindle.services.mangadex.mixed_download.os.walk", return_value=[])
    @patch("md2kindle.services.mangadex.mixed_download.os.listdir", return_value=[])
    @patch("md2kindle.services.mangadex.mixed_download.subprocess.run")
    def test_noncontiguous_ranges_split_calls(self, mock_run, *_):
        """Rangos no contiguos dentro del mismo idioma generan múltiples llamadas."""
        mock_run.return_value = MagicMock(returncode=0)
        # caps 1-3 y 10-11, mismo idioma → 2 llamadas
        chapter_map = {"1": "en", "2": "en", "3": "en", "10": "en", "11": "en"}

        download_volume_mixed(
            "http://mangadex.org/title/123",
            "/tmp/test",
            chapter_map,
            vol="1",
            app_config=self._make_config(),
        )

        assert mock_run.call_count == 2
