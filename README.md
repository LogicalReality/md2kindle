# 📖 md2kindle (MangaDex to Kindle)

Un script de automatización en Python que simplifica la descarga de manga desde [MangaDex](https://mangadex.org) y su conversión automática a formatos optimizados para e-readers Kindle usando [KCC (Kindle Comic Converter)](https://github.com/ciromattia/kcc).

---

## 🚀 Características Principales

- **Descarga Fluida**: Descarga volúmenes completos o capítulos individuales, uno a uno o en lote (rangos).
- **Conversión Automática**: Detecta los archivos `.cbz` resultantes y lanza la conversión casi sin intervención manual.
- **Preconfigurado para Kindle**: Listo para exportar formato MOBI/AZW3 con lectura de derecha a izquierda, escalado avanzado de resolución e unión de páginas dobles rotadas.
- **Flujo Interactivo**: Un asistente de terminal muy sencillo amigable con el usuario.

---

## 🛠️ Requisitos Previos

Para la estructura general, asegúrate de tener instaladas las siguientes herramientas en tu entorno (Windows):

1. **[Python 3.x](https://www.python.org/downloads/)**: El intérprete necesario para este script.
2. **[mangadex-dl](https://github.com/mansuf/mangadex-downloader/releases)**: Aplicación usada como motor para la extracción de mangas. (`mangadex-dl.exe`).
3. **[Kindle Comic Converter (KCC)](https://github.com/ciromattia/kcc/releases)**: Se requiere el ejecutable especializado por línea de comandos, específicamente `kcc_c2e.exe`.
4. **[Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011)**: KCC requiere el componente `kindlegen` oculto en este programa para empaquetar en formato Amazon (.mobi/.azw3). Al instalarlo, KCC lo autodetectará.

---

## ⚙️ Configuración y Setup

Por defecto, el script ha sido escrito pensando en un usuario habitual. Antes de la primera ejecución, es indispensable abrir `md2kindle.py` en cualquier editor de texto (Ej. Visual Studio Code / Bloc de Notas) para mapear correctamente las herramientas instaladas en tu disco duro:

```python
# ==========================================
# CONFIGURACIÓN
# ==========================================
# Mapeo Absoluto de Ejecutables
MANGADEX_DL_PATH = r"C:\mangadex-dl\mangadex-dl.exe"
KCC_C2E_PATH = r"C:\Antigravity\md2kindle\kcc_c2e_9.6.2.exe"

# Entornos de Carpeta de Destinos
OUTPUT_FOLDER_MANGA = r"C:\Manga"
OUTPUT_FOLDER_KCC = r"C:\KCC Output"

# Ajustes Base para KCC (Target: Kindle Paperwhite 12)
KCC_PROFILE = "KO"  # Activo para dispositivos de >1000px y Serie Signature.
KCC_FORMAT = "MOBI" # Generacion del archivo DUAL
...
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

### Método Autoejecutable de Windows (`.bat`)

Habiendo descargado o clonado la carpeta en Windows, bastará con **Hacer doble click** en el archivo adjunto:
`Iniciar_Manga_To_Kindle.bat`

### Rellenando el Asistente

Al iniciarse te encontrarás con las siguientes preguntas:

- **URL de MangaDex**: Link completo del Manga. (ej: `https://mangadex.org/title/8015...`)
- **Nombre de la carpeta**: Carpeta donde organizarás todas sus entregas a futuro. (ej. `Berserk`)
- **Idioma**: Por defecto usa latino (`es-la`). Pulsar enter lo confirmará.
- **Volumen o Capítulo**: Escribir la letra de la dimensión en que deseas compilar. (`v` o `c`)
- **Rangos de descarga**: Iniciar y determinar el fin de la descarga (ej: para un solo Volumen contestar `25` en ambas preguntas).

---

## 💡 Notas Adicionales y Resolución de Problemas

- **Almacenamiento Redundante**: Si te enfrentas a problemas de disco duro, y no deseas mantener la copia ".cbz", puedes editar la variable `DELETE_CBZ_AFTER_CONVERSION` igualándola a `True` para auto-eliminar los brutos.
- **El script falla justo antes de transformar**: A veces pasa si la herramienta `KCC` no logra encontrar el componente `kindlegen`. Asegúrate de haber instalado **Kindle Previewer** y abrilo una vez para asentar sus registros.
