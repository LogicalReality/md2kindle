# 📖 md2kindle (MangaDex to Kindle)

**English** | [🌐 Español](README.es.md)

An automation pipeline to download manga from [MangaDex](https://mangadex.org) and convert it into Kindle-optimized formats (`.mobi`/`.azw3`) using [KCC](https://github.com/ciromattia/kcc). Designed to run locally or in the cloud via GitHub Actions, with a Telegram bot for added convenience.

---

## 🚀 Quick Start

Get your first manga on your Kindle in 3 steps:

1. **Install Prerequisites**: [Python 3.13](https://www.python.org/downloads/) and download [kcc_c2e](https://github.com/ciromattia/kcc/releases), [mangadex-dl](https://github.com/mansuf/mangadex-downloader/releases), and [ffsend](https://github.com/timvisee/ffsend/releases) binaries into the `bin/` folder (you must create it manually at the project root).
2. **Setup Environment**:

   ```bash
   git clone https://github.com/LogicalReality/md2kindle.git
   cd md2kindle
   pip install -e .
   ```

3. **Run your first download**:
   You can run the interactive assistant by simply executing `run.bat` (Windows) or via Python:

   ```bash
   python md2kindle.py
   ```

---

## ✨ Why use this?

| Feature | Benefit |
| :--- | :--- |
| **Intelligent Fallback** | Automatically tries `es-la` > `es` > `en` per chapter. |
| **Kindle Optimized** | RTL reading, upscaling, and double-page spread rotation. |
| **Delivery Freedom** | Direct Telegram (under 50MB) or high-speed Cloudflare R2 links. |
| **Zero Maintenance** | Detects binaries automatically in `./bin/` or System PATH. |
| **Cloud Native** | Run it via GitHub Actions or trigger it from Telegram. |

---

## 🛠️ Requirements & Setup

### 1. Binaries Priority Table

The script searches for tools in this order. **No configuration required.**

| Priority | Location | Recommendation |
| :--- | :--- | :--- |
| **1st** | `./bin/` | Put `mangadex-dl.exe`, `kcc_c2e.exe`, and `ffsend.exe` here. |
| **2nd** | System PATH | Install tools globally for access from anywhere. |
| **3rd** | Python venv | If you installed `mangadex-downloader` via pip. |

> [!IMPORTANT]
> **Kindle Previewer** must be installed and opened at least once on your system for KCC to generate `.mobi` files correctly.

### 2. Environment Configuration (`.env`)

Create a `.env` file for automated delivery (Telegram/Cloudflare):

```env
# Telegram
TELEGRAM_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_id_here

# Cloudflare (R2 Storage)
CLOUDFLARE_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your_bucket_name

# Cloudflare (D1 History - Optional)
D1_DATABASE_ID=your_database_id
D1_API_TOKEN=your_api_token
```

---

## 🏃 Usage Guide

### CLI Cheat Sheet

```bash
python md2kindle.py <URL> [OPTIONS]
```

| Argument | Flag | Example |
| :--- | :--- | :--- |
| **URL** | (First arg) | `https://mangadex.org/title/...` |
| **Mode** | `--mode` | `v` (volume) or `c` (chapter) |
| **Range** | `--start`, `--end` | `--start 1 --end 5` |
| **Language** | `--lang` | `--lang es-la` |
| **Telegram** | `--telegram` | Direct delivery via direct upload or ffsend |
| **Cloud R2** | `--r2` | Upload to Cloudflare and send link to Telegram bot |
| **Silent** | `--silent` | Minimize log output |

---

## ☁️ Cloud Automation

### GitHub Actions

1. **Fork** this repo.
2. **Add Secrets**: Go to `Settings > Secrets > Actions` and add your `.env` variables.
3. **Run**: Use the `Actions` tab to trigger the **Manga Pipeline** manually.

### Telegram Bot (Serverless)

Trigger downloads by chatting with your bot:

1. Deploy the Cloudflare Worker in `.github/workers/telegram-bot.js`.
2. Send: `/manga <url> v 1 5 es-la`

---

## 🧪 Development & Verification

### Local Verification

- [ ] `pip install -e .[dev]`
- [ ] `.venv\Scripts\python.exe -m pytest -v` (Should be 27/27 PASS)
- [ ] `python md2kindle.py --help`

---

## 💡 Troubleshooting

- **Telegram file too big?** Use the `--r2` flag for Cloudflare delivery.
