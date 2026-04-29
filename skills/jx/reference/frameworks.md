# Framework integration

Jx is framework-agnostic — it just renders strings. To wire it into a stack you only need to: (1) construct a single `Catalog` at startup, (2) call `render()` from view handlers, (3) make framework helpers (`url_for`, CSRF, request, current user) available to components.

## Flask

```python
from flask import Flask, url_for, request, g
from jx import Catalog

app = Flask(__name__)
catalog = Catalog(
    "components/",
    auto_reload=app.debug,
    url_for=url_for,            # global available in every component
)

@app.route("/")
def home():
    return catalog.render(
        "pages/home.jx",
        globals={"request": request, "user": g.user},
        products=get_products(),
    )
```

### Sharing the Jinja env

Flask has its own Jinja2 environment with filters, globals, the loader, etc. Pass it to `Catalog` so everything stays in sync:

```python
app.jinja_env.filters["my_filter"] = my_filter
app.jinja_env.globals["my_global"] = my_global

catalog = Catalog("components/", jinja_env=app.jinja_env)
```

Components now see Flask's filters/globals automatically.

### CSRF

Flask-WTF or similar:

```python
from flask_wtf.csrf import generate_csrf

catalog = Catalog("components/", csrf_token=generate_csrf)
```

```html+jinja
<form method="post">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

### Static URLs

Pass `url_for` and use it:

```html+jinja
<img src="{{ url_for('static', filename='logo.png') }}" />
```

Or use the `asset_resolver` callback for component-declared assets — see `reference/assets.md`.

## Django

```python
# project/jx_setup.py
from jx import Catalog
from django.urls import reverse

catalog = Catalog(
    "components/",
    auto_reload=settings.DEBUG,
    url=reverse,                # name → URL
    static="/static/",          # base for static URLs
)
```

```python
# views.py
from django.http import HttpResponse
from .jx_setup import catalog

def home(request):
    html = catalog.render(
        "pages/home.jx",
        globals={"request": request, "user": request.user},
        products=get_products(),
    )
    return HttpResponse(html)
```

### A render helper

Most projects write a small wrapper that always passes `request` and renders to `HttpResponse`:

```python
def jx_render(request, template, **kwargs):
    html = catalog.render(
        template,
        globals={"request": request, "user": request.user},
        **kwargs,
    )
    return HttpResponse(html)
```

### CSRF

Django exposes `csrf_token` on the request context. Make it available via globals or a helper:

```python
from django.middleware.csrf import get_token

def jx_render(request, template, **kwargs):
    return HttpResponse(catalog.render(
        template,
        globals={"request": request, "csrf_token": get_token(request)},
        **kwargs,
    ))
```

```html+jinja
<form method="post">
  <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
  ...
</form>
```

### Class-based views

```python
from django.views.generic import View

class HomeView(View):
    def get(self, request):
        return jx_render(request, "pages/home.jx", products=Product.objects.all())
```

### Messages framework

```python
from django.contrib import messages

def jx_render(request, template, **kwargs):
    return HttpResponse(catalog.render(
        template,
        globals={
            "request": request,
            "messages": list(messages.get_messages(request)),
        },
        **kwargs,
    ))
```

## FastAPI

```python
from fastapi import FastAPI, Request, Depends
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

### Render helper

```python
def render(template: str, request: Request, **kwargs) -> HTMLResponse:
    return HTMLResponse(catalog.render(
        template,
        globals={"request": request, "url_for": request.url_for},
        **kwargs,
    ))
```

### Dependency injection

```python
def get_current_user(request: Request) -> User: ...

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: User = Depends(get_current_user)):
    return render("pages/home.jx", request, user=user)
```

### URL generation

FastAPI's `request.url_for("name")` returns a URL by route name; expose it as a global so components can use it:

```python
catalog = Catalog("components/", url_for=lambda name, **kw: app.url_path_for(name, **kw))
```

Or pass it per-request via `globals={"url_for": request.url_for}`.

### Async routes

`catalog.render(...)` is synchronous. For an async route, just call it directly:

```python
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    products = await get_products_async()
    return render("pages/home.jx", request, products=products)
```

If rendering is heavy and would block the event loop, run it in a thread pool: `await run_in_threadpool(catalog.render, ...)`.

## htmx

htmx is just attribute soup — Jx doesn't need anything special. Two patterns matter:

### 1. htmx attributes via `attrs` (underscore → dash)

```html+jinja title="components/htmx_button.jx"
{#def label, url, target #}

<button {{ attrs.render(
  class="htmx-btn",
  hx_get=url,
  hx_target=target,
  hx_swap="innerHTML",
) }}>
  {{ label }}
</button>
```

`hx_get` becomes `hx-get` automatically.

### 2. Partial responses

For htmx requests you usually return only a fragment, not a full page:

```python
@app.route("/products/search")
def search():
    if request.headers.get("HX-Request"):
        # Render only the result fragment
        return catalog.render("partials/product-list.jx", products=get_products())
    # Full page on direct navigation
    return catalog.render("pages/search.jx", products=get_products())
```

Component-declared assets (`{#css ... #}`, `{#js ... #}`) are collected only during the render — partial fragments don't include `<link>`/`<script>` tags by default. If a fragment introduces a new component that needs an asset, either preload it on the full page, or render the fragment inside a wrapper that also emits its own `<link>` for that one asset.

### Common patterns

| Pattern | Sketch |
|---|---|
| Search with debounce | `<input hx_get="/search" hx_trigger="input changed delay:300ms" hx_target="#results">` |
| Infinite scroll | `<div hx_get="/page/2" hx_trigger="revealed" hx_swap="afterend">` |
| Modal dialog over htmx | Server returns a `<dialog>` fragment; htmx swaps it in; client opens with `.showModal()`. |
| Form validation | Server returns the form with errors; htmx swaps in place. Use `hx_swap="outerHTML"`. |
| Out-of-band updates | Return multiple fragments with `hx-swap-oob="true"` on the secondary ones. |

## Cross-cutting tips

- **One Catalog per process.** Don't construct it per-request — that defeats caching.
- **Pass request via `globals`, not as a positional kwarg**, so deeply nested components can reach it.
- **Don't leak framework specifics into components.** A reusable component should not import `flask` or `django`. Accept URLs/tokens/users as props or globals.
