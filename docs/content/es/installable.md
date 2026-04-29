---
title: Paquetes instalables
description: Crea y usa paquetes instalables de componentes con assets
icon: images/icons/package.svg
---

Los paquetes de Python pueden incluir componentes Jx junto con sus assets CSS y/o JS. Esto te permite publicar librerías de componentes reutilizables que otros instalan con `pip` y registran con una sola línea de código.

## Usa un paquete

### Regístralo con `add_package`

```python
from jx import Catalog

catalog = Catalog(
    "components/",
    asset_resolver=my_resolver,  # se explica más abajo
)
catalog.add_package("my_ui_kit", prefix="ui")
```

A diferencia de `add_folder`, aquí el prefijo es **obligatorio**.

```html+jinja
{#import "@ui/button.jx" as Button #}
{#import "@ui/card.jx" as Card #}

<Button label="Click me" />
<Card title="Hello">Some content</Card>
```

## Resolución de assets

Los componentes dentro de un paquete normalmente declaran URLs de assets relativas al paquete:

```html+jinja title="my_ui_kit/components/button.jx"
{#css button.css #}
{#js button.js #}
{#def label #}

<button class="btn">{{ label }}</button>
```

Pero estos archivos viven en `site-packages`, no en la carpeta de archivos estáticos de tu servidor web. Un `asset_resolver` salva esa brecha transformando las URLs de los assets en el momento del renderizado.

### El callback `asset_resolver`

Pasa un callable al Catalog que reciba `(url, prefix)` y devuelva la URL accesible desde el navegador:

```python
catalog = Catalog(
    "components/",
    asset_resolver=lambda url, prefix: f"/pkg/{prefix}/{url}",
)
catalog.add_package("my_ui_kit", prefix="ui")
```

Con este resolver, `button.css` declarado en un componente `@ui/` se convierte en `/pkg/ui/button.css` en el HTML renderizado.

El resolver **solo se invoca** para componentes cuyo prefijo tiene una carpeta de assets registrada. Los componentes de carpetas regulares, aunque usen un prefijo, no se ven afectados. Esto significa que las URLs de assets de tus componentes locales pasan sin cambios.

Una desventaja es que debes agregar manualmente código para servir los assets del paquete **durante el desarrollo**. En producción, en su lugar usarías `collect_assets`.

### Ejemplo con Flask

```python
from flask import Flask, send_from_directory
from jx import Catalog

app = Flask(__name__)

catalog = Catalog(
    "components/",
    auto_reload=app.debug,
    asset_resolver=lambda url, prefix: f"/pkg/{prefix}/{url}",
)
catalog.add_package("my_ui_kit", prefix="ui")

@app.route("/pkg/<prefix>/<path:filename>")
def serve_package_assets(prefix, filename):
    assets_dir = catalog.get_assets_folder(prefix)
    if assets_dir is None:
        abort(404)
    return send_from_directory(assets_dir, filename)

```

### Ejemplo con FastAPI

```python
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from jx import Catalog

app = FastAPI()

catalog = Catalog(
    "components/",
    asset_resolver=lambda url, prefix: f"/pkg/{prefix}/{url}",
)
catalog.add_package("my_ui_kit", prefix="ui")

@app.get("/pkg/{prefix}/{filename:path}")
def serve_package_assets(prefix: str, filename: str):
    assets_dir = catalog.get_assets_folder(prefix)
    if assets_dir is None:
        raise HTTPException(404)
    return FileResponse(assets_dir / filename)
```

## Recolecta assets para producción

En producción, normalmente quieres que los archivos estáticos los sirva Nginx, una CDN o el manejador de archivos estáticos de tu framework, en lugar de una ruta de Python. El método `collect_assets` copia todos los assets de paquetes registrados a una carpeta de salida:

```python
catalog.collect_assets("static/pkg")
```

Esto copia los archivos preservando la estructura de prefijos:

```sh
static/pkg/
  ui/
    button.css
    button.js
    card.css
```

Puedes ejecutarlo como parte de tu paso de build o despliegue:

```bash
jx collect_assets myapp.setup:catalog ./static/pkg
```

Después de recolectar, actualiza tu resolver para que apunte a la ruta estática:

```python
# Producción: los assets ya están en /static/pkg/<prefix>/

def asset_resolver(url, prefix):
    if app.debug:
        return f"/pkg/{prefix}/{url}"
    return f"/static/pkg/{prefix}/{url}"


catalog = Catalog(
    "components/",
    asset_resolver=asset_resolver,
    auto_reload=False,
)
```

----

## Crea un paquete

Un paquete compatible con Jx expone dos atributos a nivel de módulo:

- **`JX_COMPONENTS`** (obligatorio): Ruta a la carpeta que contiene los archivos de componentes `.jx`.
- **`JX_ASSETS`** (opcional): Ruta a la carpeta que contiene los assets CSS/JS.

### Estructura del paquete

```sh
my_ui_kit/
  __init__.py
  components/
    button.jx
    card.jx
    modal.jx
  assets/
    button.css
    button.js
    card.css
```

### `__init__.py`

```python title="my_ui_kit/__init__.py"
from pathlib import Path

JX_COMPONENTS = Path(__file__).parent / "components"
JX_ASSETS = Path(__file__).parent / "assets"
```

### `pyproject.toml`

Asegúrate de que los archivos de componentes y assets se incluyan en la distribución:

```toml title="pyproject.toml"
[project]
name = "my-ui-kit"
version = "1.0.0"

[tool.setuptools.package-data]
my_ui_kit = ["components/*.jx", "assets/**/*"]
```

### Rutas de assets

A diferencia de los componentes locales, usa una ruta relativa a la carpeta de assets declarada:

```html+jinja title="my_ui_kit/components/card.jx"
{#css "card.css" #}
...
```

### Los componentes pueden importar a sus pares

Los componentes dentro de un paquete pueden importarse entre sí usando rutas relativas:

```html+jinja title="my_ui_kit/components/card.jx"
{#import "./button.jx" as Button #}
{#def title #}
{#css "card.css" #}

<div class="card">
  <h3>{{ title }}</h3>
  {{ content }}
  <Button label="Learn more" />
</div>
```

### Paquete sin assets

Si tu paquete solo provee componentes (sin CSS/JS), omite `JX_ASSETS`:

```python title="my_icons/__init__.py"
from pathlib import Path

JX_COMPONENTS = Path(__file__).parent / "icons"
```

El `asset_resolver` nunca se llamará para los componentes de este paquete.
