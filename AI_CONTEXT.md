# Contexto Técnico y Operativo para AI (mangadex-dl & KCC)

Este documento centraliza los aprendizajes técnicos y las peculiaridades del ecosistema de descarga y conversión de manga a e-readers. Ha sido concebido como un puente de contexto para futuras sesiones de inteligencia artificial o mantenimientos al script `md2kindle.py`.

## 1. El Flujo de Trabajo Teórico

El objetivo es transformar código y metadatos alojados en MangaDex hacia un archivo empaquetado optimizado para pantallas de tinta electrónica (e-ink), mitigando fricción.

[MangaDex API] -> `mangadex-dl` -> (Archivos .cbz crudos) -> `kcc_c2e` -> (Archivo Dual .mobi/.azw3) -> [Kindle]

---

## 2. Herramienta: `mangadex-dl` (Extracción)

Es un CLI robusto escrito en Python pero que solemos usar a través de su binario compilado de Windows (`mangadex-dl.exe`).

### Aprendizajes Críticos y Comportamiento

- **Identificadores**: Se nutre de UUIDs de mangas en su URL, no de nombres (ej. `mangadex.org/title/801513ba...`).
- **Empaquetado**: El argumento `--save-as cbz-volume` es altamente útil porque unifica todo un volumen en un único archivo.
- **Aislamiento Semántico**: Usa `--language es-la` (o `es`) imperativamente, ya que sin bandera de lenguaje descargará traducciones rumanas o inglesas de cada capítulo causando una sobrecarga masiva.

---

## 3. Herramienta: KCC (Kindle Comic Converter - c2e)

Para uso de scripts automáticos, utilizamos el binario `kcc_c2e.exe` *(Comic-to-ePub/Mobi)*, ignorando la GUI tradicional (`KCC.exe`).

### Aprendizajes Críticos y Banderas Relevantes

- **Dependencias Sensibles (Kindlegen)**: KCC preprocesa las imágenes excepcionalmente bien, pero la conversión generará un error fatal en el último paso si el sistema no posee el motor `kindlegen` de Amazon. En Windows basta con instalar **[Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011)** para que sus binarios internos sean autodetectados. (Aviso: Textos desactualizados suelen listar `Calibre` como requerimiento, pero iteraciones modernas han descartado esta dependencia).
- **Dual Format File**: El flag `-f MOBI` de KCC tiene un comportamiento particular. Genera un archivo `.mobi` pesado, el cual no es un MOBI estándar, sino un archivo *Master* (Dual MOBI y AZW3 simultáneo).
- **Perfiles Perfectos**: Para dispositivos potentes como el **Kindle Paperwhite 12 Signature Edition (o superior)**, el perfil óptimo de KCC es `-p KO` (Oasis/Paperwhite G11+), y no los perfiles KPW3/4 u otros más viejos, previniendo bordes vacíos y aprovechando la alta resolución (300dpi).

### Set de Banderas Ganadoras (KCC Config)

Siempre inyectar esta cadena para asegurar de que el cómic se comporte como manga premium nativo en Amazon:

- `-m` (**Manga Mode**): Revierte la lectura haciéndola de Izquierda <- Derecha. Fundamental.
- `-r 1` (**Rotate Spreads**): Analiza páginas hiper-anchas (páginas dobles donde los autores conectan dos paneles) y las gira 90 grados para que el lector del Kindle las aprecie rotando su dispositivo en vez de achicarlas rompiendo el cuadro.
- `-u` (**Upscale**): Aumenta artificialmente la resolución de mangas antiguos o subidos a baja resolución, rellenando con proporción nativa (aspect ratio) hasta chocar con el borde de la pantalla del Kindle `KO`. Minimiza los márgenes blancos.
