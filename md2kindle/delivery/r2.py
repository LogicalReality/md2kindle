"""Compatibility shim for `md2kindle.services.delivery.r2`."""

from importlib import import_module
import sys

_shim_name = __name__
_module = import_module("md2kindle.services.delivery.r2")
sys.modules[_shim_name] = _module
globals().update(_module.__dict__)
