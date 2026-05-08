# 🧠 Entendiendo md2kindle (Guía Táctica)

Esta guía explica las "complejidades" del proyecto de forma sencilla. Si te perdés entre tanto código, este es tu mapa.

---

## 1. El Gran Flujo (El Pipeline) 🎼

`md2kindle` no es un solo script, es una **fábrica**. Todo pasa por `app/pipeline.py`, que coordina tres estaciones de trabajo:

| Estación | Archivo Responsable | ¿Qué hace? |
| :--- | :--- | :--- |
| **1. La Mina** | `services/mangadex/downloader.py` | Busca el manga, gestiona idiomas y descarga imágenes en `.cbz`. |
| **2. La Forja** | `services/converter/service.py` | Llama a KCC para transformar fotos en un libro que el Kindle entienda. |
| **3. El Correo** | `services/delivery/service.py` | Decide si el archivo va por Telegram, R2 o ffsend según el tamaño. |

---

## 2. El Cerebro: `AppConfig` ⚙️

Para que la fábrica funcione, necesita instrucciones claras. Antes estaban sueltas, ahora viven en un objeto llamado `AppConfig` (en `core/config/settings.py`):

- **Inyectable**: Podemos crear una configuración "de mentira" para tests sin romper la configuración real.
- **Inmutable**: Una vez que arranca, nadie puede cambiar la ruta de descarga a mitad de camino.
- **Detección Automática**: Sabe si estás en GitHub Actions (CI) o en tu PC y ajusta los logs y rutas solo.

---

## 3. La Búsqueda de Herramientas (Binary Resolution) 🔍

Este es uno de los puntos más "complejos". El script necesita herramientas externas (`mangadex-dl`, `kcc`, `kindlegen`).

**¿Cómo las encuentra?** (Capa de Infraestructura):

1. Mira en la carpeta `./bin/` (Prioridad máxima, ideal para portables).
2. Si no están ahí, le pregunta al Sistema Operativo (PATH).
3. Si hay varias versiones (ej: `kcc_9.6.exe` y `kcc_10.1.exe`), **siempre elige la más nueva** gracias a una lógica de ordenamiento inteligente.

---

## 4. El "Secret Sauce": Fallback de Idiomas 🌐

MangaDex es caótico. A veces el capítulo 1 está en español, pero el 2 solo en inglés.
El script hace algo llamado **Granular Fallback**:

1. El usuario pide `es-la` (Español Latino).
2. El script revisa capítulo por capítulo.
3. ¿Falta el cap 5 en latino? Lo busca en `es` (España). ¿Sigue faltando? Lo busca en `en` (Inglés).
4. Al final, te entrega un tomo completo mezclando idiomas si es necesario para que no te falte ninguna página.

---

## 5. El Sandbox y los Permisos 🛡️

Si corrés esto en entornos restringidos (como este chat o GitHub Actions):

- **Regla de Oro**: Nunca usamos `os.chmod`. Windows y los Sandboxes odian que toquemos permisos manualmente.
- **Mocks en Tests**: En lugar de crear carpetas reales que luego no se pueden borrar, usamos "carpetas de mentira" (Mocks) en los tests para verificar que el código funciona sin ensuciar el disco.

---

## 6. ¿Dónde toco si quiero...? 🛠️

- **¿Cambiar cómo se ve el mobi?** -> `core/config/settings.py` (ajusta `KCC_PROFILE` o `KCC_CUSTOM_ARGS`).
- **¿Agregar un nuevo método de envío?** -> Crea un archivo en `services/delivery/` y registralo en `services/delivery/service.py`.
- **¿Mejorar la descarga?** -> `services/mangadex/downloader.py`.

---

> [!TIP]
> **Resumen para humanos**: El código está diseñado para que el "qué hacer" (Pipeline) esté separado del "cómo se hace" (Infrastructure) y del "con qué datos" (Models).
