import os
import pytest
from unittest.mock import patch, MagicMock
from md2kindle.app.pipeline import sync_usb
from md2kindle.core.config import AppConfig

@patch("md2kindle.app.pipeline.os.path.exists")
@patch("md2kindle.app.pipeline.os.walk")
@patch("md2kindle.services.delivery.usb.send_to_usb")
def test_sync_usb_discovers_and_sends_files(mock_send, mock_walk, mock_exists):
    """Testea que sync_usb encuentre archivos .mobi y los envíe."""
    # Simular una estructura de archivos
    # out_kcc/Berserk/Berserk - Vol 1.mobi
    # out_kcc/Berserk/Berserk - Vol 2.mobi
    # out_kcc/Other/other.txt (debería ignorarse)
    
    # Usar el objeto global si es necesario o uno mockeado correctamente
    from md2kindle.core.config.binaries import BinaryPaths
    app_config = AppConfig(
        root_dir=".",
        binaries=BinaryPaths(mangadex_dl="md", kcc_c2e="kcc", ffsend="ff"),
        output_folder_kcc="out_kcc",
        output_folder_manga="out_manga"
    )
    
    mock_exists.return_value = True
    mock_walk.return_value = [
        ("out_kcc", ["Berserk", "Other"], []),
        (os.path.join("out_kcc", "Berserk"), [], ["Berserk - Vol 1.mobi", "Berserk - Vol 2.mobi"]),
        (os.path.join("out_kcc", "Other"), [], ["other.txt"]),
    ]
    
    mock_send.return_value = True
    
    processed_count = sync_usb(app_config=app_config)
    
    assert processed_count == 2
    assert mock_send.call_count == 1
    
    # Verificar que se llamó con el lote de Berserk
    call_args = mock_send.call_args
    files_sent = call_args[0][0]
    manga_title = call_args[0][1]
    
    assert manga_title == "Berserk"
    assert len(files_sent) == 2
    assert os.path.join("out_kcc", "Berserk", "Berserk - Vol 1.mobi") in files_sent
    assert os.path.join("out_kcc", "Berserk", "Berserk - Vol 2.mobi") in files_sent
