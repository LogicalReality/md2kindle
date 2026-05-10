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
│       ├── usb.py           # Detección multiplataforma de Kindle USB
│       ├── ffsend.py        # Upload E2EE via ffsend binary
│       └── d1.py            # Logging de historial a Cloudflare D1
│
└── utils/
    └── ranges.py            # Parsing de rangos de volúmenes/capítulos
```

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
