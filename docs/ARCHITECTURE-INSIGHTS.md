# Insights de Arquitectura — md2kindle

> Una explicación amigable de cómo está armado este proyecto por dentro,
> pensada para quien está aprendiendo mientras codea.

---

## 0. ¿Qué es la Arquitectura Hexagonal?

Imaginate un electrodoméstico — una licuadora. La licuadora tiene un **enchufe** (el puerto). Lo que hacés es conectar un **cable** (el adaptador) entre la licuadora y la pared.

La licuadora no sabe ni le importa si la electricidad viene de una usina hidroeléctrica, de paneles solares o de un generador a nafta. Solo necesita que el cable le entregue 220V con la ficha correcta.

**Eso es Arquitectura Hexagonal** (o *Ports & Adapters*):

- **Puerto** = el contrato ("necesito recibir archivos .mobi")
- **Adaptador** = la implementación concreta ("te los mando por Telegram")
- **App** = la licuadora, que solo conoce el contrato, nunca el adaptador

La magia: podés cambiar el adaptador sin tocar la app. Si mañana querés entregar por Signal en vez de Telegram, escribís un adaptador nuevo y listo.

---

## 1. Puertos & Adaptadores en md2kindle

En la vida real del proyecto, esto se ve así:

### El Puerto (el contrato)

```python
# md2kindle/core/ports.py

class Deliverer(Protocol):
    """Cualquier cosa que sepa entregar archivos .mobi"""

    def deliver(self, files: list[str], context: PipelineContext) -> None:
        """Entrega los archivos a algún destino."""
        ...
```

Fijate: no dice *cómo* se entrega. Solo dice "necesito que algo llamado `Deliverer` tenga un método `deliver`". Eso es el **puerto**.

### El Adaptador (la implementación concreta)

```python
# md2kindle/services/delivery/manager.py

class DeliveryManager:
    """Sabe entregar por USB, Telegram, R2, o preguntarle al usuario."""

    def deliver(self, files, context):
        # Intenta USB → si no, Telegram → si no, R2 → si no, interactivo
        ...
```

`DeliveryManager` **cumple el contrato** de `Deliverer`. Tiene el método `deliver` con la firma esperada. El pipeline solo sabe que existe un `Deliverer`; nunca sabe si es `DeliveryManager`, `MockDeliverer` o `FuturoSignalDeliverer`.

### ¿Por qué importa?

- **Testear es fácil**: le pasás un `Deliverer` falso que no hace nada y verificás que el pipeline lo llamó correctamente.
- **Cambiar es seguro**: si mañana agregás WhatsApp, no tocás `pipeline.py`. Solo creás un adaptador nuevo.
- **El código no se acopla**: `pipeline.py` no importa `DeliveryManager`. Solo importa `Deliverer`.

---

## 2. Inyección de Dependencias (sin frameworks ni magia)

Acá no hay ningún framework de DI. Es simplemente pasar cosas por parámetro.

```python
# md2kindle/app/pipeline.py

def run(
    params: PipelineContext,
    converter: Converter | None = None,   # ← parámetro opcional
    deliverer: Deliverer | None = None,   # ← parámetro opcional
) -> None:
    converter = converter or KccConverter(app_config)  # default sensato
    deliverer = deliverer or DeliveryManager(app_config)
```

**¿Qué pasa acá?**
1. Si el que llama **no pasa nada**, se usan los defaults (`KccConverter`, `DeliveryManager`).
2. Si el que llama **pasa un mock** (ej: para tests), se usa el mock.
3. El código de producción sigue siendo simple (no necesita configurar nada).

**¿Por qué importa?** Porque podés testear el pipeline completo sin depender de internet, de KCC, ni de un Kindle conectado. Le pasás adaptadores falsos y listo.

---

## 3. Configuración Inmutable (frozen dataclass)

```python
# md2kindle/core/config/settings.py

@dataclass(frozen=True)
class AppConfig:
    root_dir: str
    output_folder_manga: str
    kcc_profile: str = "KO"
    kcc_format: str = "MOBI"
    telegram_bot_token: str | None = None
    ...
```

**`frozen=True`** significa que una vez creado, **no se puede modificar**. Si intentás hacer `config.kcc_format = "EPUB"`, Python tira error.

Las credenciales se cargan **una sola vez** al inicio desde el archivo `.env`:

```python
def load_config() -> AppConfig:
    return AppConfig(
        telegram_bot_token=os.environ.get("TELEGRAM_TOKEN"),
        ...
    )
```

**¿Por qué importa?** Dos razones:
1. **Seguridad**: nadie modifica accidentalmente un token o una ruta en medio de la ejecución.
2. **Predictibilidad**: en cualquier parte del código, `app_config` siempre tiene los mismos valores. Cero sorpresas.

---

## 4. PipelineContext: Un "sobre" con todo adentro

En vez de pasar 15 parámetros sueltos por todos lados, el proyecto usa **un solo objeto** que contiene todo:

```python
# md2kindle/core/models/pipeline.py

@dataclass
class PipelineContext:
    manga: MangaContext        # título, autor, idioma, UUID
    range: DownloadRange       # qué capítulos/volúmenes bajar
    delivery: DeliveryOptions  # ¿mando por Telegram? ¿R2?
    sync: bool = False
    silent: bool = False
```

Cada campo es a su vez otro dataclass:

```python
MangaContext   →  url, title, lang, author, manga_uuid
DownloadRange  →  mode ("v"/"c"), start, end, skip_oneshots
DeliveryOptions → telegram (bool), r2 (bool)
```

**¿Por qué importa?**
- **Una sola fuente de verdad**: si necesitás el título del manga, sabés que está en `context.manga.title`.
- **No se desparraman parámetros**: todas las funciones reciben `context` y extraen lo que necesitan.
- **Fácil de extender**: ¿nuevo campo? Lo agregás al dataclass y listo.

El flujo es: `cli.py` arma el `PipelineContext` → `pipeline.py` lo usa → `workflows` lo consumen → `services` reciben lo que necesitan.

---

## 5. Errores con Nombre y Apellido

El proyecto tiene una jerarquía de excepciones propia:

```
MD2KindleError            ← el abuelo (hereda de Exception)
├── ConfigurationError    ← error de configuración
├── DownloadError         ← falló la descarga de MangaDex
├── ConversionError       ← falló KCC
└── DeliveryError         ← falló el envío (USB, Telegram, R2)
```

**¿Por qué importa?**
- Podés **atrapar errores por capa**: `except DownloadError` solo agarra problemas de descarga, dejando pasar otros.
- El mensaje de error es **específico**: "Fallo crítico en KCC" vs un genérico "algo salió mal".
- Si un día querés reintentar descargas pero no conversiones, filtrás por tipo de excepción.

---

## 6. Fallback de Idioma Granular (por capítulo)

Este es uno de los features más inteligentes del proyecto. No es un fallback global de "si no hay español, bajá todo en inglés". Es **por capítulo**.

### ¿Cómo funciona?

```python
# md2kindle/app/pipeline.py

lang_priority = ["es-la", "en", "es"]  # orden de preferencia

# Para cada volumen, se arma un mapa: capítulo → idioma disponible
chapter_map = {
    "5": "es-la",   # el cap 5 está en español
    "6": "en",      # el cap 6 solo existe en inglés
    "7": "es-la",   # el cap 7 está en español
}
```

Si un volumen tiene capítulos en varios idiomas, `download_volume_mixed()` baja cada capítulo en su mejor idioma disponible. El resultado es un solo CBZ con la máxima cobertura en tu idioma preferido.

**¿Por qué importa?** Porque no te quedás sin un volumen entero solo porque **un** capítulo no está traducido. Bajás lo que existe en español y el resto en inglés.

---

## 7. Cadena de Entrega (Delivery Chain)

La entrega de archivos `.mobi` sigue un orden de prioridad bien definido:

```
1. USB (siempre se intenta primero — es lo más directo)
   ↓ si no hay Kindle conectado
2. Cloudflare R2 (si se pasó --r2 o está configurado)
   ↓ si no está configurado R2
3. Telegram directo (si se pasó --telegram)
   ↓ si nada de lo anterior
4. Modo interactivo (le pregunta al usuario qué hacer)
```

En código:

```python
# md2kindle/services/delivery/manager.py

def deliver_files(mobi_files, params):
    # 1. Intentar USB
    if send_to_usb(mobi_files, ...):
        return  # éxito, no seguimos

    # 2. Si el usuario pidió R2
    if params.delivery.r2:
        for f in mobi_files:
            _deliver_via_r2(f, ...)
        return

    # 3. Si el usuario pidió Telegram
    if params.delivery.telegram:
        for f in mobi_files:
            _deliver_via_telegram(f, ...)
        return

    # 4. Modo interactivo (preguntar)
    ...
```

R2 además tiene un **sub-fallback**: si la subida a R2 falla, automáticamente intenta Telegram directo.

**¿Por qué importa?** Porque el usuario no tiene que pensar en qué método usar. El sistema prueba las opciones en orden de conveniencia y solo pregunta cuando no le queda otra.

---

## 8. Resolución de Binarios en Cascada

El proyecto necesita tres herramientas externas: `mangadex-dl`, `kcc-c2e` y `ffsend`. Para encontrarlas, sigue esta cascada:

```
1. ./bin/          ← buscá en la carpeta bin del proyecto
   ↓ si no está
2. PATH del sistema ← buscá con shutil.which()
   ↓ si no está
3. Comando desnudo  ← usá el nombre del comando pelado
```

En Windows hay una rama especial: **prefiere los `.exe` de `./bin/`** sobre el PATH:

```python
# md2kindle/core/config/binaries.py

mangadex_dl = (
    mangadex_local                          # .exe local
    if mangadex_local and os_name == "nt"   # solo si es Windows
    else shutil.which("mangadex-dl") or "mangadex-dl"  # sino, PATH
)
```

**¿Por qué importa?**
- En **desarrollo**: ponés los binarios en `./bin/` y listo. No contaminás el sistema.
- En **CI**: los binarios se instalan en el PATH del runner.
- En **Windows**: usás los `.exe` locales sin depender de variables de entorno.

---

## 9. Idempotencia: Correlo 10 Veces, No Rompe Nada

"Idempotente" es una palabra fancy para decir "podés ejecutarlo mil veces y el resultado es el mismo". El pipeline aplica esto en **tres niveles**:

### Nivel 1: ¿Ya existe el MOBI? → Salteá todo

```python
# md2kindle/app/workflows/volume.py

existing_mobis = glob.glob(os.path.join(output_dir, "*.mobi"))
if existing_mobis:
    logger.info("MOBI ya existe. Saltando...")
    return [existing_mobis[0]]
```

Si el archivo final ya está generado, no se descarga ni se convierte nada.

### Nivel 2: ¿Ya existe el CBZ? → Salteá la descarga

```python
existing_cbzs = glob.glob(os.path.join(folder, "*.cbz"))
if existing_cbzs:
    logger.info("CBZ ya presente. Saltando descarga...")
else:
    download_manga(...)  # solo descarga si no hay CBZ
```

Si los archivos fuente ya están, solo se hace la conversión.

### Nivel 3: Solo descargá/converí lo necesario

El pipeline nunca re-descarga un capítulo que ya tiene, ni re-convierte un volumen que ya procesó.

**¿Por qué importa?** Porque si se corta la luz a mitad del proceso, volvés a correr el comando y continúa exactamente donde se quedó. Sin re-hacer trabajo.

---

## 10. CLI y Pipeline: Separados al Nacer

Este es un principio clásico de diseño: **Single Responsibility** (cada cosa hace una sola cosa).

```
cli.py        → "Hablo con el usuario y armo los parámetros"
pipeline.py   → "Ejecuto el proceso con los parámetros que me dieron"
```

**`cli.py` solo hace parsing.** No sabe nada de descargas, conversiones ni entregas:

```python
def resolve_parameters() -> PipelineContext:
    """Arma el PipelineContext desde args de CLI o modo interactivo."""
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    # ... resuelve título, idioma, rango ...
    return PipelineContext(
        manga=MangaContext(url=...),
        range=DownloadRange(mode=...),
        ...
    )
```

**`pipeline.py` solo orquesta.** No sabe nada de argparse ni de input del usuario:

```python
def run(params: PipelineContext):
    """Ejecuta el pipeline con parámetros ya resueltos."""
    for vol in volumes:
        generated = process_volume_flow(params, vol, ...)
    deliverer.deliver(all_mobi_files, params)
```

**¿Por qué importa?**
- **Probás el pipeline sin CLI**: llamás `run()` directamente con un `PipelineContext` armado a mano.
- **Cambiás la CLI sin romper nada**: si mañana usás Click o Typer en vez de argparse, `pipeline.py` ni se entera.
- **Reutilizás la lógica**: un worker de CI, un bot de Telegram o una interfaz web pueden llamar a `run()` sin pasar por la CLI.

---

## 11. Trucos de Importación: TYPE_CHECKING

En `core/ports.py` hay un detalle sutil:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from md2kindle.core.models import PipelineContext
```

**¿Qué hace esto?** `TYPE_CHECKING` es `True` solo cuando el type checker (mypy, pyright, tu IDE) está analizando el código. En tiempo de ejecución es `False`.

Esto evita un **import circular**: `ports.py` necesita `PipelineContext` para type hints, y `PipelineContext` está en `models/`, que a su vez podría necesitar algo de `ports.py`. Con `TYPE_CHECKING`, el import solo existe para el analizador de tipos, no en ejecución.

**¿Por qué importa?** Porque permite tener type hints precisos sin crear dependencias circulares que rompan el código. El IDE te muestra los tipos correctos, pero Python no se enreda al cargar los módulos.

---

## 12. El Patrón config_kwargs

En `app/context.py` hay una función chiquita pero importante:

```python
def config_kwargs(explicit_config: bool, app_config: AppConfig) -> dict:
    """Pasa AppConfig solo cuando el caller lo inyectó explícitamente."""
    return {"app_config": app_config} if explicit_config else {}
```

Y se usa así en los workflows:

```python
def process_volume_flow(params, ..., app_config: AppConfig | None = None):
    explicit_config = app_config is not None
    app_config = app_config or APP_CONFIG
    config_kwargs = _config_kwargs(explicit_config, app_config)

    download_manga(url, folder, ..., **config_kwargs)
    # ↑ solo pasa "app_config" si vino explícitamente
```

**¿Qué resuelve esto?** Dos escenarios distintos:

| Escenario | `explicit_config` | ¿Pasa app_config a services? |
|-----------|-------------------|------------------------------|
| Producción | `False` (usa `APP_CONFIG` global) | No — las funciones usan su propio `APP_CONFIG` por defecto |
| Tests | `True` (inyectó un config de prueba) | Sí — para que el test controle la configuración |

**¿Por qué importa?** Porque permite migrar gradualmente de una arquitectura con variable global (`APP_CONFIG`) a inyección de dependencias, sin romper el código existente. Las funciones viejas que no esperan `app_config` simplemente no lo reciben.

---

## Resumen Visual

```
┌─────────────────────────────────────────────────────────┐
│  cli.py                                                 │
│  "Hablo con el usuario"                                 │
│  argparse / modo interactivo → PipelineContext           │
└──────────────────────┬──────────────────────────────────┘
                       │ PipelineContext (el "sobre")
                       ▼
┌─────────────────────────────────────────────────────────┐
│  pipeline.py                                            │
│  "Orquesto el proceso"                                  │
│  download → audit → convert → deliver                   │
│                                                         │
│  Recibe:  converter: Converter  ← el puerto             │
│           deliverer: Deliverer ← el puerto              │
│  (inyectados por parámetro, con defaults sensatos)      │
└──────┬──────────────────────────────────┬───────────────┘
       │                                  │
       ▼                                  ▼
┌──────────────────┐          ┌──────────────────────────┐
│ services/converter│          │ services/delivery        │
│ KccConverter     │          │ DeliveryManager          │
│ (CBZ → MOBI)     │          │ (USB → R2 → Telegram)    │
│                  │          │                          │
│ ADAPTADOR para   │          │ ADAPTADOR para           │
│ puerto Converter │          │ puerto Deliverer         │
└──────────────────┘          └──────────────────────────┘

Todo cableado sin frameworks: solo Protocol, dataclasses,
funciones con defaults, y un AppConfig frozen.
```

---

## Lo que aprendiste

Si entendiste estos 12 puntos, ya tenés una base sólida de arquitectura de software:

- **Puertos y Adaptadores** no es magia: son protocolos e implementaciones.
- **Inyección de Dependencias** no necesita un framework: pasá las cosas por parámetro.
- **Inmutabilidad** (`frozen=True`) previene bugs por modificación accidental.
- **DTOs** (como `PipelineContext`) organizan los datos en vez de desparramar parámetros.
- **Idempotencia** hace que tu programa sea seguro de re-ejecutar.
- **Separación de responsabilidades** (`cli.py` vs `pipeline.py`) hace el código mantenible.

Este proyecto es un excelente ejemplo de cómo aplicar estos patrones en Python **sin sobre-ingeniería**. Todo es estándar: `dataclass`, `Protocol`, funciones, sin frameworks externos.
