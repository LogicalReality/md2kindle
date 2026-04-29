# 📖 md2kindle (MangaDex to Kindle)

**English** | [🌐 Español](README.es.md)

A Python automation script that simplifies downloading manga from [MangaDex](https://mangadex.org) and automatically converting it to Kindle-optimized formats using [KCC (Kindle Comic Converter)](https://github.com/ciromattia/kcc).

---

## 🚀 Key Features

- **Smooth Downloads**: Download complete volumes or individual chapters, one at a time or in bulk (ranges).
- **Automatic Conversion**: Detects resulting `.cbz` files and launches conversion with minimal manual intervention.
- **🛡️ E2EE Delivery (Zero Trace)**: Heavy files (>45MB) are locally encrypted and a one-time-use link (1 download / 1 hour) is generated via `ffsend`. Total privacy guaranteed.
- **🔗 Telegram Integration**: Receive your converted manga (or encrypted links) directly on your phone or Telegram app to send to your e-reader.
- **☁️ GitHub Actions (Cloud)**: No PC needed! Trigger the download and conversion from the GitHub web interface and receive the result in minutes.
- **🤖 Interactive Telegram Bot**: Trigger the workflow directly from Telegram with a command — no GitHub UI needed, no extra configuration.
- **⚡ Processing Efficiency**: Intelligent detection of existing `.mobi` files to skip unnecessary downloads and conversions.
- **Kindle-Ready**: MOBI/AZW3 format with RTL reading, advanced scaling, and double-page spread joining.

---

## 🛠️ Prerequisites

Make sure the following tools are installed in your environment (Windows):

1. **[Python 3.x](https://www.python.org/downloads/)**: The interpreter required to run the script.
2. **[mangadex-dl](https://github.com/mansuf/mangadex-downloader/releases)**: Engine for manga extraction. (`mangadex-dl.exe`).
3. **[Kindle Comic Converter (KCC)](https://github.com/ciromattia/kcc/releases)**: Requires the specialized `kcc_c2e.exe` executable.
4. **[Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011)**: Used by KCC to generate `.mobi` files.
5. **[ffsend](https://github.com/timvisee/ffsend/releases)**: Required for E2EE encrypted delivery of heavy files.

---

## 🖥️ Local Setup — Step by Step

Follow these steps to get your environment ready to run on your machine.

### 1. Install Python 3.x

Download and install Python from [python.org](https://www.python.org/downloads/). During installation, check the **"Add Python to PATH"** option.

### 2. Download mangadex-dl

1. Go to [mansuf/mangadex-downloader/releases](https://github.com/mansuf/mangadex-downloader/releases).
2. Download the Windows binary (`mangadex-dl.exe`).
3. Create a folder at `C:\mangadex-dl\` and place the executable there.

### 3. Install Kindle Previewer (Kindlegen)

1. Download **Kindle Previewer** from [amazon.com/Kindle-Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011).
2. Install it and open it **at least once** so it registers its internal binaries.
3. KCC will detect it automatically.

> [!NOTE]
> Without Kindle Previewer, KCC will fail at the final conversion step with an error about `kindlegen`.

### 4. [Optional] Download ffsend for Encrypted Delivery

If you plan to use the Telegram feature with heavy files (+45MB), you need `ffsend`:

1. Go to [timvisee/ffsend/releases](https://github.com/timvisee/ffsend/releases).
2. Download the Windows binary.
3. Place it in the project folder or add it to the system PATH.

> [!TIP]
> If you don't use Telegram or only send small files, you can skip this step.

### 5. Clone or Download the Repository

```bash
git clone https://github.com/LogicalReality/md2kindle.git
cd md2kindle
```

### 6. Install Python Dependencies

```bash
pip install -e .
```

This will install `requests` and register the `md2kindle` command in your environment using `pyproject.toml`.

> [!NOTE]
> If you prefer the standalone binary (`mangadex-dl.exe`), download it from
> [mansuf/mangadex-downloader/releases](https://github.com/mansuf/mangadex-downloader/releases)
> and place it inside `mangadex-dl/` at the project root. The script will detect it automatically.

### 7. Place Binaries (Auto-Detection)

The script detects tools in a **cascade**, with no code editing required:

| Priority | Location searched |
| :--- | :--- |
| **1st** | Project folder: `./bin/` (e.g. `./bin/ffsend.exe`) |
| **2nd** | Tool specific folders: `./bin/mangadex-dl/mangadex-dl.exe` |
| **3rd** | Project root (Legacy/Portable) |
| **4th** | System PATH (`mangadex-dl`, `kcc-c2e` installed globally) |

**Professional Structure** — Recommended organization for binaries:

```text
md2kindle/
├── bin/
│   ├── mangadex-dl/
│   │   └── mangadex-dl.exe
│   ├── kcc_c2e_9.6.2.exe
│   └── ffsend.exe
├── md2kindle/            # Package Source
│   ├── cli.py            # Argument parsing
│   ├── pipeline.py       # Flow orchestration
│   ├── models.py         # Typed data contracts
│   ├── config.py         # Path & tool configuration
│   ├── mangadex/         # MangaDex API + Downloader
│   └── delivery/         # Telegram + ffsend
├── md2kindle.py          # Local entry point (wrapper)
└── pyproject.toml        # Package definition
```

> [!TIP]
> If you installed `mangadex-downloader` via pip, you don't need the binary.
> The script will find it in the PATH automatically.

### 8. [Optional] Configure Telegram Environment Variables

The script automatically detects if the `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` variables are available. You have three ways to configure them:

#### Option A: `.env` file (Recommended for local development)

1. Create a `.env` file in the project root:

   ```env
   TELEGRAM_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

2. To load them automatically, use a wrapper or configure your IDE/terminal.

> [!WARNING]
> **Never push the `.env` file to GitHub.** It's already ignored by `.gitignore`,
> but verify it's not tracked before committing.

#### Option B: System Variables (Windows CMD)

```cmd
set TELEGRAM_TOKEN=your_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
python md2kindle.py --url "..." --telegram
```

#### Option C: PowerShell

```powershell
$env:TELEGRAM_TOKEN="your_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
python md2kindle.py --url "..." --telegram
```

---

## ⚙️ Configuration

All central configuration lives in `md2kindle/config.py`. The default values work without modification in most cases:

```python
# ==========================================
# CONFIGURATION  (md2kindle/config.py)
# ==========================================

# Output folders — Relative to the project
OUTPUT_FOLDER_MANGA = "./downloads"   # Downloaded CBZ files
OUTPUT_FOLDER_KCC   = "./output"      # Converted MOBI/AZW3 files

# KCC settings
KCC_PROFILE     = "KO"               # KO = Kindle Oasis / Paperwhite 12
KCC_FORMAT      = "MOBI"             # Dual MOBI/AZW3 format
KCC_CUSTOM_ARGS = ["-m", "-r", "1", "-u"]

# General behavior
DELETE_CBZ_AFTER_CONVERSION   = False
DEFAULT_LANGUAGE               = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE   = True
```

## 🛠️ Advanced Configuration Guide

### 1. Kindle Comic Converter (KCC) - `kcc-c2e`

These settings define the quality and format of the final file your Kindle will read.

- `KCC_PROFILE`: Determines output resolution. `KO` is ideal for Kindle Oasis/Paperwhite 12.
- `KCC_FORMAT`: Final file format (`MOBI`, `AZW3`, `KFX`, `EPUB`).

#### KCC Custom Arguments (`KCC_CUSTOM_ARGS`)

Use these flags inside the list (e.g., `["-m", "-u"]`).

| Flag | Description | Recommendation |
| :--- | :--- | :--- |
| `-m` | **Manga Mode**: Enables Right-to-Left (RTL) reading. | **On** |
| `-r 1` | **Rotate Spreads**: Detects double-page spreads and rotates them 90°. | **On** |
| `-u` | **Upscale**: Scales small images to fill the screen. | **On** |
| `-w` | **Webtoon**: Processes files as infinite vertical strips. | **On** (Webtoons only) |
| `-c` | **Color**: Disables grayscale conversion. | **On** (Kindle Color) |
| `-q` | **Quality**: High-quality resizing algorithm. | **On** |

### 2. MangaDex Downloader

Configures how the engine (`mangadex-dl`) searches and filters chapters on the servers.

- **`SKIP_ONESHOTS_ON_VOLUME_MODE`**:
  - `True`: (Recommended) Ignores "Oneshot" or special chapters.
  - `False`: Includes everything listed.
- **`DEFAULT_LANGUAGE`**: Sets the download language. If a chapter doesn't exist in this language, the script will ask which version to download.

#### Priority Language Codes

| Priority | Code | Language |
| :--- | :---: | :--- |
| **🥇 Primary** | `es-la` | Spanish (Latin America) |
| **🥈 Fallback** | `es` | Spanish (Spain) |
| **🇬🇧 Global** | `en` | English |
| **🇯🇵 Original** | `ja` | Japanese |
| **🇧🇷 Extra** | `pt-br` | Portuguese (Brazil) |

> [!TIP]
> You can see the full list (40+ languages) by running `mangadex-dl --list-languages` in your terminal.

### 3. Script Automation

Internal logic settings for `md2kindle.py`.

- `DELETE_CBZ_AFTER_CONVERSION`:
  - `False`: Keeps the original `.cbz` file.
  - `True`: Automatically deletes the `.cbz` to save disk space.

---

## 🏃 Usage

You can operate this tool in two modes:

### Console Method (Classic)

Open a terminal (CMD or PowerShell), navigate to the project folder and run:

```bash
python md2kindle.py
```

### Interactive Assistant

When started, you'll be prompted with the following questions:

- **MangaDex URL**: Full link to the manga. (e.g., `https://mangadex.org/title/8015...`)
- **Folder name**: Folder where all deliveries will be organized. (e.g., `Berserk`)
- **Language**: Defaults to Latin Spanish (`es-la`). Press Enter to confirm.
- **Volume or Chapter**: Type the letter for the mode you want to download. (`v` or `c`)
- **Download range**: Set start and end numbers (e.g., to download a single volume, answer `25` to both questions).

### CLI Arguments (Advanced)

Pass all parameters directly without going through the interactive assistant:

```bash
python md2kindle.py <URL> [options]
```

| Argument | Description | Example |
| :--- | :--- | :--- |
| `url` | MangaDex manga URL | `https://mangadex.org/title/8015...` |
| `--title` | Output folder name | `--title "Berserk"` |
| `--lang` | Download language | `--lang es-la` |
| `--mode` | `v` (volume) or `c` (chapter) | `--mode v` |
| `--start` | Starting number | `--start 1` |
| `--end` | Ending number (default = `--start`) | `--end 5` |
| `--skip-oneshots` | Skip Oneshot chapters | `--skip-oneshots` |
| `--telegram` | Send result to Telegram | `--telegram` |
| `--silent` | Reduce log verbosity | `--silent` |

**Full example** — Download volumes 1 through 5 in Spanish and send to Telegram:

```bash
python md2kindle.py https://mangadex.org/title/801513ba-a712-498c-8f57-cae55b38cc92 \
  --mode v --start 1 --end 5 --lang es-la \
  --skip-oneshots --telegram
```

> [!NOTE]
> The script automatically detects if the requested language has no available chapters
> and falls back automatically: `es-la → en → es`.

---

## ☁️ GitHub Actions Automation

If you prefer not to keep Python installed on your machine, you can use the GitHub Actions pipeline.

### 1. Push the Repository to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-user/md2kindle.git
git push -u origin main
```

### 2. Configure GitHub Secrets

For the Telegram bot to work, add your credentials:

1. In your GitHub repository, go to **Settings → Secrets and variables → Actions**.
2. Create two secrets:

| Secret             | Value                                     |
| ------------------ | ----------------------------------------- |
| `TELEGRAM_TOKEN`   | Your Telegram bot token                   |
| `TELEGRAM_CHAT_ID` | The chat ID where you'll receive files    |

#### How to get your Telegram credentials

1. **TELEGRAM_TOKEN**:
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram.
   - Send `/newbot` and follow the instructions.
   - BotFather will give you a token like: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`
   - That's your `TELEGRAM_TOKEN`.

2. **TELEGRAM_CHAT_ID**:
   - Talk to [@userinfobot](https://t.me/userinfobot) or [@getidsbot](https://t.me/getidsbot).
   - The bot will reply with your **Chat ID** (e.g., `123456789`).

> [!NOTE]
> If you're the only user, the Chat ID is usually your personal **User ID** (a long number).

### 3. Run the Workflow

1. Go to the **Actions** tab in your repository.
2. Select the workflow: **Manga to Kindle Delivery**.
3. Click **Run workflow** and enter:
   - **MangaDex URL** (e.g., `https://mangadex.org/title/8015...`)
   - **Mode**: `v` (volume) or `c` (chapter)
   - **Start and end volume/chapter number**
   - **Language**: `es-la`, `en`, `es`, etc.
   - **Skip Oneshots**: `true` or `false`
4. Click **Run** and watch the process in real time.

### 4. Receive the File

- If the file is under 45MB, it arrives directly in Telegram.
- If larger, you'll receive an **ephemeral E2EE link** from ffsend (1 download / 1 hour).

> [!TIP]
> **Privacy**: The decryption key travels in the URL fragment (`#`), so not even the ffsend server can see your manga.

---

## 🤖 Telegram Bot — Command Activation

Instead of manually opening GitHub Actions, you can send a message to your Telegram bot and the workflow triggers automatically. This is implemented with a serverless **Cloudflare Worker** (free).

### Architecture

```text
You → /manga <url> → Telegram → Cloudflare Worker → GitHub API → Actions → .mobi → Telegram → You
```

### Prerequisites

- A [Cloudflare](https://cloudflare.com) account (free)
- A Telegram bot created with [@BotFather](https://t.me/BotFather)
- A GitHub Personal Access Token (Classic) with `workflow` scope

### 1. Create the Cloudflare Worker

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create**.
2. Choose **Hello World Worker**, give it a name (e.g., `md2kindle-bot`) and click **Deploy**.
3. Click **Edit code**, clear the content, and paste the code from `.github/workers/telegram-bot.js`.
4. Click **Deploy**.

### 2. Configure Worker Secrets

In your Worker → **Settings** → **Variables and Secrets** → **Add**:

| Secret | Value |
| --- | --- |
| `TELEGRAM_TOKEN` | Your bot token (BotFather) |
| `TELEGRAM_CHAT_ID` | Your personal Chat ID (get it from [@userinfobot](https://t.me/userinfobot)) |
| `GITHUB_PAT` | GitHub Classic Token with `workflow` scope |

> [!WARNING]
> Use a **Classic Token**, not Fine-grained. Fine-grained tokens return 403 on the `workflow_dispatch` endpoint unless you explicitly configure per-repository permissions.

### 3. Create the GitHub PAT

1. Go to [github.com/settings/tokens/new](https://github.com/settings/tokens/new) (Classic).
2. Check only the scope: ✅ `workflow`.
3. Generate the token and paste it into the `GITHUB_PAT` secret.

### 4. Register the Telegram Webhook (one time only)

Open this URL in your browser (replace `<YOUR_TOKEN>` and `<YOUR_WORKER_URL>`):

```text
https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=<YOUR_WORKER_URL>
```

If everything is correct you'll see:

```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Usage

```text
/manga <url> <mode> <start> [end] [lang]
```

| Parameter | Description | Default |
| --- | --- | --- |
| `url` | MangaDex manga URL | — |
| `mode` | `v` (volume) or `c` (chapter) | `v` |
| `start` | Starting number | `1` |
| `end` | Ending number (optional) | same as start |
| `lang` | `es-la`, `en`, `es`, etc. | `es-la` |

**Examples:**

```text
/manga https://mangadex.org/title/xxx v 1
/manga https://mangadex.org/title/xxx v 1 5
/manga https://mangadex.org/title/xxx c 10 20 en
```

> [!NOTE]
> The bot only responds to your Chat ID. Any other user is silently ignored.
> The Cloudflare Workers free plan includes 100,000 requests/day — more than enough for personal use.

---

## 🧪 Development

If you want to contribute or modify the project:

```bash
# Create virtual environment and install in editable mode
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

# Run tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Verify CLI
.\.venv\Scripts\python.exe -m md2kindle --help
```

---

## 💡 Additional Notes & Troubleshooting

- **Storage**: If you're running low on disk space, set `DELETE_CBZ_AFTER_CONVERSION = True` in `md2kindle/config.py` to automatically delete the raw `.cbz` files after conversion.
- **Script fails just before converting**: This usually happens when KCC can't find the `kindlegen` component. Make sure you've installed **Kindle Previewer** and opened it at least once so it registers its internal binaries.
