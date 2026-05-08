# AGENTS.md

## Project

Python CLI that downloads manga from MangaDex, converts to Kindle formats (.mobi/.azw3) via KCC, and delivers via USB/Telegram/Cloudflare R2.

## Quick Reference

```bash
pip install -e .[dev]                  # install with dev deps
.venv\Scripts\python.exe -m pytest -v  # run tests (use venv directly)
python md2kindle.py --help             # CLI help
python md2kindle.py <URL> [OPTIONS]    # run pipeline
run.bat                                # Windows interactive launcher
```

## Architecture

```text
md2kindle.py          # thin entrypoint → md2kindle.app.cli:main
md2kindle/
  app/
    cli.py            # argparse + interactive mode → PipelineParams → pipeline.run()
    pipeline.py       # orchestrates: download → audit → convert → deliver
  core/
    config/
      settings.py     # AppConfig dataclass, .env loading, constants
      binaries.py     # binary resolution: bin/ folder → system PATH → venv
    models/
      pipeline.py     # PipelineParams, format_manga_title()
    logging/
      setup.py        # centralized logging (--silent = WARNING level)
  services/
    converter/
      service.py      # CBZ → MOBI via kcc_c2e subprocess
    mangadex/
      api.py          # MangaDex REST API calls (title lookup, aggregate structure)
      downloader.py   # mangadex-dl subprocess, audit_and_cleanup, mixed-lang download
    delivery/
      service.py      # delivery orchestration: USB → R2 → Telegram → interactive fallback
      telegram.py     # Telegram Bot API (direct upload or ffsend for >45MB)
      r2.py           # Cloudflare R2 via boto3 (presigned URLs, 7-day expiry)
      usb.py          # Kindle USB detection (Windows only: MTP + mass storage)
      ffsend.py       # E2EE upload via ffsend binary (send.vis.ee)
      d1.py           # optional download history logging to Cloudflare D1
  utils/
    ranges.py         # volume/chapter range parsing (supports decimals, alphanumerics)
```

## Key Conventions

- **Config centralization**: all settings in `md2kindle/core/config/settings.py` via `AppConfig`. Never hardcode paths or values.
- **Binary detection**: cascading `./bin/` → system PATH → venv. On Windows, prefers local `.exe` files.
- **Language fallback**: `es-la` → `en` → `es` (per-chapter granularity in volume mode).
- **KCC profile**: `KO` (Kindle Oasis 2/3 / Paperwhite 12), format `MOBI` (dual MOBI/AZW3).
- **Idempotent pipeline**: skips download if `.cbz` exists, skips conversion if `.mobi` exists.

## Testing Quirks

- Always use `.venv\Scripts\python.exe -m pytest` (not bare `pytest`) to avoid PATH issues.
- USB tests mock `os.name` to `"nt"` since CI may run on Linux.
- Expected: 29 tests passing.

## Environment

- Python 3.12+ required.
- External binaries needed in `bin/`: `mangadex-dl`, `kcc_c2e`, `ffsend` (optional).
- **Kindle Previewer** must be installed and opened once for KCC `.mobi` generation.
- `.env` for secrets: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `CLOUDFLARE_ACCOUNT_ID`, `R2_*`, `D1_*`.
- CI detection: `CI=true` or `GITHUB_ACTIONS=true` → suppresses KCC stderr, adjusts behavior.

## Cloud Components

- **GitHub Actions**: `.github/workflows/manga-pipeline.yml` — manual dispatch, installs kindlegen + ffsend + KCC from source.
- **Telegram Bot**: `.github/workers/telegram-bot.js` — Cloudflare Worker that triggers GitHub Actions workflow via `/manga` command.
