---
title: Catálogo
description: Configuración y uso del Catálogo de Jx
---

El `Catalog` es el gestor central de tus componentes. Se encarga de cargar, cachear y renderizar componentes desde una o más carpetas.

## Configuración básica

```python
from jx import Catalog

catalog = Catalog("components/")
```

Esto crea un catálogo que carga componentes desde la carpeta `components/`.

## Opciones del constructor

```python
catalog = Catalog(
    folder="components/",       # Carpeta inicial opcional
    jinja_env=None,             # Entorno Jinja2 personalizado
    extensions=None,            # Extensiones Jinja2 adicionales
    filters=None,               # Filtros de plantilla personalizados
    tests=None,                 # Tests de plantilla personalizados
    auto_reload=True,           # Detecta cambios en archivos automáticamente
    asset_resolver=None,        # Callback que resuelve URLs de assets
    file_ext=".jx",             # Extensión de archivo de los componentes
    **globals                   # Variables globales de plantilla
)
```

### `folder`

Ruta opcional a una carpeta de componentes. Atajo para llamar a `add_folder()`:

```python
# Estas formas son equivalentes:
catalog = Catalog("components/")

catalog = Catalog()
catalog.add_folder("components/")
```

### `file_ext`

La extensión que usa Jx para descubrir archivos de componentes. Por defecto es `.jx`.

Cámbiala para mantener una convención distinta (por ejemplo `.jinja` para proyectos antiguos):

```python
catalog = Catalog("components/", file_ext=".jinja")
```

### `auto_reload`

Cuando es `True` (valor por defecto), Jx revisa si los archivos de componentes han cambiado y los recarga automáticamente. Ideal para desarrollo.

Para producción, configúralo como `False` para omitir las verificaciones de modificación de archivos:

```python
catalog = Catalog("components/", auto_reload=False)
```

### `globals`

Variables disponibles para todos los componentes:

```python
catalog = Catalog(
    "components/",
    site_name="My App",
    current_year=2026,
    debug=True,
)
```

```html+jinja title="components/footer.jx"
<footer>
  © {{ current_year }} {{ site_name }}
</footer>
```

### `filters`

Filtros Jinja2 personalizados:

```python
def format_price(value):
    return f"${value:,.2f}"

def pluralize(count, singular, plural=None):
    plural = plural or f"{singular}s"
    return singular if count == 1 else plural

catalog = Catalog(
    "components/",
    filters={
        "price": format_price,
        "pluralize": pluralize,
    }
)
```

```html+jinja
<span>{{ product.price | price }}</span>
<span>{{ count }} {{ count | pluralize("item") }}</span>
```

### `tests`

Tests Jinja2 personalizados:

```python
def is_admin(user):
    return user.role == "admin"

catalog = Catalog(
    "components/",
    tests={"admin": is_admin}
)
```

```html+jinja
{% if user is admin %}
  <a href="/admin">Admin Panel</a>
{% endif %}
```

### `extensions`

Extensiones Jinja2 adicionales para cargar:

```python
catalog = Catalog(
    "components/",
    extensions=["jinja2.ext.i18n", "jinja2.ext.loopcontrols"]
)
```

Nota: La extensión `jinja2.ext.do` siempre está habilitada (es necesaria para la manipulación de `attrs`).

### `jinja_env`

Usa un entorno Jinja2 existente en lugar de crear uno nuevo:

```python
from jinja2 import Environment

env = Environment()
env.globals["my_func"] = my_function
env.filters["my_filter"] = my_filter

catalog = Catalog("components/", jinja_env=env)
```

Esto resulta útil al integrarse con frameworks que proveen su propio entorno Jinja.

### `asset_resolver`

Callback opcional para transformar las URLs de assets de los componentes. Recibe `(url, prefix)` y devuelve la cadena de URL resuelta. Solo se invoca para componentes cuyo prefijo tiene una carpeta `assets` registrada (consulta `add_folder`).

```python
def my_resolver(url, prefix):
    return f"/static/{prefix}/{url}"

catalog = Catalog("components/", asset_resolver=my_resolver)
```

---

## Agrega carpetas

### `add_folder(path, prefix="", assets=None)`

Agrega una carpeta de componentes al catálogo:

```python
catalog = Catalog()
catalog.add_folder("components/")
catalog.add_folder("layouts/")
```

El parámetro opcional `assets` especifica una carpeta que contiene archivos CSS/JS para los componentes de esta carpeta. Cuando se establece, el callback `asset_resolver` se usa para transformar las URLs de assets en el momento del renderizado (ver [Paquetes instalables](/docs/installable/) para más detalles).

Los componentes se importan por su ruta relativa a la carpeta:

```html+jinja
{#import "button.jx" as Button #}
{#import "forms/input.jx" as Input #}
```

### Uso de prefijos

Los prefijos crean un espacio de nombres para los componentes, útil para librerías de terceros:

```python
catalog.add_folder("components/")
catalog.add_folder("vendor/ui-kit/", prefix="ui")
catalog.add_folder("vendor/icons/", prefix="icons")
```

Importa componentes con prefijo usando `@prefix/`:

```html+jinja
{#import "button.jx" as Button #}
{#import "@ui/modal.jx" as Modal #}
{#import "@icons/check.jx" as CheckIcon #}
```

### Múltiples carpetas, mismo prefijo

Si agregas varias carpetas con el mismo prefijo (o sin prefijo), se tratan como un único espacio de nombres. Si ambas contienen un componente con la misma ruta, **gana la primera que se agregó**:

```python
catalog.add_folder("my-components/")      # Tiene button.jx
catalog.add_folder("fallback-components/") # También tiene button.jx

# "button.jx" se resuelve a my-components/button.jx
```

---

## Renderizado

### `render(relpath, globals=None, **kwargs)`

Renderiza un componente por su ruta:

```python
html = catalog.render("page.jx", title="Hello", user=current_user)
```

**Argumentos:**

- `relpath` - Ruta al componente (por ejemplo, `"pages/home.jx"`)
- `globals` - Diccionario de variables disponibles para este componente y todas sus importaciones
- `**kwargs` - Argumentos pasados directamente al componente

```python
# Pasa datos como argumentos por nombre
html = catalog.render(
    "user-profile.jx",
    user=user,
    posts=posts,
    show_email=True,
)

# O usa globals para valores que también necesitan los componentes hijos
html = catalog.render(
    "page.jx",
    globals={"request": request, "csrf_token": token},
    title="Dashboard",
)
```

### `render_string(source, globals=None, **kwargs)`

Renderiza un componente desde una cadena (no desde un archivo):

```python
source = """
{#def name #}
<h1>Hello, {{ name }}!</h1>
"""

html = catalog.render_string(source, name="World")
# <h1>Hello, World!</h1>
```

Útil para:

- Probar componentes
- Plantillas dinámicas almacenadas en una base de datos
- Renderizados puntuales sencillos

Nota: Los componentes desde cadenas pueden usar importaciones absolutas pero no relativas (no hay una ruta de archivo desde la cual resolver).

---

## Introspección

### `list_components()`

Devuelve una lista con todas las rutas de componentes registrados:

```python
paths = catalog.list_components()
# ["button.jx", "card.jx", "forms/input.jx"]
```

### `get_signature(relpath)`

Devuelve la firma de un componente, incluyendo sus argumentos y metadatos:

```python
sig = catalog.get_signature("button.jx")
```

Devuelve un diccionario con:

- `required` - diccionario con los nombres de argumentos requeridos asociados a su tipo (o `None`)
- `optional` - diccionario con los argumentos opcionales asociados a `(default_value, type or None)`
- `slots` - tupla de nombres de slots
- `css` - tupla de URLs de archivos CSS
- `js` - tupla de URLs de archivos JS

```python
sig = catalog.get_signature("modal.jx")
# {
#     "required": {"title": str},
#     "optional": {"size": ("md", str)},
#     "slots": ("header", "footer"),
#     "css": ("modal.css",),
#     "js": ("modal.js",),
# }
```

### `collect_assets(output)`

Copia todos los assets de paquetes registrados a una carpeta de salida. Para cada prefijo que tiene una carpeta de assets registrada (ver `add_folder`), los archivos se copian a `<output>/<prefix>/`:

```python
copied = catalog.collect_assets("static/vendor")
# [("ui", Path("button.css")), ("ui", Path("button.js")), ...]
```

Devuelve una lista de tuplas `(prefix, relative_path)` por cada archivo copiado.

---

## Integración con frameworks

### Flask

```python
from flask import Flask, url_for
from jx import Catalog

app = Flask(__name__)
catalog = Catalog(
    "components/",
    auto_reload=app.debug,
    url_for=url_for,  # Hace url_for disponible en los componentes
)

@app.route("/")
def home():
    return catalog.render("pages/home.jx", products=get_products())
```

### FastAPI

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jx import Catalog

app = FastAPI()
catalog = Catalog("components/", auto_reload=True)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return catalog.render(
        "pages/home.jx",
        globals={"request": request},
        products=get_products(),
    )
```

### Comparte el entorno Jinja

Si tu framework tiene su propio entorno Jinja con filtros, globals, etc., pásalo al catálogo:

```python
# Ejemplo con Flask
from flask import Flask

app = Flask(__name__)
app.jinja_env.filters["my_filter"] = my_filter
app.jinja_env.globals["my_global"] = my_global

catalog = Catalog("components/", jinja_env=app.jinja_env)
```

Ahora tus componentes tienen acceso a todo lo registrado en el entorno de Flask.

---

## Configuración para producción

Para producción, desactiva la recarga automática.

```python
import os

catalog = Catalog(
    "components/",
    auto_reload=os.environ.get("DEBUG", "false").lower() == "true",
)
```

O basándote en la configuración de debug de tu framework:

```python
# Flask
catalog = Catalog("components/", auto_reload=app.debug)

# FastAPI
catalog = Catalog("components/", auto_reload=settings.debug)
```

---

## Globals de plantilla integrados

Además de cualquier global que pases al constructor, Jx provee automáticamente estas funciones a todos los componentes:

### `_get_random_id(prefix="id")`

Genera una cadena única apta para IDs de elementos HTML. Útil para elementos de formulario, popovers y otros componentes que requieren IDs únicos para funcionar correctamente:

```html+jinja title="components/popover.jx"
{#def label, content #}

{% set popover_id = _get_random_id("popover") %}

<button popovertarget="{{ popover_id }}">{{ label }}</button>
<div id="{{ popover_id }}" popover>{{ content }}</div>
```

Cada llamada devuelve un ID distinto como `popover-a1b2c3d4e5f6...`, así que puedes usarlo como valor por defecto sin requerir que quien llama pase un ID explícito:

```html+jinja title="components/input.jx"
{#def name, label="", id="" #}

{% set input_id = id or _get_random_id(name) %}

{% if label %}
  <label for="{{ input_id }}">{{ label }}</label>
{% endif %}
<input id="{{ input_id }}" name="{{ name }}" {{ attrs.render() }} />
```
