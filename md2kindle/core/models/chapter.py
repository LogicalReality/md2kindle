from dataclasses import dataclass

@dataclass
class DownloadRange:
    mode: str  # "v" (volumen) | "c" (capítulo)
    start: str
    end: str
    skip_oneshots: bool
