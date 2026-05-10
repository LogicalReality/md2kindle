import pytest
from unittest.mock import patch, MagicMock
from md2kindle.core.config import AppConfig
from md2kindle.services.delivery.telegram import send_message
from md2kindle.services.delivery.r2 import send_to_r2
from md2kindle.services.delivery.d1 import log_download

def test_telegram_uses_provided_config():
    """Verifica que Telegram use el token del AppConfig inyectado."""
    custom_config = AppConfig(
        root_dir=".",
        binaries=MagicMock(),
        output_folder_manga=".",
        output_folder_kcc=".",
        telegram_bot_token="custom-token",
        telegram_chat_id="custom-chat-id"
    )
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_message("test", app_config=custom_config)
        
        # Debe llamar al URL con el token custom
        args, kwargs = mock_post.call_args
        assert "botcustom-token" in args[0]
        assert kwargs["data"]["chat_id"] == "custom-chat-id"

def test_r2_uses_provided_config():
    """Verifica que R2 use las credenciales del AppConfig inyectado."""
    custom_config = AppConfig(
        root_dir=".",
        binaries=MagicMock(),
        output_folder_manga=".",
        output_folder_kcc=".",
        r2_account_id="custom-acc",
        r2_access_key_id="custom-key",
        r2_secret_access_key="custom-secret",
        r2_bucket_name="custom-bucket"
    )
    
    with patch("boto3.client") as mock_boto:
        # Mocking the client and the exists check
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        with patch("os.path.exists", return_value=True):
            send_to_r2("test.mobi", "Manga", "Vol1", app_config=custom_config)
            
            # Verificamos que se inicializó con la URL y llaves custom
            mock_boto.assert_called_once()
            _, kwargs = mock_boto.call_args
            assert "custom-acc" in kwargs["endpoint_url"]
            assert kwargs["aws_access_key_id"] == "custom-key"

def test_d1_uses_provided_config():
    """Verifica que D1 use las credenciales del AppConfig inyectado."""
    custom_config = AppConfig(
        root_dir=".",
        binaries=MagicMock(),
        output_folder_manga=".",
        output_folder_kcc=".",
        d1_account_id="custom-acc",
        d1_database_id="custom-db",
        d1_api_token="custom-token"
    )
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        
        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=1024):
            log_download("Manga", "Vol1", "es", "test.mobi", "usb", app_config=custom_config)
            
            # Verificamos que se llamó al endpoint custom
            args, _ = mock_post.call_args
            assert "custom-acc" in args[0]
            assert "custom-db" in args[0]
