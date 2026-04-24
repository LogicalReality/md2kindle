# 📖 md2kindle (MangaDex to Kindle)

Un script de automatización en Python que simplifica la descarga de manga desde [MangaDex](https://mangadex.org) y su conversión automática a formatos optimizados para e-readers Kindle usando [KCC (Kindle Comic Converter)](https://github.com/ciromattia/kcc).

---

## 🚀 Características Principales

- **Descarga Fluida**: Descarga volúmenes completos o capítulos individuales, uno a uno o en lote (rangos).
- **Conversión Automática**: Detecta los archivos `.cbz` resultantes y lanza la conversión casi sin intervención manual.
- **🛡️ Entrega E2EE (Zero Trace)**: Los archivos pesados (>45MB) se cifran localmente y se genera un enlace de "un solo uso" (1 descarga / 1 hora) mediante `ffsend`. Privatización total garantizada.
- **🔗 Integración con Telegram**: Recibe tus mangas convertidos (o sus enlaces cifrados) directamente en tu móvil o app de Telegram para enviarlos a tu e-reader.
- **☁️ GitHub Actions (Nube)**: ¡No necesitas tu PC! Dispara la descarga y conversión desde la web de GitHub y recibe el resultado en segundos.
- **⚡ Eficiencia de Procesamiento**: Detección inteligente de archivos `.mobi` existentes para saltar descargas y conversiones innecesarias.
- **Preconfigurado para Kindle**: Formato MOBI/AZW3 con lectura RTL, escalado avanzado e unión de páginas dobles.

---

## 🛠️ Requisitos Previos

Para la estructura general, asegúrate de tener instaladas las siguientes herramientas en tu entorno (Windows):

1. **[Python 3.x](https://www.python.org/downloads/)**: El intérprete necesario para este script.
2. **[mangadex-dl](https://github.com/mansuf/mangadex-downloader/releases)**: Motor para la extracción de mangas. (`mangadex-dl.exe`).
3. **[Kindle Comic Converter (KCC)](https://github.com/ciromattia/kcc/releases)**: Requiere el ejecutable especializado `kcc_c2e.exe`.
4. **[Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011)**: KCC lo usa para generar archivos `.mobi`.
5. **[ffsend](https://github.com/timvisee/ffsend/releases)**: Necesario para la entrega cifrada (E2EE) de archivos pesados.

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

### 4. [Opcional] Descargar ffsend para Entregas Cifradas

Si planeas usar la función de Telegram con archivos pesados (+45MB), necesitas `ffsend`:

1. Ve a [timvisee/ffsend/releases](https://github.com/timvisee/ffsend/releases).
2. Descarga el binario de Windows.
3. Colócalo en la carpeta del proyecto o agrégalo al PATH del sistema.

> [!TIP]
> Si no usas Telegram o solo envías archivos pequeños, puedes omitir este paso.

### 5. Clonar o Descargar el Repositorio

```bash
git clone https://github.com/tu-usuario/md2kindle.git
cd md2kindle
```

### 6. Instalar Dependencias de Python

```bash
pip install -r requirements.txt
```

Esto instalará `requests` y `mangadex-downloader` (la librería Python oficial).

> [!NOTE]
> Si prefieres el binario standalone (`mangadex-dl.exe`), descárgalo desde
> [mansuf/mangadex-downloader/releases](https://github.com/mansuf/mangadex-downloader/releases)
> y colócalo dentro de `mangadex-dl/` en la raíz del proyecto. El script lo detectará automáticamente.

### 7. Colocar los Binarios (Detección Automática)

El script detecta las herramientas en **cascada**, sin necesidad de editar código:

| Prioridad | Ubicación buscada |
| :--- | :--- |
| **1ª** | Raíz del proyecto (`./mangadex-dl/mangadex-dl.exe`, `./kcc_c2e_*.exe`) |
| **2ª** | PATH del sistema (`mangadex-dl`, `kcc-c2e` instalados globalmente) |

**Modo Portable** — Estructura recomendada si usas los binarios directamente:

```
md2kindle/
├── mangadex-dl/
│   └── mangadex-dl.exe
├── kcc_c2e_9.6.2.exe
└── md2kindle.py
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
   ```

2. Para cargarlas automáticamente, puedes usar un wrapper o configurar tu IDE/terminal.

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
| `--silent` | Reducir verbosidad de logs | `--silent` |

**Ejemplo completo** — Descargar los volúmenes 1 al 5 en español y enviar a Telegram:

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
2. Selecciona el workflow: **Manga to Kindle Delivery**.
3. Haz clic en **Run workflow** e ingresa:
   - **URL de MangaDex** (ej: `https://mangadex.org/title/8015...`)
   - **Modo**: `v` (volumen) o `c` (capítulo)
   - **Volumen/Capítulo inicial y final**
   - **Idioma**: `es-la`, `en`, `es`, etc.
   - **Omitir Oneshots**: `true` o `false`
4. Haz clic en **Run** y observa el proceso en tiempo real.

### 4. Recibir el Archivo

- Si el archivo es menor a 45MB, arrive directamente a Telegram.
- Si es mayor, recibirás un **enlace efímero E2EE** de ffsend (1 descarga / 1 hora).

> [!TIP]
> **Privacidad**: La llave de descifrado viaja en el fragmento del URL (`#`), por lo que ni siquiera el servidor de ffsend puede ver tu manga.

---

## 💡 Notas Adicionales y Resolución de Problemas

- **Almacenamiento Redundante**: Si te enfrentas a problemas de disco duro, y no deseas mantener la copia ".cbz", puedes editar la variable `DELETE_CBZ_AFTER_CONVERSION` igualándola a `True` para auto-eliminar los brutos.
- **El script falla justo antes de transformar**: A veces pasa si la herramienta `KCC` no logra encontrar el componente `kindlegen`. Asegúrate de haber instalado **Kindle Previewer** y abrilo una vez para asentar sus registros.
