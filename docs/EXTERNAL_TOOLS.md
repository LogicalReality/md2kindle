# 🛠️ Herramientas Externas (KCC & mangadex-dl)

Este documento detalla los comandos y parámetros de las herramientas que utiliza `md2kindle`. Es útil para entender qué estamos pasando en `kcc_custom_args` y cómo extender la funcionalidad del pipeline.

---

## 📘 KCC (Kindle Comic Converter)

KCC es el motor que transforma las imágenes (`.cbz`) en libros electrónicos optimizados. En el código, lo llamamos a través de `kcc_c2e`.

### Mapeo en `settings.py`

| Configuración | Flag de KCC | Descripción |
| :--- | :--- | :--- |
| `kcc_profile` | `-p`, `--profile` | Perfil del dispositivo (e.g., `KO` para Kindle Oasis, `KV` para Voyage). |
| `kcc_format` | `-f`, `--format` | Formato de salida (`MOBI`, `EPUB`, `CBZ`, `KFX`). |
| `kcc_custom_args` | (Varios) | Lista de flags adicionales de procesamiento. |

### Argumentos Comunes (usados en `kcc_custom_args`)

*   **`-m`, `--manga-style`**: Habilita el modo manga (lectura de derecha a izquierda y división de páginas dobles en consecuencia).
*   **`-r SPLITTER`, `--splitter`**: Modo de procesado de páginas dobles.
    *   `0`: Dividir (Default).
    *   `1`: Rotar (Usado en `md2kindle`).
    *   `2`: Ambos.
*   **`-u`, `--upscale`**: Redimensiona imágenes más pequeñas que la resolución del dispositivo.
*   **`-s`, `--stretch`**: Estira las imágenes para llenar toda la pantalla.
*   **`-q`, `--hq`**: Intenta aumentar la calidad de la magnificación.
*   **`-w`, `--webtoon`**: Modo de procesamiento especial para webtoons (scrolling vertical).
*   **`--forcecolor`**: No convierte las imágenes a escala de grises (útil si tenés un Kindle Color o usás la app de tablet).

---

## 📥 MangaDex Downloader (`mangadex-dl`)

Es la herramienta encargada de scrapear la API de MangaDex y bajar los capítulos.

### Argumentos Clave en el Pipeline

*   **`--save-as`**: Determina cómo se agrupan los archivos descargados.
    *   `cbz-volume`: Crea un archivo `.cbz` por cada volumen.
    *   `cbz-single`: Crea un único archivo `.cbz` con todos los capítulos solicitados.
    *   `raw`: Descarga las imágenes sueltas en carpetas (usado en el modo de descarga mixta).
*   **`--language`, `-lang`**: Código de idioma (e.g., `es-la`, `en`, `ja`).
*   **`--no-oneshot-chapter`**: Ignora capítulos únicos (oneshots) si existen.
*   **`--start-volume` / `--end-volume`**: Define el rango de tomos a descargar.
*   **`--start-chapter` / `--end-chapter`**: Define el rango de capítulos.

---

## 🔗 Referencias Rápidas para `AppConfig`

Si querés cambiar el comportamiento por defecto, editá `md2kindle/core/config/settings.py`:

```python
# Ejemplo: Cambiar a formato EPUB y agregar calidad HQ
kcc_format: str = "EPUB"
kcc_custom_args: list[str] = ["-m", "-r", "1", "-u", "-q"]
```

## 📱 Perfiles de Dispositivo (KCC)

Estos son los valores que podés usar en `kcc_profile` según tu e-reader.

### 📱 Kindle (Amazon)

*   **`KO`**: Kindle Oasis (1, 2 y 3) [1264x1680] - *Perfil "Master" de 300 PPI. Es idéntico en resolución al nuevo Paperwhite 12.*
*   **`KPW6`**: Kindle Paperwhite 6 (12ª Gen - 7") [1264x1680] - *Misma resolución que el Oasis.*
*   **`KPW5`**: Kindle Paperwhite 5 (11ª Gen - 6.8") [1236x1648]
*   **`K11`**: Kindle 11 (Modelo 2022)
*   **`KS`**: Kindle Scribe
*   **`KCS`**: Kindle Colorsoft (Color)
*   **`KV`**: Kindle Voyage
*   **`KPW34`**: Kindle Paperwhite 3 y 4
*   **`KPW`**: Kindle Paperwhite 1 y 2
*   **`K810`**: Kindle 8 y 10 (Modelos básicos)
*   **`K57`**: Kindle 5 y 7
*   **`K34`**: Kindle 3 y 4 (Keyboard/Touch antiguo)
*   **`KDX`**: Kindle DX
*   **`K1` / `K2`**: Kindle 1 y 2 (Legacy)

### 📱 Kobo

*   **`KoLC`**: Kobo Libra Colour (Color)
*   **`KoCC`**: Kobo Clara Colour (Color)
*   **`KoL`**: Kobo Libra (H2O/2)
*   **`KoS`**: Kobo Sage
*   **`KoE`**: Kobo Elipsa (1 y 2)
*   **`KoC`**: Kobo Clara (HD/2E)
*   **`KoF`**: Kobo Forma
*   **`KoN`**: Kobo Nia
*   **`KoAO`**: Kobo Aura ONE
*   **`KoAH2O`**: Kobo Aura H2O
*   **`KoGHD`**: Kobo Glo HD
*   **`KoMT`**: Kobo Mini / Touch

### 📱 reMarkable

*   **`RmkPP`**: reMarkable Paper Pro (Color)
*   **`Rmk2`**: reMarkable 2
*   **`Rmk1`**: reMarkable 1

### ⚙️ Otros

*   **`OTHER`**: Para cualquier otro dispositivo. Requiere que definas el tamaño manualmente usando `--customwidth` y `--customheight`.


> [!TIP]
> Por defecto usamos `KO` (Kindle Oasis), que funciona perfecto en la mayoría de los Kindle Paperwhite modernos (10ma gen en adelante).

