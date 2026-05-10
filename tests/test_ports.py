import pytest
from typing import Protocol, runtime_checkable

def test_ports_existence():
    """Test that ports module and protocols exist."""
    from md2kindle.core.ports import Converter, Deliverer
    assert issubclass(Converter, Protocol)
    assert issubclass(Deliverer, Protocol)

def test_protocols_runtime_checkable():
    """Test that classes satisfying the signature are recognized."""
    from md2kindle.core.ports import Converter, Deliverer
    
    class MockConverter:
        def convert(self, target_path, author, title, vol_hint=None):
            return []
            
    class MockDeliverer:
        def deliver(self, files, context):
            pass
            
    assert isinstance(MockConverter(), Converter)
    assert isinstance(MockDeliverer(), Deliverer)
