# 📖 md2kindle (MangaDex to Kindle)

[🌐 English](README.md) | **Español**

Un pipeline de automatización para descargar manga desde [MangaDex](https://mangadex.org) y convertirlo a formatos optimizados para Kindle (`.mobi`/`.azw3`) usando [KCC](https://github.com/ciromattia/kcc). Diseñado para ejecutarse localmente o en la nube mediante GitHub Actions, con un bot de Telegram integrado para mayor comodidad.

---

## 🚀 Inicio Rápido

Ten tu primer manga en el Kindle en 3 pasos:

1. **Instala los requisitos**: [Python 3.13](https://www.python.org/downloads/) y descarga los ejecutables de [kcc_c2e](https://github.com/ciromattia/kcc/releases), [mangadex-dl](https://github.com/mansuf/mangadex-downloader/releases) y [ffsend](https://github.com/timvisee/ffsend/releases) dentro de la carpeta `bin/` (debes crearla manualmente en la raíz del proyecto).
2. **Prepara el entorno**:

   ```bash
   git clone https://github.com/LogicalReality/md2kindle.git
   cd md2kindle
   pip install -e .
   ```

3. **Lanza tu primera descarga**:
   Puedes ejecutar el asistente interactivo simplemente corriendo `run.bat` (Windows) o mediante Python:

   ```bash
   python md2kindle.py
   ```

---

## ✨ ¿Por qué usar esto?

| Característica | Beneficio |
| :--- | :--- |
| **Fallback Inteligente** | Intenta automáticamente `es-la` > `es` > `en` por cada capítulo. |
| **Optimizado para Kindle** | Lectura RTL, escalado de imágenes y rotación de páginas dobles. |
| **Libertad de Entrega** | Telegram directo (menos de 50MB) o enlaces rápidos de Cloudflare R2. |
| **Cero Mantenimiento** | Detecta binarios automáticamente en `./bin/` o en el PATH del sistema. |
| **Nativo en la Nube** | Corrélo vía GitHub Actions o dispáralo desde Telegram. |

---

## 🛠️ Requisitos y Configuración

### 1. Tabla de Prioridad de Binarios

El script busca las herramientas en este orden. **No requiere configuración manual.**

| Prioridad | Ubicación | Recomendación |
| :--- | :--- | :--- |
| **1ª** | `./bin/` | Coloca `mangadex-dl.exe`, `kcc_c2e.exe` y `ffsend.exe` aquí. |
| **2ª** | PATH del sistema | Instala las herramientas globalmente para acceso general. |
| **3ª** | venv de Python | Si instalaste `mangadex-downloader` vía pip. |

> [!IMPORTANT]
> **Kindle Previewer** debe estar instalado y haberse abierto al menos una vez para que KCC pueda generar archivos `.mobi` correctamente.

### 2. Variables de Envío (`.env`)

Crea un archivo `.env` para automatizar entregas (Telegram/Cloudflare):

```env
# Telegram
TELEGRAM_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Cloudflare (R2 Storage)
CLOUDFLARE_ACCOUNT_ID=tu_account_id
R2_ACCESS_KEY_ID=tu_access_key
R2_SECRET_ACCESS_KEY=tu_secret_key
R2_BUCKET_NAME=tu_bucket_name

# Cloudflare (D1 History - Opcional)
D1_DATABASE_ID=tu_database_id
D1_API_TOKEN=tu_api_token
```

---

## 🏃 Guía de Uso

### Cheat Sheet de CLI

```bash
python md2kindle.py <URL> [OPCIONES]
```

| Argumento | Flag | Ejemplo |
| :--- | :--- | :--- |
| **URL** | (1er arg) | `https://mangadex.org/title/...` |
| **Modo** | `--mode` | `v` (volumen) o `c` (capítulo) |
| **Rango** | `--start`, `--end` | `--start 1 --end 5` |
| **Idioma** | `--lang` | `--lang es-la` |
| **Telegram** | `--telegram` | Entrega directa al chat usando envio directo o ffsend |
| **Cloud R2** | `--r2` | Sube a Cloudflare y envía el enlace a bot de telegram |
| **Silent** | `--silent` | Minimiza la salida de logs |

---

## ☁️ Automatización Cloud

### GitHub Actions

1. **Fork** de este repo.
2. **Agrega Secrets**: Ve a `Settings > Secrets > Actions` y suma tus variables del `.env`.
3. **Ejecuta**: Usa la pestaña `Actions` para disparar el **Manga Pipeline** manualmente.

### Bot de Telegram (Serverless)

Dispara descargas chateando con tu bot:

1. Despliega el Cloudflare Worker en `.github/workers/telegram-bot.js`.
2. Envía: `/manga <url> v 1 5 es-la`

---

## 🧪 Desarrollo y Verificación

### Verificación Local

- [ ] `pip install -e .[dev]`
- [ ] `.venv\Scripts\python.exe -m pytest -v` (Debería dar 27/27 PASS)
- [ ] `python md2kindle.py --help`

---

## 💡 Solución de Problemas

- **¿Archivo de Telegram muy pesado?** Usa el flag `--r2` para entrega vía Cloudflare.
