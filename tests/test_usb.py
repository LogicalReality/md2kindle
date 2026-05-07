import os
import pytest
from unittest.mock import patch, MagicMock
from md2kindle.delivery.usb import get_kindle_drive, send_to_usb, get_volume_name

@patch("md2kindle.delivery.usb.os.path.exists")
@patch("md2kindle.delivery.usb.get_volume_name")
def test_get_kindle_drive_found(mock_vol_name, mock_exists):
    """Testea que el drive correcto se retorna cuando se cumplen los 3 factores."""
    # Simular que solo E:\ cumple todo
    def exists_side_effect(path):
        if "E:\\documents" in path or "E:\\system" in path or "E:\\" == path:
            return True
        if "C:\\" == path:
            return True
        return False

    mock_exists.side_effect = exists_side_effect

    def vol_side_effect(drive):
        if drive == "E:\\": return "Kindle"
        return "Windows"

    mock_vol_name.side_effect = vol_side_effect

    # Pre-mockear os.name para simular Windows en caso de que los tests corran en Linux CI
    with patch("md2kindle.delivery.usb.os.name", "nt"):
        assert get_kindle_drive() == "E:\\"

@patch("md2kindle.delivery.usb.os.path.exists")
@patch("md2kindle.delivery.usb.get_volume_name")
def test_get_kindle_drive_fake(mock_vol_name, mock_exists):
    """Testea que un pendrive con carpetas similares pero distinto nombre sea rechazado."""
    def exists_side_effect(path):
        if "D:\\documents" in path or "D:\\system" in path or "D:\\" == path:
            return True
        return False

    mock_exists.side_effect = exists_side_effect

    def vol_side_effect(drive):
        if drive == "D:\\": return "KINGSTON"
        return ""

    mock_vol_name.side_effect = vol_side_effect

    with patch("md2kindle.delivery.usb.os.name", "nt"):
        assert get_kindle_drive() is None

@patch("md2kindle.delivery.usb.get_kindle_drive")
@patch("md2kindle.delivery.usb.shutil.copy2")
@patch("md2kindle.delivery.usb.os.makedirs")
def test_send_to_usb_success(mock_makedirs, mock_copy, mock_get_drive):
    """Testea que se llame a copy2 con la ruta correcta (Manga/Titulo)."""
    fake_drive = "E:\\"
    mock_get_drive.return_value = fake_drive

    result = send_to_usb("C:\\manga_vol_1.mobi", "Berserk")

    assert result is True
    expected_dest = os.path.join(fake_drive, "documents", "Manga", "Berserk", "manga_vol_1.mobi")
    mock_copy.assert_called_once_with("C:\\manga_vol_1.mobi", expected_dest)
