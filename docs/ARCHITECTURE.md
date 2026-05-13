# Arquitectura de md2kindle

## Capas

```text
app/           → CLI, pipeline, workflows de aplicación
core/          → config, models, exceptions, ports (interfaces/protocolos)
services/      → integraciones concretas con sistemas externos
utils/         → helpers genéricos sin dependencias internas
```

## Mapa de Módulos

```text
md2kindle/
├── app/
│   ├── cli.py               # argparse + interactive mode → PipelineContext → pipeline.run()
│   ├── context.py           # Helpers compartidos de la capa de aplicación
│   ├── pipeline.py          # Orquestador: download → audit → convert → deliver
│   └── workflows/
│       ├── volume.py        # Flujo de procesamiento por volumen
│       └── chapter.py       # Flujo de procesamiento por capítulo/rango
│
├── core/
│   ├── config/
│   │   ├── settings.py      # AppConfig dataclass, .env, constantes
│   │   └── binaries.py      # Resolución de binarios: bin/ → PATH → venv
│   ├── models/
│   │   └── pipeline.py      # PipelineContext, MangaContext, DownloadRange, DeliveryOptions
│   ├── exceptions/
│   │   ├── base.py          # Md2KindleError (raíz)
│   │   ├── config.py        # ConfigError
│   │   ├── converter.py     # ConversionError
│   │   ├── delivery.py      # DeliveryError
│   │   └── downloader.py    # DownloadError
│   ├── logging/
│   │   └── setup.py         # Configuración centralizada de logging
│   └── ports.py             # Protocolos: Converter, Deliverer
│
├── services/
│   ├── mangadex/
│   │   ├── client.py        # HTTP client para la API de MangaDex
│   │   ├── parser.py        # Parsing de respuestas JSON de la API
│   │   ├── resolver.py      # Resolución de títulos y UUIDs
│   │   ├── downloader.py    # Wrapper de mangadex-dl CLI
│   │   ├── audit.py         # Auditoría de integridad y limpieza de huérfanos
│   │   └── mixed_download.py # Descargas multi-idioma con empaquetado CBZ
│   ├── converter/
│   │   └── engine.py        # CBZ → MOBI via kcc_c2e subprocess
│   └── delivery/
│       ├── manager.py       # Orquestación: USB → R2 → Telegram → fallback
│       ├── telegram.py      # Telegram Bot API (direct upload o ffsend >45MB)
│       ├── r2.py            # Cloudflare R2 via boto3 (presigned URLs, 7 días)
│       ├── usb/             # Detección y entrega multiplataforma Kindle USB
│       │   ├── __init__.py  # Orquestador y fachada
│       │   ├── discovery.py # Detección multi-OS (Windows/Linux/macOS)
│       │   ├── mass_storage.py # Copiado por almacenamiento masivo
│       │   └── mtp.py       # Puente MTP interactivo para Windows
│       ├── ffsend.py        # Upload E2EE via ffsend binary
│       └── d1.py            # Logging de historial a Cloudflare D1
│
└── utils/
    └── ranges.py            # Parsing de rangos de volúmenes/capítulos
```

## El Corazón del Dato: `PipelineContext`

La comunicación entre capas no se hace con variables sueltas, sino a través del `PipelineContext` (en `core/models/pipeline.py`). Este objeto contiene:

- **`MangaContext`**: Metadatos del manga (título, autor, UUID).
- **`DownloadRange`**: Qué capítulos/volúmenes se deben procesar.
- **`DeliveryOptions`**: Preferencias de envío (Telegram, R2, USB).

Este contexto nace en `cli.py`, se refina en los `workflows` y es consumido por los `services`.

## Diagrama de Dependencias

```text
app → core + services
services → core
utils → (sin dependencias internas)
core → (sin dependencias internas, excepto entre subpaquetes)
```

## Convenciones Clave

- **Centralización de Config**: Todo en `AppConfig` (`core/config/settings.py`).
- **Binarios**: Cascade `./bin/` → System PATH → Venv.
- **Fallback de Idioma**: `es-la` → `en` → `es` (evaluado por capítulo).
- **Idempotencia**: Salta descarga si `.cbz` existe, salta conversión si `.mobi` existe.
- **Protocolos**: `Converter` y `Deliverer` definen las interfaces para DI.

## Estrategia de Delivery

La capa de entrega soporta múltiples rutas de salida con lógica de fallback:

- **USB**: Entrega directa a dispositivos Kindle detectados localmente.
- **Telegram Directo**: Subida del archivo `.mobi` si es menor a 45MB.
- **Cloudflare R2**: Subida persistente (S3) y entrega del link vía Telegram. Es la opción preferida para archivos pesados si está configurada.
- **ffsend Fallback**: Respaldo "Zero-Config" para archivos pesados cuando R2 no está configurado. Genera un enlace cifrado E2EE temporal.

R2 se prioriza sobre `ffsend` cuando existen credenciales. `ffsend` garantiza que archivos grandes puedan entregarse sin necesidad de configurar servicios cloud complejos.
