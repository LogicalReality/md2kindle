"""Compatibility shim for `md2kindle.services.converter.service`."""

from importlib import import_module
import sys

_shim_name = __name__
_module = import_module("md2kindle.services.converter.service")
sys.modules[_shim_name] = _module
globals().update(_module.__dict__)
