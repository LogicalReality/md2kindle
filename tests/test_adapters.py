import pytest
from md2kindle.services.converter.engine import KccConverter
from md2kindle.core.ports import Converter

def test_kcc_converter_implements_protocol():
    """Test that KccConverter satisfies the Converter Protocol."""
    converter = KccConverter()
    assert isinstance(converter, Converter)

def test_kcc_converter_delegation():
    """Test that KccConverter delegates to convert_with_kcc."""
    from unittest.mock import patch
    with patch("md2kindle.services.converter.engine.convert_with_kcc") as mock_convert:
        mock_convert.return_value = ["file.mobi"]
        
        converter = KccConverter()
        result = converter.convert("path", "author", "title", "vol")
        
        mock_convert.assert_called_once_with(
            target_path="path", author="author", title="title", vol_hint="vol", app_config=converter._config
        )
        assert result == ["file.mobi"]

def test_delivery_manager_implements_protocol():
    """Test that DeliveryManager satisfies the Deliverer Protocol."""
    from md2kindle.services.delivery.manager import DeliveryManager
    from md2kindle.core.ports import Deliverer
    
    manager = DeliveryManager()
    assert isinstance(manager, Deliverer)

def test_delivery_manager_delegation():
    """Test that DeliveryManager delegates to deliver_files."""
    from md2kindle.services.delivery.manager import DeliveryManager
    from unittest.mock import patch, Mock
    with patch("md2kindle.services.delivery.manager.deliver_files") as mock_deliver:
        manager = DeliveryManager()
        mock_files = ["a.mobi"]
        mock_ctx = Mock()
        
        manager.deliver(mock_files, mock_ctx)
        
        mock_deliver.assert_called_once_with(mobi_files=mock_files, params=mock_ctx, app_config=manager._config)
