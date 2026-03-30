# Memoria.md

## [2026-03-29 21:20] Sesión de Trabajo: Pipeline de MangaDex a Kindle (Pruebas y Automatización)

- **Objetivo**: Dominar el proceso manual de descarga de manga (Berserk Vol. 25) desde MangaDex (`mangadex-dl`), optimizar su conversión en consola para Kindle Paperwhite 12 Signature Edition (`KCC`), y finalmente automatizar el flujo completo de ambos programas mediante un script de Python.
- **Decisiones**:
  - Descargar tomos compilados en `.cbz` filtrando el idioma (`es-la`).
  - Auditar manualmente las descargas y eliminar capítulos "huérfanos" superpuestos por la metadata original del sitio web (ej. el desfasado Capítulo 383 de Berserk).
  - Efectuar las conversiones a .mobi únicamente mediante la versión CLI de KCC (`kcc_c2e.exe`), omitiendo interfaces gráficas y fijando el perfil target en `KO` e inyectándole las variables óptimas (`-m -r 1 -u`).
  - Centralizar y parametrizar las ejecuciones de los ejecutables de terceros (`mangadex-dl.exe` y `kcc_c2e.exe`) dentro del nuevo script de consola `md2kindle.py`.
  - Desarrollar un archivo puente `.bat` para los inicios desde Windows y dejar asentada la guía de usuario íntegra en el archivo `README.md`.
- **Aprendizajes**:
  - El motor de CLI de `mangadex-dl` es lo bastamente flexible para agrupar en el vuelo (`--save-as cbz-volume`) pero ocasionalmente agrupa material dispar si el proveedor tiene desórdenes de etiquetado en el origen.
  - KCC `c2e.exe` conserva la suprema calidad de las emulaciones visuales que el usuario solía hacer mediante el GUI prestando idéntica atención al *Upscaling*, y requiere incondicionalmente contar con el paquete de Calibre/KindleGen anclado al path del sistema.
  - Integrar las fases de "Post-descarga" localizando los archivos CBZ en las sub-carpetas usando el módulo `glob` de Python.
- **Próximos Pasos**:
  - Iniciar descargas de manga de prueba en uso en la vida real.
  - Transferir y verificar empíricamente los archivos `.mobi` autogenerados al Kindle vía USB.

## [2026-03-29 22:48] Sesión de Trabajo: Filtrado de Capítulos Huérfanos

- **Objetivo**: Evitar que capítulos sin volumen (huérfanos) o muy adelantados se descarguen y conviertan al usar el Modo Volumen.
- **Decisiones**:
  - Implementar una limpieza dinámica post-descarga en Python que borra cualquier archivo `.cbz` que no coincida con el patrón del volumen solicitado (ej: Berserk Ch. 383).
  - Parametrizar el filtro de oneshots mediante la variable `SKIP_ONESHOTS_ON_VOLUME_MODE`, permitiendo al usuario decidir si desea activarlo solo en el Modo Volumen para evitar omitir capítulos 0 o prólogos en el Modo Capítulo por error.
- **Aprendizajes**: `mangadex-downloader v3.1.4` no filtra estrictamente los capítulos `null` (None) al usar rangos de volumen, y `--no-oneshot-chapter` solo afecta a capítulos marcados específicamente como oneshots.
- **Próximos Pasos**: Validar con otros mangas de larga duración y monitorear actualizaciones de `mangadex-dl`.
