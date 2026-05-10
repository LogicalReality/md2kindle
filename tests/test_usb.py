import os
import ntpath
import pytest
from unittest.mock import patch, MagicMock
from md2kindle.services.delivery.usb import get_kindle_drive, send_to_usb, get_volume_name, get_potential_mount_points

def test_get_potential_mount_points_windows(monkeypatch):
    monkeypatch.setattr("os.name", "nt")
    monkeypatch.setattr("os.path.exists", lambda p: p in ("C:\\", "E:\\"))
    points = get_potential_mount_points()
    assert points == ["C:\\", "E:\\"]

def test_get_potential_mount_points_linux(monkeypatch):
    monkeypatch.setattr("os.name", "posix")
    # Simulate not being on darwin
    monkeypatch.setattr("sys.platform", "linux")
    
    # Mock os.path.exists for base directories
    def mock_exists(path):
        return path in ("/media", "/run/media", "/mnt")
    monkeypatch.setattr("os.path.exists", mock_exists)
    
    # Mock os.listdir for those directories
    def mock_listdir(path):
        if path == "/media": return ["user1", "user2"]
        if path == "/run/media": return ["user1"]
        if path == "/mnt": return ["usb"]
        return []
    monkeypatch.setattr("os.listdir", mock_listdir)
    
    # Mock os.path.isdir to return true for everything under those bases
    monkeypatch.setattr("os.path.isdir", lambda p: True)
    
    points = get_potential_mount_points()
    assert "/media/user1" in points
    assert "/media/user2" in points
    assert "/run/media/user1" in points
    assert "/mnt/usb" in points

def test_get_potential_mount_points_macos(monkeypatch):
    monkeypatch.setattr("os.name", "posix")
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("os.path.exists", lambda p: p == "/Volumes")
    monkeypatch.setattr("os.listdir", lambda p: ["Kindle", "Macintosh HD"] if p == "/Volumes" else [])
    monkeypatch.setattr("os.path.isdir", lambda p: True)
    
    points = get_potential_mount_points()
    assert points == ["/Volumes/Kindle", "/Volumes/Macintosh HD"]

@patch("md2kindle.services.delivery.usb.os.path.exists")
@patch("md2kindle.services.delivery.usb.get_volume_name")
def test_get_kindle_drive_found(mock_vol_name, mock_exists):
    """Testea que el drive correcto se retorna cuando se cumplen los 3 factores."""
    # Simular que solo E:\ cumple todo
    def exists_side_effect(path):
        e_drive = "E:\\"
        if path in (
            e_drive,
            ntpath.join(e_drive, "documents"),
            ntpath.join(e_drive, "system"),
        ):
            return True
        if path == "C:\\":
            return True
        return False

    mock_exists.side_effect = exists_side_effect

    def vol_side_effect(drive):
        if drive == "E:\\": return "Kindle"
        return "Windows"

    mock_vol_name.side_effect = vol_side_effect

    # Pre-mockear os.name para simular Windows en caso de que los tests corran en Linux CI
    with patch("md2kindle.services.delivery.usb.os.name", "nt"):
        assert get_kindle_drive() == "E:\\"

@patch("md2kindle.services.delivery.usb.os.path.exists")
@patch("md2kindle.services.delivery.usb.get_volume_name")
def test_get_kindle_drive_fake(mock_vol_name, mock_exists):
    """Testea que un pendrive con carpetas similares pero distinto nombre sea rechazado."""
    def exists_side_effect(path):
        d_drive = "D:\\"
        if path in (
            d_drive,
            ntpath.join(d_drive, "documents"),
            ntpath.join(d_drive, "system"),
        ):
            return True
        return False

    mock_exists.side_effect = exists_side_effect

    def vol_side_effect(drive):
        if drive == "D:\\": return "KINGSTON"
        return ""

    mock_vol_name.side_effect = vol_side_effect

    with patch("md2kindle.services.delivery.usb.os.name", "nt"):
        assert get_kindle_drive() is None

@patch("md2kindle.services.delivery.usb.get_potential_mount_points")
@patch("md2kindle.services.delivery.usb.os.path.exists")
def test_get_kindle_drive_linux_found(mock_exists, mock_get_points):
    """Testea que en Linux se detecta correctamente verificando la firma del directorio."""
    mock_get_points.return_value = ["/run/media/user/Kindle", "/run/media/user/Other"]
    
    def exists_side_effect(path):
        import posixpath
        if path == posixpath.join("/run/media/user/Kindle", "documents"): return True
        if path == posixpath.join("/run/media/user/Kindle", "system"): return True
        return False
        
    mock_exists.side_effect = exists_side_effect
    
    with patch("md2kindle.services.delivery.usb.os.name", "posix"):
        with patch("sys.platform", "linux"):
            assert get_kindle_drive() == "/run/media/user/Kindle"

@patch("md2kindle.services.delivery.usb.get_potential_mount_points")
@patch("md2kindle.services.delivery.usb.os.path.exists")
def test_get_kindle_drive_macos_found(mock_exists, mock_get_points):
    """Testea que en macOS se detecta correctamente verificando la firma del directorio."""
    mock_get_points.return_value = ["/Volumes/KINDLE", "/Volumes/Macintosh HD"]
    
    def exists_side_effect(path):
        import posixpath
        if path == posixpath.join("/Volumes/KINDLE", "documents"): return True
        if path == posixpath.join("/Volumes/KINDLE", "system"): return True
        return False
        
    mock_exists.side_effect = exists_side_effect
    
    with patch("md2kindle.services.delivery.usb.os.name", "posix"):
        with patch("sys.platform", "darwin"):
            assert get_kindle_drive() == "/Volumes/KINDLE"

@patch("md2kindle.services.delivery.usb.get_kindle_drive")
@patch("md2kindle.services.delivery.usb.shutil.copy2")
@patch("md2kindle.services.delivery.usb.os.makedirs")
def test_send_to_usb_success(mock_makedirs, mock_copy, mock_get_drive):
    """Testea que se llame a copy2 con la ruta correcta (Manga/Titulo)."""
    # Use native pathing for the mock drive and file so os.path handles it correctly
    fake_drive = os.path.join("mnt", "fake_drive") if os.name == 'posix' else "E:\\"
    fake_file = os.path.join("home", "user", "manga_vol_1.mobi") if os.name == 'posix' else "C:\\manga_vol_1.mobi"
    
    mock_get_drive.return_value = fake_drive

    result = send_to_usb(fake_file, "Berserk")

    assert result is True
    expected_dest = os.path.join(fake_drive, "documents", "Manga", "Berserk", "manga_vol_1.mobi")
    mock_copy.assert_called_once_with(fake_file, expected_dest)
