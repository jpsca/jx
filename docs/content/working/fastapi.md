---
title: Working with FastAPI
description: Integrating Jx components with FastAPI applications
---

[FastAPI](https://fastapi.tiangolo.com/){target=_blank} is a modern, high-performance Python web framework. Jx integrates cleanly with FastAPI for server-rendered HTML applications, especially when combined with htmx.

## Basic Setup

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

## Passing Request Context

Use FastAPI's dependency injection to pass request data to components:

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

## Creating a Render Helper

Simplify rendering with a helper function:

```python title="app.py"
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jx import Catalog

app = FastAPI()
catalog = Catalog("components/", auto_reload=True)


def render(request: Request, component: str, status_code: int = 200, **context):
    """Render a Jx component with request context."""
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

## Using Dependency Injection

For cleaner code, create a dependency that provides the render function:

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

## URL Generation

FastAPI doesn't have a built-in `url_for` like Flask. Use `request.url_for()`:

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

Make sure your routes have names:

```python title="app.py"
@app.get("/", name="home")
def home(templates: Templates = Depends()):
    return templates.render("pages/home.jx")


@app.get("/products", name="products")
def products(templates: Templates = Depends()):
    return templates.render("pages/products.jx")
```

## Static Files

Mount a static files folder and create a helper:

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

## Flash Messages

FastAPI doesn't have built-in flash messages. Here's a simple session-based implementation:

```python title="flash.py"
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request


def flash(request: Request, message: str, category: str = "info"):
    """Add a flash message to the session."""
    if "_flashes" not in request.session:
        request.session["_flashes"] = []
    request.session["_flashes"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    """Get and clear flash messages from the session."""
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
    # ... create item ...
    flash(request, "Item created successfully!", "success")
    return RedirectResponse(url="/items", status_code=303)
```

## Authentication

Integrate with your authentication system:

```python title="dependencies.py"
from fastapi import Request, Depends
from auth import get_current_user  # Your auth implementation


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

## Working with htmx

FastAPI and htmx are a great combination. Jx makes it easy to return HTML partials:

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
    """Return just the item list partial for htmx requests."""
    items = get_items()
    return HTMLResponse(catalog.render("partials/item-list.jx", items=items))


@app.post("/items")
def create_item(request: Request):
    item = create_new_item()
    # Return the new item partial to be swapped in
    return HTMLResponse(catalog.render("partials/item.jx", item=item))


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    delete_item_by_id(item_id)
    return HTMLResponse("")  # Empty response removes the element
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

## Error Handling

Create custom error pages:

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

## Complete Example

```python title="app.py"
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from jx import Catalog
import os

# Configuration
is_production = os.getenv("ENV") == "production"
catalog = Catalog(auto_reload=not is_production)


# Flash messages
def flash(request: Request, message: str, category: str = "info"):
    if "_flashes" not in request.session:
        request.session["_flashes"] = []
    request.session["_flashes"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    return request.session.pop("_flashes", [])


# Templates dependency
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


# Routes
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
    # ... create product ...
    flash(request, "Product created!", "success")
    return RedirectResponse(url="/products", status_code=303)


# Error handlers
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

## Async Routes

Jx rendering is synchronous, but this is fine in async routes. Template rendering is CPU-bound and fast:

```python
@app.get("/dashboard")
async def dashboard(templates: Templates = Depends()):
    # Async database call
    stats = await get_dashboard_stats()

    # Sync template rendering (fast, CPU-bound)
    return templates.render("pages/dashboard.jx", stats=stats)
```

If you prefer, define sync routes and FastAPI will run them in a thread pool:

```python
@app.get("/dashboard")
def dashboard(templates: Templates = Depends()):
    stats = get_dashboard_stats()  # sync
    return templates.render("pages/dashboard.jx", stats=stats)
```

Both approaches work well. Choose based on whether your data fetching is async or sync.
