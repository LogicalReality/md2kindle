"""Compatibility package for `md2kindle.services.delivery`."""

import sys

from md2kindle.services import delivery as _delivery
from md2kindle.services.delivery import d1, ffsend, r2, service, telegram, usb
from md2kindle.services.delivery import *

sys.modules[__name__ + ".d1"] = d1
sys.modules[__name__ + ".ffsend"] = ffsend
sys.modules[__name__ + ".r2"] = r2
sys.modules[__name__ + ".service"] = service
sys.modules[__name__ + ".telegram"] = telegram
sys.modules[__name__ + ".usb"] = usb
