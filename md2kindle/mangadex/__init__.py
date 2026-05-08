"""Compatibility package for `md2kindle.services.mangadex`."""

import sys

from md2kindle.services import mangadex as _mangadex
from md2kindle.services.mangadex import api, downloader
from md2kindle.services.mangadex import *

sys.modules[__name__ + ".api"] = api
sys.modules[__name__ + ".downloader"] = downloader
