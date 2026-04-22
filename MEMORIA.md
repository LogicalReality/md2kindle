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

## [2026-03-29 22:48] Sesión de Trabajo: Filtrado de Capítulos Huérfanos

- **Objetivo**: Evitar que capítulos sin volumen (huérfanos) o muy adelantados se descarguen y conviertan al usar el Modo Volumen.
- **Decisiones**:
  - Implementar una limpieza dinámica post-descarga en Python que borra cualquier archivo `.cbz` que no coincida con el patrón del volumen solicitado (ej: Berserk Ch. 383).
  - Parametrizar el filtro de oneshots mediante la variable `SKIP_ONESHOTS_ON_VOLUME_MODE`, permitiendo al usuario decidir si desea activarlo solo en el Modo Volumen para evitar omitir capítulos 0 o prólogos en el Modo Capítulo por error.
- **Aprendizajes**: `mangadex-downloader v3.1.4` no filtra estrictamente los capítulos `null` (None) al usar rangos de volumen, y `--no-oneshot-chapter` solo afecta a capítulos marcados específicamente como oneshots.

## [2026-03-29 23:26] Sesión de Trabajo: Refactorización y Estabilización de md2kindle.py

- **Objetivo**: Corregir un error crítico en `md2kindle.py` donde el parámetro `--language` se separaba de su valor al inyectar lógicamente nuevos *flags* de comando (`--no-oneshot-chapter`), rompiendo la ejecución de `mangadex-dl`.
- **Decisiones**:
  - Refactorizar la construcción de la lista de comandos (`cmd`) para armarlos secuencialmente e impedir la rotura de parejas "flag/valor".
  - Utilizar `subprocess.list2cmdline(cmd)` para los logs de la consola en lugar de un *join* genérico, garantizando que el usuario tenga un *output* con comillas correctas para probar en la terminal localizándolo con seguridad en Windows.
  - Implementar el *tracker* local de tareas `TO-DO-list.md` (con su solución al linter MD041) y un archivo `.gitignore` estandarizado para archivos sensibles y contexto IA.
  - Actualización del workflow global `@[/save_to_do]` para evitar proactivamente errores de linting en otros proyectos.
- **Aprendizajes**: La construcción de comandos para `subprocess` debe ser estrictamente secuencial al añadir lógicas condicionales; el uso de indexados absolutos como `insert(5, x)` causa *side-effects* técnicos invisibles y bloqueantes si la estructura de argumentos original cambia.

## [2026-03-29 23:44] Sesión de Trabajo: Integración Global con Obsidian Vault

- **Objetivo**: Dotar a Antigravity de la capacidad de guardar aprendizajes y explicaciones técnicas directamente en un Vault de Obsidian local.
- **Decisiones**:
  - Creación del workflow global `@[/save_learning]` ubicado en los recursos del agente para persistencia entre proyectos.
  - Definición de la ruta maestra de la bóveda en `C:\Obsidian_Vault\ObsidianVault\Aprendizajes_AI\`.
  - Estandarización del formato de nota: Título en Kebab-case, fecha automática, tags de Obsidian y metadatos YAML (frontmatter).
  - Ajuste fino del workflow para cumplir con las reglas de linting (MD009, MD031, MD041) asegurando que las notas nuevas no generen advertencias en el IDE.
- **Aprendizajes**: Integrar herramientas de toma de notas externas (como Obsidian) mediante el acceso directo al sistema de archivos permite una colaboración fluida sin necesidad de APIs de terceros. La importancia de los encabezados H1 y el espaciado en bloques de código para mantener la higiene del repositorio.

## [2026-03-29 23:51] Sesión de Trabajo: Corrección de Borrado Accidental de Volúmenes

- **Objetivo**: Corregir un error donde el volumen recién descargado era eliminado por la lógica de limpieza de capítulos huérfanos debido a discrepancias en el nombre del archivo (puntos, ceros extra, etc.).
- **Decisiones**:
  - Implementar una búsqueda basada en Expresiones Regulares (Regex) con el patrón `vol\.?\s*0*{vol}\b` para identificar correctamente el volumen sin importar si contiene puntos (`Vol.`) o ceros a la izquierda (`027`).
  - Utilizar `re.IGNORECASE` para garantizar compatibilidad con cualquier combinación de mayúsculas/minúsculas.
  - Ejecutar un script de prueba independiente (`test_regex.py`) para validar múltiples casos de borde antes de aplicar el cambio al script principal.
- **Aprendizajes**: Las comparaciones de cadenas de texto simples (`in`, `not in`) son peligrosas en automatizaciones de archivos donde los nombres pueden variar ligeramente por convenciones de terceros; Regex ofrece la granularidad necesaria para distinguir entre `Vol. 27` y `Vol. 271`.

## [2026-03-30 00:15] Sesión de Trabajo: Documentación Centralizada y Refinamiento visual

- **Objetivo**: Documentar los argumentos de KCC y MangaDex en el `README.md` para facilitar la configuración sin ensuciar el código fuente.
- **Decisiones**:
  - Centralizar la documentación técnica en el `README.md`, dejando `md2kindle.py` solo con referencias mínimas y limpias.
  - Rediseñar la sección de idiomas de MangaDex con una tabla priorizada (🥇, 🥈, 🇬🇧) y descriptiva para mejorar la UX.
  - Agrupar parámetros base de KCC (`KCC_PROFILE`, `KCC_FORMAT`) y sus argumentos CLI en una sección dedicada y visualmente pulida.
  - Incluir instrucciones dinámicas para que el usuario pueda listar todos los idiomas soportados directamente desde la terminal (`mangadex-dl --list-languages`).
- **Aprendizajes**:
  - La documentación visual (tablas, iconos, jerarquías) mejora significativamente la experiencia del usuario al configurar herramientas con muchos parámetros.
  - Mantener una separación clara entre la lógica operativa del script y la referencia de herramientas externas previene la "deuda de conocimiento" y facilita el mantenimiento a largo plazo.

## [2026-03-30 01:25] Sesión de Trabajo: Detección Inteligente de MangaDex

- **Objetivo**: Automatizar la asignación de nombres de carpeta y metadatos de autor mediante la API de MangaDex.
- **Decisiones**:
  - Se implementó un **Selector Interactivo** que permite elegir entre títulos en Romaji (prioritario), Inglés o Español.
  - Se integró la consulta de `relationships` en la API para extraer el **nombre del autor** real.
  - Se modificó `convert_with_kcc` para inyectar el autor (`-a`) y replicar la **estructura de subcarpetas** del origen en la carpeta de destino (`KCC Output`).
- **Aprendizajes**:
  - Uso de `urllib.request` para consultas ligeras a APIs externas sin dependencias pesadas.
  - Manejo de prioridades de idioma (`ja-ro` > `en` > `es-la`) para mejorar la experiencia de usuario.

## [2026-03-30 01:25] Sesión de Trabajo: Organización Espejo y Metadatos Reales para Kindle

- **Objetivo**: Implementar la organización de carpetas para los archivos generados por KCC y refinar la extracción de metadatos (autor) para mejorar la agrupación nativa en e-readers Kindle.
- **Decisiones**:
  - Mantener la "estructura de carpetas espejo" entre el directorio origen (`C:\Manga`) y destino (`C:\KCC Output`) para preservar el orden íntegro y facilitar futuras gestiones locales.
  - Modificar la consulta a la API de MangaDex agregando el parámetro `includes[]=author` para conseguir el creador original de la obra (ex: Kentaro Miura).
  - Inyectar el autor capturado en KCC a través del argumento `-a`.
  - Crear un *fallback* (respaldo) explícitamente comentado que asigne el nombre "MangaDex" sólo si la información de autor falla o es omitida de la base de datos de origen, asegurando la resiliencia del script.
- **Aprendizajes**:
  - El sistema del Kindle ignora las jerarquías anidadas al transferirse por USB y formatea de modo "plano" la vista de la biblioteca. Por tanto, integrar el nombre del autor explícito en los metadatos ofrece una organización automatizada ("agrupar por autor") nativa, suplementando la creación manual de Colecciones en los dispositivos modernos.

## [2026-03-31 02:30] Sesión de Trabajo: Blindaje de Metadata e Inteligencia de URL

- **Objetivo**: Implementar un sistema de detección inteligente de URLs y robustecer la extracción de autores múltiples de MangaDex.
- **Decisiones**:
  - Implementar un **Seguro de Entrada** mediante un Regex universal que detecta UUIDs en URLs canónicas, alias (`/manga/`) y capítulos.
  - Implementar un **Modo Sugerencia**: Si se detecta una URL de capítulo, el script precarga el número de capítulo y volumen en el asistente, permitiendo al usuario aceptarlos con `Enter`.
  - Refinar la metadata para unir múltiples autores con ` & `, filtrando artistas según la preferencia del usuario (Solo Autores).
  - Diseñar un sistema de **Fallo Seguro** que revierte al modo manual si la API no está disponible o la URL es irreconocible, usando `try/except` y validaciones por Regex.
  - Implementar el **Smart Language Override**: Detección automática de discrepancias entre el idioma de la URL y el `DEFAULT_LANGUAGE`, con opción de cambio temporal interactivo.
  - **Corrección de URLs de Capítulo**: Implementar la redirección canónica a la URL del manga padre para permitir descargas de volúmenes completos desde links de capítulos individuales.
- **Aprendizajes**: El uso de Regex flexibles y sugerencias de `input()` mejora drásticamente la UX sin quitarle control al usuario. La validación prematura de URLs previene errores de red innecesarios y aumenta la percepción de "inteligencia" del script al evitar descargas en idiomas incorrectos o incompletas por contexto limitado.

## [2026-03-30 23:40] Sesión de Trabajo: Conclusión y Plan de Blindaje

- **Objetivo**: Estabilizar el sistema de redirección y documentar los casos de borde para futuras expansiones.
- **Decisiones**:
  - Se identificaron 8 casos de borde (edge cases) técnicos para robustecer el script en la próxima fase.
  - Se validó con éxito la descarga de volúmenes completos desde URLs de capítulos individuales (Fix de Redirección Canónica).

## [2026-03-31 14:40] Sesión de Trabajo: Auditoría Inteligente y Robustez en Volúmenes

- **Objetivo**: Optimizar la canalización MangaDex-to-Kindle con un manejo más inteligente de volúmenes/capítulos y un sistema de auditoría de integridad.
- **Decisiones**:
  - **API Whitelisting**: Sustitución de limpieza basada en Regex por una "Lista Blanca" obtenida de la API `/aggregate`. Solo se borran archivos que MangaDex confirme que no pertenecen al volumen solicitado.
  - **Validación Pre-Descarga**: El script ahora verifica si el volumen ingresado existe en los servidores ANTES de llamar a `mangadex-dl`, ahorrando tiempo y errores.
  - **Oneshots Interactivos**: El filtro de capítulos promocionales ya no es un ajuste estático; ahora el script pregunta al usuario en cada descarga.
  - **Auditoría Universal**: El reporte final de capítulos faltantes (`Faltan: [X, Y]`) ahora funciona tanto para volúmenes como para rangos de capítulos individuales.
- **Aprendizajes**:
  - La API de MangaDex utiliza el identificador `none` para capítulos sin volumen y prefijos `S1`, `S2` para temporadas (Manhwas).
  - La consistencia entre los nombres de archivo de `mangadex-dl` (`Ch. X`) y la API permite una auditoría cruzada de alta fiabilidad.

## [2026-03-31 14:47] Sesión de Trabajo: Resiliencia de Título (Fallback UUID)

- **Objetivo**: Evitar fallos críticos (`OSError`) al intentar crear carpetas con nombres prohibidos en Windows o vacíos tras sanitización.
- **Decisiones**:
  - Implementar un **Fallback Automático**: Si el nombre sanitizado queda vacío, el script usa el `manga_uuid` como nombre de carpeta.
  - Blindar el modo manual con un bucle `while` para impedir entradas vacías por error del usuario.
  - Inyectar el autor ("MangaDex") de forma explícita si fallan todos los métodos de detección, manteniendo la compatibilidad con KCC.
- **Aprendizajes**: El uso de identificadores únicos (UUID) como red de seguridad es una práctica de "elegancia defensiva" que previene interrupciones en flujos de automatización largos sin requerir intervención manual constante.

## [2026-03-31 23:45] Sesión de Trabajo: Cloud Kindle Delivery y Seguridad E2EE

- **Objetivo**: Implementar una entrega de archivos pesados cifrada de extremo a extremo y establecer un pipeline de automatización resiliente en GitHub Actions.
- **Decisiones**:
  - Integrar `ffsend` para archivos >45MB con política de rastro cero (borrado tras 1 descarga/1 hora).
  - Implementar lógica de eficiencia "Skip-if-exists" para evitar redundancias de descarga y conversión si el `.mobi` ya está en el destino.
  - Corregir el despliegue en la nube usando mirrors de Archive.org para KindleGen e instalando KCC directamente desde GitHub para mayor estabilidad.
- **Aprendizajes**:
  - Los repositorios de binarios de KindleGen en GitHub son inestables; Archive.org es un respaldo más fiable para CI/CD.
  - El entorno "headless" de GitHub Actions requiere dependencias de sistema específicas (`libpng`, `libjpeg`) para que las librerías de imagen de KCC funcionen.

## [2026-04-21 02:00] Sesión de Trabajo: Auditoría Integral y Mejoras de Infrastructure

- **Objetivo**: Auditar el proyecto md2kindle, documentar issues pendientes e implementar mejoras de infrastructure identificadas.
- **Decisiones**:
  - Crear `requirements.txt` centralizando dependencias (`requests`, `mangadex-downloader>=1.0.0`).
  - Crear suite de tests con pytest (`tests/test_md2kindle.py`) con 17 tests cubriendo: `parse_range`, `sanitize_filename`, detección CI, `audit_and_cleanup`, y `download_manga`.
  - Resolver mismatch de `mangadex-dl` en CI: workflow ahora descarga binario localmente en lugar de usar pip (Opción A - Binario Local), y script tiene fallback CI-specific para detección de path.
  - Actualizar configuración de ffsend: `--downloads 5 --expiry 12h` (antes 1/1h) para mayor tolerancia en descargas de archivos pesados.
  - Intentando implementar progress limpo en CI con `--no-progress-bar`: falló porque mangadex-dl no reconoció el flag y ocultó todo output (incluyendo errores). Reverado.
  - Revertido cambio de binario local a pip install para mangadex-dl (el zip tiene estructura compleja que requiere ajuste de path).
  - Agregar item a `TO-DO-list.md` para refactoring de `main()` en funciones testables (postpuesto).
- **Aprendizajes**:
  - Tests vacíos con solo `print("[SKIP]")` no proveen valor. La correcta unit testing requiere mock de filesystem, environment vars, y subprocess calls.
  - El workflow de CI debe ser consistente con el uso local. Si el script espera un binario local, CI debe instalar el binario, no rely en pip package que puede cambiar.
  - pytest con `tmp_path` fixture y `monkeypatch` permiten tests de filesystem sin contaminar el entorno real.
- **Archivos Creados**:
  - `requirements.txt`
  - `tests/__init__.py`
  - `tests/test_md2kindle.py` (17 tests - 100% passing)
- **Archivos Modificados**:
  - `md2kindle.py` (líneas 23-31: CI fallback revertido; `--no-progress-bar` removido tras falla)
  - `.github/workflows/kindle-delivery.yml` (pip install restaurado)
  - `TO-DO-list.md` (item refactoring main() agregado)

## [2026-04-22 04:50] Sesión de Trabajo: Mejora de Mensajes de Telegram

- **Objetivo**: Mejorar los mensajes enviados por Telegram con información más clara y dinámica.
- **Decisiones**:
  - Crear helper `format_manga_title()` para extraer nombre del manga y volumen del path del archivo.
  - Actualizar mensajes de Telegram para mostrar "📖 **Berserk** - Vol. 39" en lugar de "📚 Manga: Vol. 39.mobi".
  - Cambiar "Bóveda Cifrada Detectada" por "🔒 Enlace seguro (archivo de X MB). Expira en 12h".
  - Corregir el texto de expiración de "se borra en 1h" a "expira en 12h" (reflejando la configuración real de ffsend).
- **Aprendizajes**:
  - `os.path.relpath()` permite obtener el path relativo desde `OUTPUT_FOLDER_KCC`, facilitando la extracción del nombre del manga.
- **Archivos Modificados**:
  - `md2kindle.py` (nueva función `format_manga_title()`, mensajes de Telegram mejorados)
  - `TO-DO-list.md` (item mensaje Telegram marcado como completado)

## [2026-04-22 05:15] Sesión de Trabajo: Metadatos de Título en MOBI

- **Objetivo**: Incluir el nombre del manga y volumen en los metadatos del archivo .mobi generado por KCC.
- **Decisiones**:
  - Modificar `convert_with_kcc()` para aceptar parámetro `title` y extraer volumen del nombre del CBZ.
  - Agregar flag `-t` a KCC con título formateado (ej: "Berserk Vol. 39").
  - Extraer volumen con regex `r"(Vol\.?\s*\d+)"` para manejar variaciones como "Vol. 39" o "Vol 39".
  - Actualizar ambas llamadas a `convert_with_kcc()` (modo volumen y modo capítulo) para pasar `p["title"]`.
- **Aprendizajes**:
  - KCC soporta flag `-t` para establecer el título del libro en los metadatos del MOBI.
  - El volumen puede extraerse del nombre del archivo CBZ usando regex para normalizar "Vol." vs "Vol".
- **Archivos Modificados**:
  - `md2kindle.py` (función `convert_with_kcc()` con parámetro `title` y flag `-t`)
  - `TO-DO-list.md` (item metadatos MOBI marcado como completado)
  