# 📖 md2kindle (MangaDex to Kindle)

🌐 [English](README.md) | **Español**

Un script de automatización en Python que simplifica la descarga de manga desde [MangaDex](https://mangadex.org) y su conversión automática a formatos optimizados para e-readers Kindle usando [KCC (Kindle Comic Converter)](https://github.com/ciromattia/kcc).

---

## 🚀 Características Principales

- **Descarga Fluida**: Descarga volúmenes completos o capítulos individuales, uno a uno o en lote (rangos).
- **Conversión Automática**: Detecta los archivos `.cbz` resultantes y lanza la conversión casi sin intervención manual.
- **☁️ Entrega vía Cloudflare R2**: Soporte para entrega mediante la nube, superando el límite de 50MB de Telegram con enlaces de alta velocidad.
- **🔗 Integración con Telegram**: Recibe tus mangas convertidos (o sus enlaces de R2) directamente en tu móvil.
- **🛡️ Pipeline Robusto**: Validación automática de archivos descargados y fallback de idiomas por volumen (`es-la` > `en` > `es`).
- **☁️ GitHub Actions (Nube)**: ¡No necesitas tu PC! Dispara la descarga y conversión desde la web de GitHub y recibe el resultado en segundos.
- **🤖 Bot de Telegram Interactivo**: Activa el workflow directamente desde Telegram con un comando.
- **⚡ Eficiencia de Procesamiento**: Detección inteligente de archivos `.mobi` existentes para saltar descargas y conversiones innecesarias.
- **Preconfigurado para Kindle**: Formato MOBI/AZW3 con lectura RTL, escalado avanzado e unión de páginas dobles.

---

## 🛠️ Requisitos Previos

Para la estructura general, asegúrate de tener instaladas las siguientes herramientas en tu entorno (Windows):

1. **[Python 3.13+](https://www.python.org/downloads/)**: El intérprete necesario para este script.
2. **[mangadex-dl](https://github.com/mansuf/mangadex-downloader/releases)**: Motor para la extracción de mangas. (`mangadex-dl.exe`).
3. **[Kindle Comic Converter (KCC)](https://github.com/ciromattia/kcc/releases)**: Requiere el ejecutable especializado `kcc_c2e.exe`.
4. **[Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011)**: KCC lo usa para generar archivos `.mobi`.
5. **[ffsend](https://github.com/timvisee/ffsend/releases)**: Fallback para la entrega de archivos pesados cuando R2 no está disponible. Requerido para archivos de más de 50MB.

---

## 🖥️ Ejecución Local — Guía Paso a Paso

Sigue estos pasos para dejar el entorno listo para funcionar en tu máquina.

### 1. Instalar Python 3.x

Descarga e instala Python desde [python.org](https://www.python.org/downloads/). Durante la instalación, marca la opción **"Add Python to PATH"**.

### 2. Descargar mangadex-dl

1. Ve a [mansuf/mangadex-downloader/releases](https://github.com/mansuf/mangadex-downloader/releases).
2. Descarga el binario de Windows (`mangadex-dl.exe`).
3. Crea la carpeta `C:\mangadex-dl\` y coloca el ejecutable ahí.

### 3. Instalar Kindle Previewer (Kindlegen)

1. Descarga **Kindle Previewer** desde [amazon.com/Kindle-Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011).
2. Instálalo y ábrelo **al menos una vez** para que registre sus binaries internamente.
3. KCC lo detectará automáticamente.

> [!NOTE]
> Sin Kindle Previewer, KCC fallará en el paso final de conversión con un error sobre `kindlegen`.

### 4. Instalar ffsend (Fallback para Archivos Pesados)

`ffsend` se usa como fallback automático cuando Cloudflare R2 no está disponible y el archivo pesa más de 50MB.

1. Ve a [timvisee/ffsend/releases](https://github.com/timvisee/ffsend/releases).
2. Descarga el binario de Windows.
3. Colocalo en `./bin/ffsend.exe` o agregalo al PATH del sistema.

> [!TIP]
> Si usas Cloudflare R2 de forma exclusiva y nunca falla, el script no va a necesitar `ffsend`. Pero tenerlo instalado garantiza que el pipeline nunca se quede sin salida.

### 5. Clonar o Descargar el Repositorio

```bash
git clone https://github.com/tu-usuario/md2kindle.git
cd md2kindle
```

### 6. Instalar Dependencias de Python

```bash
pip install .
```

Esto instalará `requests`, `python-dotenv`, `boto3` (para Cloudflare R2) y registrará el comando `md2kindle` en tu entorno usando `pyproject.toml`.

> [!NOTE]
> Si prefieres el binario standalone (`mangadex-dl.exe`), descárgalo desde
> [mansuf/mangadex-downloader/releases](https://github.com/mansuf/mangadex-downloader/releases)
> y colócalo dentro de `mangadex-dl/` en la raíz del proyecto. El script lo detectará automáticamente.

### 7. Colocar los Binarios (Detección Automática)

El script detecta las herramientas en **cascada**, sin necesidad de editar código:

| Prioridad | Ubicación buscada |
| :--- | :--- |
| **1ª** | Carpeta del proyecto: `./bin/` (ej. `./bin/ffsend.exe`) |
| **2ª** | Carpetas específicas de herramienta: `./bin/mangadex-dl/mangadex-dl.exe` |
| **3ª** | Raíz del proyecto (Legacy/Portable) |
| **4ª** | PATH del sistema (`mangadex-dl`, `kcc-c2e` instalados globalmente) |

**Estructura Profesional** — Organización recomendada para los binarios:

```text
md2kindle/
├── bin/
│   ├── mangadex-dl/
│   │   └── mangadex-dl.exe
│   ├── kcc_c2e_10.1.2.exe    # Detección dinámica (kcc*c2e*.exe)
│   └── ffsend.exe
├── md2kindle/            # Código Fuente (Paquete)
│   ├── cli.py            # Parsing de argumentos
│   ├── pipeline.py       # Orquestación del flujo
│   ├── models.py         # Contratos de datos tipados
│   ├── config.py         # Configuración de rutas y herramientas
│   ├── mangadex/         # API + Downloader de MangaDex
│   └── delivery/         # Telegram + R2 + ffsend (legacy)
├── md2kindle.py          # Punto de entrada local (wrapper)
├── .env                  # Credenciales locales (opcional)
└── pyproject.toml        # Definición del paquete
```

> [!TIP]
> Si instalaste `mangadex-downloader` vía pip (paso anterior), no necesitas el binario.
> El script lo encontrará en el PATH automáticamente.

### 8. [Opcional] Configurar Variables de Entorno para Telegram

El script detecta automáticamente si las variables `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID` están disponibles. Tienes tres formas de configurarlas:

#### Opción A: Archivo `.env` (Recomendado para desarrollo local)

1. Crea un archivo `.env` en la raíz del proyecto:

   ```env
   TELEGRAM_TOKEN=tu_token_aqui
   TELEGRAM_CHAT_ID=tu_chat_id_aqui

   # Cloudflare R2 (Opcional - Para archivos pesados)
   R2_ACCOUNT_ID=tu_account_id
   R2_ACCESS_KEY_ID=tu_access_key
   R2_SECRET_ACCESS_KEY=tu_secret_key
   R2_BUCKET_NAME=tu_bucket_name
   ```

2. El script cargará estas variables automáticamente al iniciar mediante `python-dotenv`.

> [!WARNING]
> **Nunca subas el archivo `.env` a GitHub.** Ya está ignorado por `.gitignore`,
> pero verifica que no esté tracked antes de hacer commit.

#### Opción B: Variables del Sistema (Windows CMD)

```cmd
set TELEGRAM_TOKEN=tu_token_aqui
set TELEGRAM_CHAT_ID=tu_chat_id_aqui
python md2kindle.py --url "..." --telegram
```

#### Opción C: PowerShell

```powershell
$env:TELEGRAM_TOKEN="tu_token_aqui"
$env:TELEGRAM_CHAT_ID="tu_chat_id_aqui"
python md2kindle.py --url "..." --telegram
```

---

## ⚙️ Configuración y Setup

Toda la configuración central vive en `md2kindle/config.py`. Los valores por defecto funcionan sin modificación en la mayoría de los casos:

```python
# ==========================================
# CONFIGURACIÓN  (md2kindle/config.py)
# ==========================================

# Carpetas de destino — Relativas al proyecto
OUTPUT_FOLDER_MANGA = "./downloads"   # CBZ descargados
OUTPUT_FOLDER_KCC   = "./output"      # MOBI/AZW3 convertidos

# Ajustes de KCC
KCC_PROFILE     = "KO"               # KO = Kindle Oasis / Paperwhite 12
KCC_FORMAT      = "MOBI"             # Formato Dual MOBI/AZW3
KCC_CUSTOM_ARGS = ["-m", "-r", "1", "-u"]

# Comportamiento general
DELETE_CBZ_AFTER_CONVERSION   = False
DEFAULT_LANGUAGE               = "es-la"
SKIP_ONESHOTS_ON_VOLUME_MODE   = True
```

## 🛠️ Guía de Configuración Avanzada

Para personalizar el comportamiento del script, puedes modificar las variables en la sección `CONFIGURACIÓN` de `md2kindle.py`. A continuación, se detallan los parámetros disponibles para cada herramienta:

### 1. Kindle Comic Converter (KCC) - `kcc-c2e`

Estos ajustes definen la calidad y formato del archivo final que leerá tu Kindle.

- `KCC_PROFILE`: Determina la resolución de salida. `KO` es ideal para Kindle Oasis/Paperwhite 12.
- `KCC_FORMAT`: Formato del archivo final (`MOBI`, `AZW3`, `KFX`, `EPUB`).

#### KCC Custom Arguments (`KCC_CUSTOM_ARGS`)

Usa estos "flags" dentro de la lista (ej: `["-m", "-u"]`).

| Flag | Descripción | Recomendación |
| :--- | :--- | :--- |
| `-m` | **Manga Mode**: Activa la lectura de Derecha a Izquierda (RTL). | **On** |
| `-r 1` | **Rotate Spreads**: Detecta páginas dobles y las rota 90°. | **On** |
| `-u` | **Upscale**: Escala imágenes pequeñas para llenar la pantalla. | **On** |
| `-w` | **Webtoon**: Procesa archivos como tiras verticales infinitas. | **On** (Solo Webtoons) |
| `-c` | **Color**: Desactiva la conversión a escala de grises. | **On** (Kindle Color) |
| `-q` | **Quality**: Algoritmo de redimensionado de alta calidad. | **On** |

### 2. MangaDex Downloader - Motor de Extracción

Configura cómo el motor (`mangadex-dl`) busca y filtra los capítulos en los servidores.

- **`SKIP_ONESHOTS_ON_VOLUME_MODE`**:
  - `True`: (Recomendado) Ignora capítulos tipo "Oneshot" o especiales.
  - `False`: Incluye absolutamente todo lo listado.
- **`DEFAULT_LANGUAGE`**: Establece el idioma de descarga. Si un capítulo no existe en este idioma, el script preguntará qué versión bajar.

#### Códigos de Idioma Prioritarios

| Prioridad | Código | Idioma |
| :--- | :---: | :--- |
| **🥇 Principal** | `es-la` | Español (Latinoamérica) |
| **🥈 Alternativo** | `es` | Español (España) |
| **🇬🇧 Global** | `en` | Inglés |
| **🇯🇵 Original** | `ja` | Japonés |
| **🇧🇷 Extra** | `pt-br` | Portugués (Brasil) |

> [!TIP]
> Puedes ver la lista completa (más de 40 idiomas) ejecutando `mangadex-dl --list-languages` en tu terminal.

### 3. Automatización del Script

Ajustes de lógica interna de `md2kindle.py`.

- `DELETE_CBZ_AFTER_CONVERSION`:
  - `False`: Conserva el archivo `.cbz` original.
  - `True`: Borra el `.cbz` automáticamente para ahorrar espacio.

---

## 🏃 ¿Cómo se usa?

Puedes operar esta herramienta a través de dos modos:

### Método de Consola (Clásico)

Abre la terminal de comandos (CMD o Powershell), navega mediante tu ruta a la carpeta origen e inicialízalo:

```bash
python md2kindle.py
```

### Rellenando el Asistente (Modo Interactivo)

Al iniciarse te encontrarás con las siguientes preguntas:

- **URL de MangaDex**: Link completo del Manga. (ej: `https://mangadex.org/title/8015...`)
- **Nombre de la carpeta**: Carpeta donde organizarás todas sus entregas a futuro. (ej. `Berserk`)
- **Idioma**: Por defecto usa latino (`es-la`). Pulsar enter lo confirmará.
- **Volumen o Capítulo**: Escribir la letra de la dimensión en que deseas compilar. (`v` o `c`)
- **Rangos de descarga**: Iniciar y determinar el fin de la descarga (ej: para un solo Volumen contestar `25` en ambas preguntas).

### Método con Argumentos CLI (Avanzado)

Puedes pasar todos los parámetros directamente sin pasar por el asistente interactivo:

```bash
python md2kindle.py <URL> [opciones]
```

| Argumento | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `url` | URL del manga en MangaDex | `https://mangadex.org/title/8015...` |
| `--title` | Nombre de la carpeta de salida | `--title "Berserk"` |
| `--lang` | Idioma de descarga | `--lang es-la` |
| `--mode` | `v` (volumen) o `c` (capítulo) | `--mode v` |
| `--start` | Número inicial | `--start 1` |
| `--end` | Número final (por defecto = `--start`) | `--end 5` |
| `--skip-oneshots` | Omitir capítulos Oneshot | `--skip-oneshots` |
| `--telegram` | Enviar resultado a Telegram | `--telegram` |
| `--r2` | Subir a R2 y enviar enlace | `--r2` |
| `--silent` | Reducir verbosidad de logs | `--silent` |

**Ejemplo completo** — Descargar los volúmenes 1 al 5 en español y subir a R2:

```bash
python md2kindle.py https://mangadex.org/title/801513ba-a712-498c-8f57-cae55b38cc92 \
  --mode v --start 1 --end 5 --lang es-la \
  --skip-oneshots --r2
```

**Alternativa** — Enviar el archivo directamente por Telegram (archivos menores a 50MB):

```bash
python md2kindle.py https://mangadex.org/title/801513ba-a712-498c-8f57-cae55b38cc92 \
  --mode v --start 1 --end 5 --lang es-la \
  --skip-oneshots --telegram
```

> [!NOTE]
> El script detecta automáticamente si el idioma solicitado no tiene capítulos disponibles
> y hace fallback automático: `es-la → en → es`.

---

## ☁️ Automatización con GitHub Actions

Si prefieres no mantener Python instalado en tu máquina, puedes usar el pipeline de GitHub Actions.

### 1. Subir el Repositorio a GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/md2kindle.git
git push -u origin main
```

### 2. Configurar Secrets en GitHub

Para que el bot de Telegram funcione, necesitas agregar tus credenciales:

1. En tu repositorio de GitHub, ve a **Settings → Secrets and variables → Actions**.
2. Crea dos secrets:

| Secret             | Valor                                     |
| ------------------ | ----------------------------------------- |
| `TELEGRAM_TOKEN`   | Token de tu bot de Telegram               |
| `TELEGRAM_CHAT_ID` | ID del chat donde recibirás los archivos  |
| `R2_ACCOUNT_ID`    | ID de cuenta de Cloudflare                |
| `R2_ACCESS_KEY_ID` | R2 API Access Key ID                      |
| `R2_SECRET_ACCESS_KEY`| R2 API Secret Access Key               |
| `R2_BUCKET_NAME`   | Nombre del bucket de R2                   |

#### ¿Cómo obtener los tokens de Telegram?

1. **TELEGRAM_TOKEN**:
   - Habla con [@BotFather](https://t.me/BotFather) en Telegram.
   - Envía `/newbot` y sigue las instrucciones.
   - Al finalizar, BotFather te dará un token como: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`
   - Ese es tu `TELEGRAM_TOKEN`.

2. **TELEGRAM_CHAT_ID**:
   - Agrega tu bot a tu grupo o chat.
   - Habla con [@userinfobot](https://t.me/userinfobot) o [@getidsbot](https://t.me/getidsbot).
   - El bot te responderá con tu **Chat ID** (ej: `123456789`).
   - También puedes usar [@MyChatInfoBot](https://t.me/MyChatInfoBot) si quieres el ID de un grupo.

> [!NOTE]
> Si eres el único usuario, el Chat ID suele ser tu **User ID** personal (número largo y negativo).

### 3. Ejecutar el Workflow

1. Ve a la pestaña **Actions** en tu repositorio.
2. Selecciona el workflow: **Manga Pipeline (R2 & Telegram)**.
3. Haz clic en **Run workflow** e ingresa:
   - **URL de MangaDex** (ej: `https://mangadex.org/title/8015...`)
   - **Modo**: `v` (volumen) o `c` (capítulo)
   - **Volumen/Capítulo inicial y final**
   - **Idioma**: `es-la`, `en`, `es`, etc.
   - **Omitir Oneshots**: `true` o `false`
4. Haz clic en **Run** y observa el proceso en tiempo real.

### 4. Recibir el Archivo

- Con **R2 activado** (por defecto): Recibirás un **link de descarga** limpio por Telegram, válido por 7 días. Los archivos se borran automáticamente del bucket a los 15 días.
- Con **R2 desactivado** (o si falla la subida a R2): El sistema hace fallback automático al método legado — archivos menores a 50MB se envían directamente por Telegram; los más pesados usan enlaces E2EE de ffsend.

> [!TIP]
> R2 es el método recomendado para cualquier tamaño de archivo — es más rápido, no tiene límite de peso y no depende de las restricciones de subida de Telegram.

---

## 🤖 Bot de Telegram — Activación por Comando

En lugar de abrir GitHub Actions manualmente, puedes enviar un mensaje a tu bot de Telegram y el workflow se dispara automáticamente. Esto se implementa con un **Cloudflare Worker** serverless (gratuito).

### Arquitectura

```text
Tú → /manga <url> → Telegram → Cloudflare Worker → GitHub API → Actions → .mobi → Telegram → Tú
```

### Requisitos Previos

- Cuenta en [Cloudflare](https://cloudflare.com) (gratuita)
- Bot de Telegram creado con [@BotFather](https://t.me/BotFather)
- GitHub Personal Access Token (Classic) con scope `workflow`

### 1. Crear el Cloudflare Worker

1. Ve a [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create**.
2. Elige **Hello World Worker**, ponle nombre (ej: `md2kindle-bot`) y haz clic en **Deploy**.
3. Haz clic en **Edit code**, borra el contenido y pega el código de `.github/workers/telegram-bot.js`.
4. Haz clic en **Deploy**.

### 2. Configurar los Secrets del Worker

En tu Worker → **Settings** → **Variables and Secrets** → **Add**:

| Secret | Valor |
| --- | --- |
| `TELEGRAM_TOKEN` | Token de tu bot (BotFather) |
| `TELEGRAM_CHAT_ID` | Tu Chat ID personal (obtenerlo con [@userinfobot](https://t.me/userinfobot)) |
| `GITHUB_PAT` | GitHub Classic Token con scope `workflow` |

> [!WARNING]
> Usa un **Classic Token**, no un Fine-grained. Los Fine-grained tokens devuelven 403 en el endpoint `workflow_dispatch` a menos que configures permisos explícitos por repositorio.

### 3. Crear el GitHub PAT

1. Ve a [github.com/settings/tokens/new](https://github.com/settings/tokens/new) (Classic).
2. Marca solo el scope: ✅ `workflow`.
3. Genera el token y cópialo en el secret `GITHUB_PAT` del Worker.

### 4. Registrar el Webhook de Telegram (una sola vez)

Abre esta URL en tu navegador (reemplaza `<TU_TOKEN>` y `<TU_WORKER_URL>`):

```text
https://api.telegram.org/bot<TU_TOKEN>/setWebhook?url=<TU_WORKER_URL>
```

Si todo está correcto verás:

```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Uso

```text
/manga <url> <modo> <inicio> [fin] [idioma]
```

| Parámetro | Descripción | Default |
| --- | --- | --- |
| `url` | URL del manga en MangaDex | — |
| `modo` | `v` (volumen) o `c` (capítulo) | `v` |
| `inicio` | Número inicial | `1` |
| `fin` | Número final (opcional) | igual a inicio |
| `idioma` | `es-la`, `en`, `es`, etc. | `es-la` |

**Ejemplos:**

```text
/manga https://mangadex.org/title/xxx v 1
/manga https://mangadex.org/title/xxx v 1 5
/manga https://mangadex.org/title/xxx c 10 20 en
```

> [!NOTE]
> El bot solo responde a tu Chat ID. Cualquier otro usuario es ignorado silenciosamente.
> El plan gratuito de Cloudflare Workers incluye 100,000 requests/día — más que suficiente para uso personal.

---

## 🧪 Desarrollo

Si querés contribuir o modificar el proyecto:

```bash
# Crear entorno virtual e instalar en modo editable
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

# Correr los tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Verificar CLI
.\.venv\Scripts\python.exe -m md2kindle --help
```

---

## 💡 Notas Adicionales y Resolución de Problemas

- **Almacenamiento Redundante**: Si te enfrentas a problemas de disco duro, edita `DELETE_CBZ_AFTER_CONVERSION = True` en `md2kindle/config.py` para auto-eliminar los archivos `.cbz` crudos tras la conversión.
- **El script falla justo antes de transformar**: A veces pasa si la herramienta `KCC` no logra encontrar el componente `kindlegen`. Asegúrate de haber instalado **Kindle Previewer** y abrirlo una vez para asentar sus registros.
