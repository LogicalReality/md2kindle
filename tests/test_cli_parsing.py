import pytest
import sys
from unittest.mock import patch, MagicMock
from md2kindle.app.cli import resolve_parameters

def test_cli_positional_url():
    """Verifica que el URL posicional funcione correctamente."""
    test_url = "https://mangadex.org/title/123"
    with patch.object(sys, "argv", ["md2kindle", test_url]):
        with patch("md2kindle.app.cli.get_manga_title_options") as mock_get:
            mock_get.return_value = ([], "Author", {}, "uuid-123")
            params = resolve_parameters()
            assert params.manga.url == f"https://mangadex.org/title/uuid-123"

def test_cli_flag_url():
    """Verifica que el flag --url funcione correctamente."""
    test_url = "https://mangadex.org/title/456"
    with patch.object(sys, "argv", ["md2kindle", "--url", test_url]):
        with patch("md2kindle.app.cli.get_manga_title_options") as mock_get:
            mock_get.return_value = ([], "Author", {}, "uuid-456")
            params = resolve_parameters()
            assert params.manga.url == f"https://mangadex.org/title/uuid-456"

def test_cli_url_collision_same():
    """Verifica que si ambos son iguales, no explote."""
    test_url = "https://mangadex.org/title/789"
    with patch.object(sys, "argv", ["md2kindle", test_url, "--url", test_url]):
        with patch("md2kindle.app.cli.get_manga_title_options") as mock_get:
            mock_get.return_value = ([], "Author", {}, "uuid-789")
            params = resolve_parameters()
            assert params.manga.url == f"https://mangadex.org/title/uuid-789"

def test_cli_url_collision_different():
    """Verifica que si son distintos, lance error de parser."""
    url1 = "https://mangadex.org/title/1"
    url2 = "https://mangadex.org/title/2"
    with patch.object(sys, "argv", ["md2kindle", url1, "--url", url2]):
        with pytest.raises(SystemExit):
            # argparse.error lanza SystemExit
            resolve_parameters()

def test_cli_unknown_flag():
    """Verifica que flags desconocidos lancen error (ahora que usamos parse_args)."""
    with patch.object(sys, "argv", ["md2kindle", "url", "--unknown-flag"]):
        with pytest.raises(SystemExit):
            resolve_parameters()
