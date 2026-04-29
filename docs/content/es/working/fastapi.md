---
title: Trabaja con FastAPI
description: Integra componentes Jx con aplicaciones FastAPI
---

[FastAPI](https://fastapi.tiangolo.com/){target=_blank} es un framework web moderno y de alto rendimiento para Python. Jx se integra de forma limpia con FastAPI para aplicaciones HTML renderizadas en el servidor, especialmente cuando se combina con htmx.

## Configuración básica

```python title="app.py"
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from jx import Catalog

app = FastAPI()
catalog = Catalog("components/", auto_reload=True)


@app.get("/", response_class=HTMLResponse)
def home():
    return catalog.render("pages/home.jx")
```

## Pasa el contexto de la petición

Usa la inyección de dependencias de FastAPI para pasar datos de la petición a los componentes:

```python title="app.py"
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
    )
```

## Crea un helper de renderizado

Simplifica el renderizado con una función auxiliar:

```python title="app.py"
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jx import Catalog

app = FastAPI()
catalog = Catalog("components/", auto_reload=True)


def render(request: Request, component: str, status_code: int = 200, **context):
    """Renderiza un componente Jx con el contexto de la petición."""
    html = catalog.render(
        component,
        globals={"request": request},
        **context,
    )
    return HTMLResponse(html, status_code=status_code)


@app.get("/")
def home(request: Request):
    return render(request, "pages/home.jx")


@app.get("/products")
def products(request: Request):
    products = get_products()
    return render(request, "pages/products.jx", products=products)
```

## Usa inyección de dependencias

Para un código más limpio, crea una dependencia que provea la función de renderizado:

```python title="dependencies.py"
from fastapi import Request
from fastapi.responses import HTMLResponse
from jx import Catalog

catalog = Catalog("components/", auto_reload=True)


class Templates:
    def __init__(self, request: Request):
        self.request = request

    def render(self, component: str, status_code: int = 200, **context):
        html = catalog.render(
            component,
            globals={"request": self.request},
            **context,
        )
        return HTMLResponse(html, status_code=status_code)
```

```python title="app.py"
from fastapi import FastAPI, Depends
from dependencies import Templates

app = FastAPI()


@app.get("/")
def home(templates: Templates = Depends()):
    return templates.render("pages/home.jx")


@app.get("/products/{product_id}")
def product_detail(product_id: int, templates: Templates = Depends()):
    product = get_product(product_id)
    return templates.render("pages/product.jx", product=product)
```

## Generación de URLs

FastAPI no tiene un `url_for` integrado como Flask. Usa `request.url_for()`:

```python title="dependencies.py"
class Templates:
    def __init__(self, request: Request):
        self.request = request

    def render(self, component: str, status_code: int = 200, **context):
        html = catalog.render(
            component,
            globals={
                "request": self.request,
                "url_for": self.request.url_for,
            },
            **context,
        )
        return HTMLResponse(html, status_code=status_code)
```

```html+jinja title="components/nav.jx"
<nav>
  <a href="{{ url_for('home') }}">Home</a>
  <a href="{{ url_for('products') }}">Products</a>
  <a href="{{ url_for('about') }}">About</a>
</nav>
```

Asegúrate de que tus rutas tengan nombres:

```python title="app.py"
@app.get("/", name="home")
def home(templates: Templates = Depends()):
    return templates.render("pages/home.jx")


@app.get("/products", name="products")
def products(templates: Templates = Depends()):
    return templates.render("pages/products.jx")
```

## Archivos estáticos

Monta una carpeta de archivos estáticos y crea un helper:

```python title="app.py"
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
```

```python title="dependencies.py"
class Templates:
    def __init__(self, request: Request):
        self.request = request

    def render(self, component: str, status_code: int = 200, **context):
        def static(path: str) -> str:
            return self.request.url_for("static", path=path)

        html = catalog.render(
            component,
            globals={
                "request": self.request,
                "url_for": self.request.url_for,
                "static": static,
            },
            **context,
        )
        return HTMLResponse(html, status_code=status_code)
```

```html+jinja title="components/layout.jx"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  <link rel="icon" href="{{ static('favicon.ico') }}">
  {% for css in assets.collect_css() %}
    <link rel="stylesheet" href="{{ static(css) }}">
  {% endfor %}
</head>
<body>
  {{ content }}
  {% for js in assets.collect_js() %}
    <script type="module" src="{{ static(js) }}"></script>
  {% endfor %}
</body>
</html>
```

## Mensajes flash

FastAPI no incluye mensajes flash. Aquí tienes una implementación simple basada en sesiones:

```python title="flash.py"
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request


def flash(request: Request, message: str, category: str = "info"):
    """Agrega un mensaje flash a la sesión."""
    if "_flashes" not in request.session:
        request.session["_flashes"] = []
    request.session["_flashes"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    """Obtiene y limpia los mensajes flash de la sesión."""
    messages = request.session.pop("_flashes", [])
    return messages
```

```python title="app.py"
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
```

```python title="dependencies.py"
from flash import get_flashed_messages


class Templates:
    def __init__(self, request: Request):
        self.request = request

    def render(self, component: str, status_code: int = 200, **context):
        html = catalog.render(
            component,
            globals={
                "request": self.request,
                "url_for": self.request.url_for,
                "messages": get_flashed_messages(self.request),
            },
            **context,
        )
        return HTMLResponse(html, status_code=status_code)
```

```html+jinja title="components/messages.jx"
{#css messages.css #}

{% if messages %}
  <div class="messages">
    {% for msg in messages %}
      <div class="message message-{{ msg.category }}">
        {{ msg.message }}
      </div>
    {% endfor %}
  </div>
{% endif %}
```

```python title="views.py"
from fastapi import Depends
from fastapi.responses import RedirectResponse
from flash import flash


@app.post("/items")
def create_item(request: Request, templates: Templates = Depends()):
    # ... crear item ...
    flash(request, "Item created successfully!", "success")
    return RedirectResponse(url="/items", status_code=303)
```

## Autenticación

Intégralo con tu sistema de autenticación:

```python title="dependencies.py"
from fastapi import Request, Depends
from auth import get_current_user  # Tu implementación de autenticación


class Templates:
    def __init__(self, request: Request, user = Depends(get_current_user)):
        self.request = request
        self.user = user

    def render(self, component: str, status_code: int = 200, **context):
        html = catalog.render(
            component,
            globals={
                "request": self.request,
                "url_for": self.request.url_for,
                "user": self.user,
            },
            **context,
        )
        return HTMLResponse(html, status_code=status_code)
```

```html+jinja title="components/nav.jx"
<nav>
  <a href="{{ url_for('home') }}">Home</a>

  {% if user %}
    <span>{{ user.email }}</span>
    <a href="{{ url_for('logout') }}">Logout</a>
  {% else %}
    <a href="{{ url_for('login') }}">Login</a>
  {% endif %}
</nav>
```

## Trabaja con htmx

FastAPI y htmx son una excelente combinación. Jx facilita devolver fragmentos de HTML:

```python title="app.py"
from fastapi import FastAPI, Request, Depends
from dependencies import Templates, catalog

app = FastAPI()


@app.get("/")
def home(templates: Templates = Depends()):
    items = get_items()
    return templates.render("pages/home.jx", items=items)


@app.get("/items")
def item_list(request: Request):
    """Devuelve solo el fragmento de la lista de items para peticiones htmx."""
    items = get_items()
    return HTMLResponse(catalog.render("partials/item-list.jx", items=items))


@app.post("/items")
def create_item(request: Request):
    item = create_new_item()
    # Devuelve el fragmento del nuevo item para que se inserte
    return HTMLResponse(catalog.render("partials/item.jx", item=item))


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    delete_item_by_id(item_id)
    return HTMLResponse("")  # Una respuesta vacía elimina el elemento
```

```html+jinja title="components/pages/home.jx"
{#import "../layout.jx" as Layout #}
{#import "../partials/item-list.jx" as ItemList #}
{#def items #}

<Layout title="Items">
  <h1>Items</h1>

  <form hx-post="/items" hx-target="#item-list" hx-swap="beforeend">
    <input type="text" name="name" placeholder="New item">
    <button type="submit">Add</button>
  </form>

  <div id="item-list">
    <ItemList items={{ items }} />
  </div>
</Layout>
```

```html+jinja title="components/partials/item.jx"
{#def item #}

<div id="item-{{ item.id }}" class="item">
  <span>{{ item.name }}</span>
  <button hx-delete="/items/{{ item.id }}" hx-target="#item-{{ item.id }}" hx-swap="outerHTML">
    Delete
  </button>
</div>
```

## Manejo de errores

Crea páginas de error personalizadas:

```python title="app.py"
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from jx import Catalog

app = FastAPI()
catalog = Catalog("components/", auto_reload=True)


@app.exception_handler(404)
def not_found(request: Request, exc: HTTPException):
    html = catalog.render(
        "errors/404.jx",
        globals={"request": request},
    )
    return HTMLResponse(html, status_code=404)


@app.exception_handler(500)
def server_error(request: Request, exc: Exception):
    html = catalog.render("errors/500.jx")
    return HTMLResponse(html, status_code=500)
```

## Ejemplo completo

```python title="app.py"
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from jx import Catalog
import os

# Configuración
is_production = os.getenv("ENV") == "production"
catalog = Catalog(auto_reload=not is_production)


# Mensajes flash
def flash(request: Request, message: str, category: str = "info"):
    if "_flashes" not in request.session:
        request.session["_flashes"] = []
    request.session["_flashes"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    return request.session.pop("_flashes", [])


# Dependencia de plantillas
class Templates:
    def __init__(self, request: Request):
        self.request = request

    def render(self, component: str, status_code: int = 200, **context):
        html = catalog.render(
            component,
            globals={
                "request": self.request,
                "url_for": self.request.url_for,
                "static": lambda path: self.request.url_for("static", path=path),
                "messages": get_flashed_messages(self.request),
            },
            **context,
        )
        return HTMLResponse(html, status_code=status_code)

# App
app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Rutas
@app.get("/", name="home")
def home(templates: Templates = Depends()):
    return templates.render("pages/home.jx")


@app.get("/products", name="products")
def products(templates: Templates = Depends()):
    products = get_products()
    return templates.render("pages/products.jx", products=products)


@app.get("/products/{product_id}", name="product_detail")
def product_detail(product_id: int, templates: Templates = Depends()):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404)
    return templates.render("pages/product.jx", product=product)


@app.post("/products", name="create_product")
def create_product(request: Request, templates: Templates = Depends()):
    # ... crear producto ...
    flash(request, "Product created!", "success")
    return RedirectResponse(url="/products", status_code=303)


# Manejadores de errores
@app.exception_handler(404)
def not_found(request: Request, exc):
    html = catalog.render("errors/404.jx", globals={"request": request})
    return HTMLResponse(html, status_code=404)
```

```html+jinja title="components/layout.jx"
{#import "./nav.jx" as Nav #}
{#import "./messages.jx" as Messages #}
{#css layout.css #}
{#def title #}

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  {% for css in assets.collect_css() %}
    <link rel="stylesheet" href="{{ static(css) }}">
  {% endfor %}
</head>
<body>
  <Nav />
  <Messages />
  <main>
    {{ content }}
  </main>
  {% for js in assets.collect_js() %}
    <script type="module" src="{{ static(js) }}"></script>
  {% endfor %}
</body>
</html>
```

## Rutas asíncronas

El renderizado de Jx es síncrono, pero esto está bien en rutas asíncronas. El renderizado de plantillas es CPU-bound y rápido:

```python
@app.get("/dashboard")
async def dashboard(templates: Templates = Depends()):
    # Llamada asíncrona a la base de datos
    stats = await get_dashboard_stats()

    # Renderizado síncrono de la plantilla (rápido, CPU-bound)
    return templates.render("pages/dashboard.jx", stats=stats)
```

Si lo prefieres, define rutas síncronas y FastAPI las ejecutará en un pool de threads:

```python
@app.get("/dashboard")
def dashboard(templates: Templates = Depends()):
    stats = get_dashboard_stats()  # síncrono
    return templates.render("pages/dashboard.jx", stats=stats)
```

Ambos enfoques funcionan bien. Elige según si tu obtención de datos es asíncrona o síncrona.
