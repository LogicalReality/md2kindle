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

> [!NOTE]
> Este mapa es una referencia rápida. Para una explicación profunda de las capas y el flujo de datos, consultá [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```text
md2kindle.py          # Entrypoint (thin wrapper)
md2kindle/
├── app/
│   ├── cli.py        # argparse + interactive mode → PipelineContext → pipeline.run()
│   ├── context.py    # shared helpers (config_kwargs)
│   ├── pipeline.py   # orchestrates: download → audit → convert → deliver
│   └── workflows/
│       ├── volume.py  # volume processing flow
│       └── chapter.py # chapter/range processing flow
├── core/
│   ├── config/
│   │   ├── settings.py  # AppConfig dataclass, .env loading, constants
│   │   └── binaries.py  # binary resolution: bin/ folder → system PATH → venv
│   ├── models/
│   │   └── pipeline.py  # PipelineContext, MangaContext, DownloadRange, DeliveryOptions
│   ├── exceptions/      # hierarchy: Md2KindleError → Config/Download/Conversion/DeliveryError
│   ├── logging/
│   │   └── setup.py     # centralized logging (--silent = WARNING level)
│   └── ports.py         # Protocols: Converter, Deliverer (DI interfaces)
├── services/
│   ├── converter/
│   │   └── engine.py    # CBZ → MOBI via kcc_c2e subprocess
│   ├── mangadex/
│   │   ├── client.py       # MangaDex HTTP client
│   │   ├── parser.py       # API response parsing
│   │   ├── resolver.py     # title/UUID resolution
│   │   ├── downloader.py   # mangadex-dl CLI wrapper
│   │   ├── audit.py        # post-download integrity audit & orphan cleanup
│   │   └── mixed_download.py # multi-language download orchestration + CBZ packing
│   └── delivery/
│       ├── manager.py   # orchestration: USB → R2 → Telegram → interactive fallback
│       ├── telegram.py  # Telegram Bot API (direct upload or ffsend for >45MB)
│       ├── r2.py        # Cloudflare R2 via boto3 (presigned URLs, 7-day expiry)
│       ├── usb/         # cross-platform Kindle delivery package
│       │   ├── __init__.py  # facade & orchestration
│       │   ├── discovery.py # multi-OS device detection
│       │   ├── mass_storage.py # standard copy logic
│       │   └── mtp.py       # Windows MTP bridge & interactive sync
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
- **Protocols**: `Converter` and `Deliverer` define DI interfaces in `core/ports.py`.

### Delivery fallback order

Telegram delivery uses the following strategy:

1. **Direct**: If file < 45MB, send directly through Telegram Bot API.
2. **Cloudflare R2**: If file > 45MB and R2 is configured, upload to S3 and send link.
3. **ffsend**: If file > 45MB and R2 is NOT configured, use `ffsend` (E2EE) as zero-config fallback.

`ffsend` is not a replacement for R2; it is a safety net for large files in zero-config environments.

## Environment

- [ ] **Python**: 3.13 installed.
- [ ] **External Binaries**: `mangadex-dl`, `kcc_c2e`, `ffsend` (fallback for large files) placed in `bin/` or PATH.
- [ ] **Environment**: `.env` populated for cloud features.
- [ ] **Verification**: Run `python -m pytest -q`. Expected: all tests pass.

## Testing & Troubleshooting

- **Pathing**: Always use `.venv\Scripts\python.exe -m pytest` (not bare `pytest`) to avoid local package resolution issues.
- **USB Mocking**: `os.name` is mocked to `"nt"` in tests to support cross-platform CI verification.
- **CLI URL**: Both positional `url` and `--url` flag are supported. The GitHub Actions workflow uses the flag for robustness.
- **Delivery Logic**: USB is always attempted first (opportunistic auto-copy). Cloud flags (`--r2`, `--telegram`) act as additional, explicit delivery paths.
- **CI Logic**: `CI=true` suppresses KCC's noisy stderr and optimizes for non-interactive runs.

## Cloud & Integration

- **GitHub Actions**: `.github/workflows/manga-pipeline.yml` handles manual/cron dispatch.
- **Telegram Bot**: Cloudflare Worker (`.github/workers/telegram-bot.js`) triggers CI via REST.

## Non-goals

- **GUI Implementation**: The project is strictly CLI/headless-first.
- **Direct Image Processing**: All conversion logic is delegated to KCC; we do not manipulate individual images.
- **Multi-Source Support**: We only support MangaDex as the source.
