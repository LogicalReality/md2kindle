# md2kindle - Copilot Instructions

## Project Overview

Python automation script that downloads manga from MangaDex and converts to Kindle format using `mangadex-dl` and `kcc_c2e`.

**Main file**: `md2kindle.py`

---

## Build & Test Commands

```bash
# Run the main script
python md2kindle.py

# Or via batch file
.\Iniciar_Manga_To_Kindle.bat
```

---

## Architecture

| Component | Purpose |
|-----------|---------|
| `md2kindle.py` | Main script - orchestrates download → conversion pipeline |
| `mangadex-dl.exe` | Downloads manga chapters/volumes from MangaDex |
| `kcc_c2e.exe` | Converts CBZ to MOBI/AZW3 for Kindle |

### Key Functions in `md2kindle.py`

| Function | Purpose |
|----------|---------|
| `clear_screen()` | Cross-platform screen clear |
| `sanitize_filename()` | Remove invalid Windows filename chars |
| `get_manga_title_options()` | Query MangaDex API for titles and author |
| `convert_with_kcc()` | Convert CBZ files using KCC with metadata |
| `download_manga()` | Main download flow with orphan cleanup |
| `main()` | Interactive CLI workflow |

---

## Configuration

All config is in the top of `md2kindle.py`:

```python
MANGADEX_DL_PATH = r"C:\mangadex-dl\mangadex-dl.exe"
KCC_C2E_PATH = r"C:\Antigravity\md2kindle\kcc_c2e_9.6.2.exe"
OUTPUT_FOLDER_MANGA = r"C:\Manga"
OUTPUT_FOLDER_KCC = r"C:\KCC Output"
KCC_PROFILE = "KO"        # Kindle Oasis 2/3 / Paperwhite 12
KCC_FORMAT = "MOBI"       # Hybrid MOBI/AZW3 output
KCC_CUSTOM_ARGS = ["-m", "-r", "1", "-u"]
DEFAULT_LANGUAGE = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE = True
DELETE_CBZ_AFTER_CONVERSION = False
```

### KCC Flags

| Flag | Meaning |
|------|---------|
| `-m` | Manga mode (RTL reading) |
| `-r 1` | Rotate spreads |
| `-u` | Upscale low-res images |
| `-p KO` | Profile for Kindle Oasis/Paperwhite 12 |

---

## Important Patterns

### Command Construction
Commands for `subprocess` must be built **sequentially** — avoid inserting at absolute indexes. Use `subprocess.list2cmdline(cmd)` for logging.

### Orphan Cleanup Regex
```python
vol_pattern = re.compile(rf"vol\.?\s*0*{vol}\b", re.IGNORECASE)
```
Matches `Vol. 27`, `vol. 027`, `VOL 27` etc.

### API Calls
Use `urllib.request` for lightweight API calls (no heavy dependencies).

### Folder Mirroring
KCC output preserves source folder structure under `OUTPUT_FOLDER_KCC`.

---

## Potential Pitfalls

1. **Argument separation bug**: Adding flags conditionally must preserve flag-value pairs — build commands sequentially
2. **Orphan chapters**: Use regex pattern to distinguish `Vol. 27` from `Vol. 271`
3. **Language codes**: Always specify `--language es-la` or similar, otherwise `mangadex-dl` downloads all languages
4. **Kindlegen dependency**: KCC needs Kindle Previewer installed for MOBI/AZW3 output

---

## Documentation

- [README.md](../README.md) - User-facing documentation and setup guide
- [MEMORIA.md](../MEMORIA.md) - Development history and decisions
- [TO-DO-list.md](../TO-DO-list.md) - Pending tasks
- [AI_CONTEXT.md](../AI_CONTEXT.md) - Technical context for AI agents

---

## File Patterns

```
*.py          → Python source
*.bat         → Windows batch scripts
*.md          → Documentation
*.cbz         → Downloaded manga archives (input to KCC)
*.mobi, *.azw3 → Kindle output files
```
