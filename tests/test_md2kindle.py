import os
import sys
import tempfile
import glob
import pytest
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from md2kindle import config
from md2kindle.mangadex import downloader
from md2kindle import cli
from md2kindle.mangadex import api
from md2kindle import converter
from md2kindle.delivery import telegram
from md2kindle import pipeline
from md2kindle.ranges import parse_range
from md2kindle.models import PipelineParams


class TestParseRange:
    def test_single_value_returns_list(self):
        result = parse_range("5", "5")
        assert result == ["5"]

    def test_range_integers(self):
        result = parse_range("1", "5")
        assert result == ["1", "2", "3", "4", "5"]

    def test_range_decimal(self):
        result = parse_range("1.5", "3.5")
        assert result == ["1.5", "3.5"]

    def test_alphanumeric(self):
        result = parse_range("S1", "S1")
        assert result == ["S1"]

    def test_float_27_0_normalized(self):
        result = parse_range("27.0", "27.0")
        assert result == ["27.0"]


class TestSanitizeFilename:
    def test_removes_forbidden_chars(self):
        result = config.sanitize_filename("test:file*name?.txt")
        assert result == "testfilename.txt"

    def test_removes_windows_pipe(self):
        result = config.sanitize_filename("file|name")
        assert result == "filename"

    def test_strips_whitespace(self):
        result = config.sanitize_filename("  title  ")
        assert result == "title"

    def test_preserves_normal_chars(self):
        result = config.sanitize_filename("Berserk_-_Vol_25")
        assert result == "Berserk_-_Vol_25"


class TestIsCIDetection:
    def test_ci_env_true(self, monkeypatch):
        monkeypatch.setenv("CI", "true")
        importlib.reload(config)
        assert config.IS_CI == True

    def test_github_actions_true(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        importlib.reload(config)
        assert config.IS_CI == True

    def test_no_ci_vars(self, monkeypatch):
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        importlib.reload(config)
        assert config.IS_CI == False


class TestAuditAndCleanup:
    def test_no_cleanup_when_no_aggregate(self, monkeypatch):
        # Con aggregate vacío, no debe borrar nada
        removed = []
        monkeypatch.setattr(downloader.glob, "glob", lambda _: ["/fake/Berserk_Ch.1.cbz"])
        monkeypatch.setattr(downloader.os, "remove", lambda p: removed.append(p))
        downloader.audit_and_cleanup("/fake", {}, "c", "1", "1", False)
        assert removed == []

    def test_keeps_expected_chapters(self, monkeypatch):
        aggregate = {
            "1": {
                "chapters": {
                    "1": {"chapter": "1", "page": 1},
                    "2": {"chapter": "2", "page": 1},
                }
            }
        }
        removed = []
        monkeypatch.setattr(downloader.glob, "glob", lambda _: [
            "/fake/Berserk_Ch.1.cbz",
            "/fake/Berserk_Ch.2.cbz",
        ])
        monkeypatch.setattr(downloader.os, "remove", lambda p: removed.append(p))
        downloader.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
        assert removed == []  # Ninguno es huérfano

    def test_removes_orphan_chapters(self, monkeypatch):
        aggregate = {
            "1": {
                "chapters": {
                    "1": {"chapter": "1", "page": 1},
                }
            }
        }
        removed = []
        monkeypatch.setattr(downloader.glob, "glob", lambda _: [
            "/fake/Berserk_Ch.1.cbz",
            "/fake/Berserk_Ch.999.cbz",
        ])
        monkeypatch.setattr(downloader.os, "remove", lambda p: removed.append(p))
        downloader.audit_and_cleanup("/fake", aggregate, "v", "1", "1", False)
        assert "/fake/Berserk_Ch.999.cbz" in removed
        assert "/fake/Berserk_Ch.1.cbz" not in removed

    def test_keeps_oneshot_when_skip_false(self, monkeypatch):
        # aggregate vacío → safe mode → no borra nada
        removed = []
        monkeypatch.setattr(downloader.glob, "glob", lambda _: ["/fake/Berserk_Ch.none.cbz"])
        monkeypatch.setattr(downloader.os, "remove", lambda p: removed.append(p))
        downloader.audit_and_cleanup("/fake", {}, "v", "1", "1", False)
        assert removed == []


class TestDownloadManga:
    def test_returns_true_on_success(self, monkeypatch):
        class MockResult:
            returncode = 0

        monkeypatch.setattr(downloader.subprocess, "run", lambda *a, **kw: MockResult())

        result = downloader.download_manga(
            "https://mangadex.org/title/123",
            "/fake/target",
            "es-la",
            "v",
            "1",
            "1",
            False,
        )
        assert result is True


class TestMainApproval:
    def test_main_volume_flow_success(self, monkeypatch):
        # Configurar espías para capturar el flujo de ejecución
        calls = []

        def mock_exists(path):
            return False

        def mock_which(cmd):
            return True

        def mock_resolve():
            return PipelineParams(
                url="http://test",
                title="TestManga",
                lang="es-la",
                mode="v",
                start="1",
                end="1",
                author="TestAuthor",
                manga_uuid="123",
                skip_oneshots=False,
                silent=True,
                telegram=True,
                r2=False,
            )

        def mock_aggregate(uuid, lang):
            return {"1": {"chapters": {"1": {}}}}

        def mock_download(*args):
            calls.append(("download", args[3], args[4]))  # mode, start
            return True

        def mock_audit(*args):
            calls.append(("audit", args[2], args[3]))
            return True

        def mock_convert(*args, **kwargs):
            calls.append(("convert", args[0]))
            return ["test_vol_1.mobi"]

        def mock_deliver(files, params):
            calls.append(("deliver", files, params.title))

        glob_calls = []

        def mock_glob(pattern):
            glob_calls.append(pattern)
            return [] if len(glob_calls) == 1 else ["downloaded.cbz"]

        monkeypatch.setattr(cli.os.path, "exists", mock_exists)
        monkeypatch.setattr(cli.shutil, "which", mock_which)
        monkeypatch.setattr(cli, "resolve_parameters", mock_resolve)
        monkeypatch.setattr(pipeline, "get_manga_aggregate", mock_aggregate)
        monkeypatch.setattr(pipeline, "download_manga", mock_download)
        monkeypatch.setattr(pipeline, "audit_and_cleanup", mock_audit)
        monkeypatch.setattr(pipeline, "convert_with_kcc", mock_convert)
        monkeypatch.setattr(pipeline, "deliver_files", mock_deliver)
        monkeypatch.setattr(pipeline.glob, "glob", mock_glob)

        cli.main()

        # Approval: Verificamos que se llame exactamente a estos flujos en este orden
        expected_folder = pipeline.os.path.join(config.OUTPUT_FOLDER_MANGA, "TestManga", "Vol 1")
        assert calls == [
            ("download", "v", "1"),
            ("audit", "v", "1"),
            ("convert", expected_folder),
            ("deliver", ["test_vol_1.mobi"], "TestManga")
        ]
