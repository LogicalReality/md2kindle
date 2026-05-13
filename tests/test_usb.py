import os
import ntpath
import pytest
from unittest.mock import patch, MagicMock
from md2kindle.services.delivery.usb import get_kindle_drive, send_to_usb, get_volume_name, get_potential_mount_points

def test_get_potential_mount_points_windows(monkeypatch):
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "nt")
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", lambda p: p in ("C:\\", "E:\\"))
    points = get_potential_mount_points()
    assert points == ["C:\\", "E:\\"]

def test_get_potential_mount_points_linux(monkeypatch):
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "posix")
    monkeypatch.setattr("sys.platform", "linux")
    
    def mock_exists(path):
        return path in ("/media", "/run/media", "/mnt")
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", mock_exists)
    
    def mock_listdir(path):
        if path == "/media": return ["user1", "user2"]
        if path == "/run/media": return ["user1"]
        if path == "/mnt": return ["usb"]
        return []
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.listdir", mock_listdir)
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.path.isdir", lambda p: True)
    
    points = get_potential_mount_points()
    assert "/media/user1" in points
    assert "/media/user2" in points
    assert "/run/media/user1" in points
    assert "/mnt/usb" in points

def test_get_potential_mount_points_macos(monkeypatch):
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "posix")
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", lambda p: p == "/Volumes")
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.listdir", lambda p: ["Kindle", "Macintosh HD"] if p == "/Volumes" else [])
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.path.isdir", lambda p: True)
    
    points = get_potential_mount_points()
    assert points == ["/Volumes/Kindle", "/Volumes/Macintosh HD"]

def test_get_kindle_drive_found(monkeypatch):
    """Testea que el drive correcto se retorna cuando se cumplen los 3 factores."""
    def exists_side_effect(path):
        e_drive = "E:\\"
        if path in (e_drive, ntpath.join(e_drive, "documents"), ntpath.join(e_drive, "system")):
            return True
        if path == "C:\\":
            return True
        return False

    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", exists_side_effect)
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "nt")
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.get_volume_name", lambda d: "Kindle" if d == "E:\\" else "Windows")

    assert get_kindle_drive() == "E:\\"

def test_get_kindle_drive_fake(monkeypatch):
    """Testea que un pendrive con carpetas similares pero distinto nombre sea rechazado."""
    def exists_side_effect(path):
        d_drive = "D:\\"
        if path in (d_drive, ntpath.join(d_drive, "documents"), ntpath.join(d_drive, "system")):
            return True
        return False

    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", exists_side_effect)
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "nt")
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.get_volume_name", lambda d: "KINGSTON" if d == "D:\\" else "")

    assert get_kindle_drive() is None

def test_get_kindle_drive_linux_found(monkeypatch):
    """Testea que en Linux se detecta correctamente verificando la firma del directorio."""
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.get_potential_mount_points", lambda: ["/run/media/user/Kindle", "/run/media/user/Other"])
    
    def exists_side_effect(path):
        import posixpath
        if path == posixpath.join("/run/media/user/Kindle", "documents"): return True
        if path == posixpath.join("/run/media/user/Kindle", "system"): return True
        return False
        
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", exists_side_effect)
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "posix")
    monkeypatch.setattr("sys.platform", "linux")
    
    assert get_kindle_drive() == "/run/media/user/Kindle"

def test_get_kindle_drive_macos_found(monkeypatch):
    """Testea que en macOS se detecta correctamente verificando la firma del directorio."""
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.get_potential_mount_points", lambda: ["/Volumes/KINDLE", "/Volumes/Macintosh HD"])
    
    def exists_side_effect(path):
        import posixpath
        if path == posixpath.join("/Volumes/KINDLE", "documents"): return True
        if path == posixpath.join("/Volumes/KINDLE", "system"): return True
        return False
        
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.path_exists", exists_side_effect)
    monkeypatch.setattr("md2kindle.services.delivery.usb.discovery.os.name", "posix")
    monkeypatch.setattr("sys.platform", "darwin")
    
    assert get_kindle_drive() == "/Volumes/KINDLE"

@patch("md2kindle.services.delivery.usb.get_kindle_drive")
@patch("md2kindle.services.delivery.usb.mass_storage.shutil_copy2")
@patch("md2kindle.services.delivery.usb.mass_storage.os.makedirs")
def test_send_to_usb_success(mock_makedirs, mock_copy, mock_get_drive):
    """Testea que se llame a copy2 con la ruta correcta (Manga/Titulo)."""
    fake_drive = os.path.join("mnt", "fake_drive") if os.name == 'posix' else "E:\\"
    fake_file = os.path.join("home", "user", "manga_vol_1.mobi") if os.name == 'posix' else "C:\\manga_vol_1.mobi"
    mock_get_drive.return_value = fake_drive

    result = send_to_usb(fake_file, "Berserk")

    assert result is True
    expected_dest = os.path.join(fake_drive, "documents", "Manga", "Berserk", "manga_vol_1.mobi")
    mock_copy.assert_called_once_with(fake_file, expected_dest)

@patch("md2kindle.services.delivery.usb.get_kindle_drive")
@patch("md2kindle.services.delivery.usb.mass_storage.shutil_copy2")
@patch("md2kindle.services.delivery.usb.mass_storage.os.makedirs")
def test_send_batch_to_usb_success(mock_makedirs, mock_copy, mock_get_drive):
    """Testea el envío de múltiples archivos en una sola llamada."""
    fake_drive = "E:\\" if os.name == 'nt' else "/mnt/kindle"
    fake_files = ["vol1.mobi", "vol2.mobi"]
    mock_get_drive.return_value = fake_drive

    result = send_to_usb(fake_files, "Berserk")

    assert result is True
    assert mock_copy.call_count == 2
