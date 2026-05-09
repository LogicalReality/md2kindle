# AGENTS.md

## Project Essence

Python-based automation pipeline that fetches manga from MangaDex, processes it for Kindle via KCC, and delivers it through multiple channels (USB, Telegram, Cloudflare R2).

## Quick Reference

| Action | Command |
| :--- | :--- |
| **Setup Dev** | `pip install -e .[dev]` |
| **Run Tests** | `.venv\Scripts\python.exe -m pytest -v` |
| **CLI Help** | `python md2kindle.py --help` |
| **Run Pipeline** | `python md2kindle.py <URL> [OPTIONS]` |
| **Launcher** | `run.bat` (Windows interactive) |

## Architecture Overview

```text
md2kindle.py          # Entrypoint (thin wrapper)
md2kindle/
├── app/
│   ├── cli.py        # argparse + interactive mode → PipelineParams → pipeline.run()
│   └── pipeline.py   # orchestrates: download → audit → convert → deliver
├── core/
│   ├── config/
│   │   ├── settings.py  # AppConfig dataclass, .env loading, constants
│   │   └── binaries.py  # binary resolution: bin/ folder → system PATH → venv
│   ├── models/
│   │   └── pipeline.py  # PipelineParams, format_manga_title()
│   └── logging/
│       └── setup.py     # centralized logging (--silent = WARNING level)
├── services/
│   ├── converter/
│   │   └── service.py   # CBZ → MOBI via kcc_c2e subprocess
│   ├── mangadex/
│   │   ├── api.py       # MangaDex REST API calls (title lookup, aggregate structure)
│   │   └── downloader.py # mangadex-dl subprocess, audit_and_cleanup, mixed-lang download
│   └── delivery/
│       ├── service.py   # orchestration: USB → R2 → Telegram → interactive fallback
│       ├── telegram.py  # Telegram Bot API (direct upload or ffsend for >45MB)
│       ├── r2.py        # Cloudflare R2 via boto3 (presigned URLs, 7-day expiry)
│       ├── usb.py       # Kindle USB detection (Windows: MTP + mass storage)
│       ├── ffsend.py    # E2EE upload via ffsend binary (send.vis.ee)
│       └── d1.py        # optional download history logging to Cloudflare D1
└── utils/
    └── ranges.py        # volume/chapter range parsing (supports decimals, alphanumerics)
```

## Key Conventions

- **Centralized Config**: Use `AppConfig` in `md2kindle/core/config/settings.py`. Do not hardcode values.
- **Binary Discovery**: Cascade order: `./bin/` → System PATH → Venv. Windows prefers `.exe`.
- **Granular Fallback**: Language priority: `es-la` → `en` → `es` (evaluated per-chapter).
- **KCC Defaults**: Profile `KO` (Oasis/Paperwhite), Format `MOBI` (Dual mode).
- **Idempotency**: Skips download if `.cbz` exists; skips conversion if `.mobi` exists.

## Environment

- [ ] **Python**: 3.13 installed.
- [ ] **External Binaries**: `mangadex-dl`, `kcc_c2e`, `ffsend` placed in `bin/` or PATH.
- [ ] **Environment**: `.env` populated for cloud features.
- [ ] **Verification**: Run `pytest` (Expect 29 tests passing).

## Testing & Troubleshooting

- **Pathing**: Always use `.venv\Scripts\python.exe -m pytest` (not bare `pytest`) to avoid local package resolution issues.
- **USB Mocking**: `os.name` is mocked to `"nt"` in tests to support cross-platform CI verification (29 tests should pass).
- **CI Logic**: `CI=true` suppresses KCC's noisy stderr and optimizes for non-interactive runs.

## Cloud & Integration

- **GitHub Actions**: `.github/workflows/manga-pipeline.yml` handles manual/cron dispatch.
- **Telegram Bot**: Cloudflare Worker (`.github/workers/telegram-bot.js`) triggers CI via REST.
