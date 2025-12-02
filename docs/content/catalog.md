---
title: Catalog
description: Configuring and using the Jx Catalog
---

The `Catalog` is the central manager for your components. It handles loading, caching, and rendering components from one or more folders.

## Basic Setup

```python
from jx import Catalog

catalog = Catalog("components/")
```

This creates a catalog that loads components from the `components/` folder.

## Constructor Options

```python
catalog = Catalog(
    folder="components/",       # Optional initial folder
    jinja_env=None,             # Custom Jinja2 environment
    extensions=None,            # Extra Jinja2 extensions
    filters=None,               # Custom template filters
    tests=None,                 # Custom template tests
    auto_reload=True,           # Auto-detect file changes
    **globals                   # Global template variables
)
```

### `folder`

Optional path to a component folder. Shortcut for calling `add_folder()`:

```python
# These are equivalent:
catalog = Catalog("components/")

catalog = Catalog()
catalog.add_folder("components/")
```

### `auto_reload`

When `True` (default), jx checks if component files have changed and reloads them automatically. Great for development.

For production, set to `False` to skip file modification checks:

```python
catalog = Catalog("components/", auto_reload=False)
```

### `globals`

Variables available to all components:

```python
catalog = Catalog(
    "components/",
    site_name="My App",
    current_year=2024,
    debug=True,
)
```

```html+jinja title="components/footer.jinja"
<footer>
  © {{ current_year }} {{ site_name }}
</footer>
```

### `filters`

Custom Jinja2 filters:

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

Custom Jinja2 tests:

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

Extra Jinja2 extensions to load:

```python
catalog = Catalog(
    "components/",
    extensions=["jinja2.ext.i18n", "jinja2.ext.loopcontrols"]
)
```

Note: The `jinja2.ext.do` extension is always enabled (required for `attrs` manipulation).

### `jinja_env`

Use an existing Jinja2 environment instead of creating a new one:

```python
from jinja2 import Environment

env = Environment()
env.globals["my_func"] = my_function
env.filters["my_filter"] = my_filter

catalog = Catalog("components/", jinja_env=env)
```

This is useful when integrating with frameworks that provide their own Jinja environment.

---

## Adding Folders

### `add_folder(path, prefix="", preload=True)`

Add a folder of components to the catalog:

```python
catalog = Catalog()
catalog.add_folder("components/")
catalog.add_folder("layouts/")
```

Components are imported by their path relative to the folder:

```html+jinja
{#import "button.jinja" as Button #}
{#import "forms/input.jinja" as Input #}
```

### Using Prefixes

Prefixes namespace components, useful for third-party libraries:

```python
catalog.add_folder("components/")
catalog.add_folder("vendor/ui-kit/", prefix="ui")
catalog.add_folder("vendor/icons/", prefix="icons")
```

Import prefixed components with `@prefix/`:

```html+jinja
{#import "button.jinja" as Button #}
{#import "@ui/modal.jinja" as Modal #}
{#import "@icons/check.jinja" as CheckIcon #}
```

### Preloading

By default, `preload=True` parses all components when the folder is added. This makes the first render faster.

Set `preload=False` to defer parsing until each component is first used:

```python
catalog.add_folder("components/", preload=False)
```

### Multiple Folders, Same Prefix

If you add multiple folders with the same prefix (or no prefix), they're treated as one namespace. If both contain a component with the same path, the **first one added wins**:

```python
catalog.add_folder("my-components/")      # Has button.jinja
catalog.add_folder("fallback-components/") # Also has button.jinja

# "button.jinja" resolves to my-components/button.jinja
```

---

## Rendering

### `render(relpath, globals=None, **kwargs)`

Render a component by its path:

```python
html = catalog.render("page.jinja", title="Hello", user=current_user)
```

**Arguments:**

- `relpath` - Path to the component (e.g., `"pages/home.jinja"`)
- `globals` - Dict of variables available to this component and all its imports
- `**kwargs` - Arguments passed directly to the component

```python
# Pass data as keyword arguments
html = catalog.render(
    "user-profile.jinja",
    user=user,
    posts=posts,
    show_email=True,
)

# Or use globals for values needed by child components too
html = catalog.render(
    "page.jinja",
    globals={"request": request, "csrf_token": token},
    title="Dashboard",
)
```

### `render_string(source, globals=None, **kwargs)`

Render a component from a string (not a file):

```python
source = """
{#def name #}
<h1>Hello, {{ name }}!</h1>
"""

html = catalog.render_string(source, name="World")
# <h1>Hello, World!</h1>
```

Useful for:

- Testing components
- Dynamic templates from a database
- Simple one-off renders

Note: String components can use absolute imports but not relative imports (no file path to resolve from).

---

## Framework Integration

### Flask

```python
from flask import Flask, render_template_string
from jx import Catalog

app = Flask(__name__)
catalog = Catalog(
    "components/",
    auto_reload=app.debug,
    url_for=flask.url_for,  # Make url_for available in components
)

@app.route("/")
def home():
    return catalog.render("pages/home.jinja", products=get_products())
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
        "pages/home.jinja",
        globals={"request": request},
        products=get_products(),
    )
```

### Sharing Jinja Environment

If your framework has its own Jinja environment with filters, globals, etc., pass it to the catalog:

```python
# Flask example
from flask import Flask

app = Flask(__name__)
app.jinja_env.filters["my_filter"] = my_filter
app.jinja_env.globals["my_global"] = my_global

catalog = Catalog("components/", jinja_env=app.jinja_env)
```

Now your components have access to everything registered in Flask's environment.

---

## Production Settings

For production, disable auto-reload.

```python
import os

catalog = Catalog(
    "components/",
    auto_reload=os.environ.get("DEBUG", "false").lower() == "true",
)
```

Or based on your framework's debug setting:

```python
# Flask
catalog = Catalog("components/", auto_reload=app.debug)

# FastAPI
catalog = Catalog("components/", auto_reload=settings.debug)
```