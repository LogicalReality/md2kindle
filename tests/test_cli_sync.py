import pytest
import sys
from unittest.mock import patch, MagicMock
from md2kindle.app.cli import resolve_parameters

def test_cli_sync_flag_no_url():
    """Verifica que el flag --sync funcione sin URL."""
    with patch.object(sys, "argv", ["md2kindle", "--sync"]):
        # Si no falla con SystemExit (error de argparse), es que lo aceptó
        params = resolve_parameters()
        assert params.sync is True

def test_cli_sync_flag_with_url():
    """Verifica que el flag --sync funcione con URL (aunque no se use en el pipeline final)."""
    test_url = "https://mangadex.org/title/123"
    with patch.object(sys, "argv", ["md2kindle", test_url, "--sync"]):
        with patch("md2kindle.app.cli.get_manga_title_options") as mock_get:
            mock_get.return_value = ([], "Author", {}, "uuid-123")
            params = resolve_parameters()
            assert params.sync is True
            assert params.manga.manga_uuid == "uuid-123"
