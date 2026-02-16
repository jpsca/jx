---
title: Installable Packages
description: Creating and using installable component packages with assets
icon: images/icons/package.svg
---

Python packages can bundle Jx components along with their CSS and/or JS assets. This lets you publish reusable component libraries that others install with `pip` and register with a single line of code.

## Using a Package

### Register with `add_package`

```python
from jx import Catalog

catalog = Catalog(
    "components/",
    asset_resolver=my_resolver,  # explained below
)
catalog.add_package("my_ui_kit", prefix="ui")
```

Unlike `add_folder`, the prefix here is **required**.

```html+jinja
{#import "@ui/button.jinja" as Button #}
{#import "@ui/card.jinja" as Card #}

<Button label="Click me" />
<Card title="Hello">Some content</Card>
```

## Asset Resolution

Components inside a package typically declare asset URLs relative to the package:

```html+jinja title="my_ui_kit/components/button.jinja"
{#css button.css #}
{#js button.js #}
{#def label #}

<button class="btn">{{ label }}</button>
```

But these files live in `site-packages`, not in your web server's static folder. An `asset_resolver` bridges this gap by transforming asset URLs at render time.

### The `asset_resolver` Callback

Pass a callable to the Catalog that receives `(url, prefix)` and returns the browser-accessible URL:

```python
catalog = Catalog(
    "components/",
    asset_resolver=lambda url, prefix: f"/pkg/{prefix}/{url}",
)
catalog.add_package("my_ui_kit", prefix="ui")
```

With this resolver, `button.css` declared in a `@ui/` component becomes `/pkg/ui/button.css` in the rendered HTML.

The resolver is **only invoked** for components whose prefix has a registered assets folder. Components from regular folders, even if they use a prefix, are not affected. This means your local components' asset URLs pass through unchanged.

A drawback is that you must manually add code to serve package assets **during development**. In production, you'd use `collect_assets` instead.

### Flask Example

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

### FastAPI Example

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

## Collecting Assets for Production

In production, you typically want static files served by Nginx, a CDN, or your framework's static file handler rather than a Python route. The `collect_assets` method copies all registered package assets to an output folder:

```python
catalog.collect_assets("static/pkg")
```

This copies files preserving the prefix structure:

```sh
static/pkg/
  ui/
    button.css
    button.js
    card.css
```

You can run this as part of your build or deploy step:

```python title="collect.py"
from myapp import catalog

catalog.collect_assets("static/pkg")
print("Assets collected.")
```

```bash
python collect.py
```

After collecting, update your resolver (or remove it entirely) to point to the static path:

```python
# Production: assets already at /static/pkg/<prefix>/

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

## Creating a Package

A Jx-compatible package exposes two module-level attributes:

- **`JX_COMPONENTS`** (required): Path to the folder containing `.jinja` component files.
- **`JX_ASSETS`** (optional): Path to the folder containing CSS/JS assets.

### Package Structure

```sh
my_ui_kit/
  __init__.py
  components/
    button.jinja
    card.jinja
    modal.jinja
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

Make sure the component and asset files are included in the distribution:

```toml title="pyproject.toml"
[project]
name = "my-ui-kit"
version = "1.0.0"

[tool.setuptools.package-data]
my_ui_kit = ["components/*.jinja", "assets/**/*"]
```

### Assets paths

Unlike local components, use a path relative to the declared assets folder:

```html+jinja title="my_ui_kit/components/card.jinja"
{#css "card.css" #}
...
```

### Components Can Import Siblings

Components within a package can import each other using relative paths:

```html+jinja title="my_ui_kit/components/card.jinja"
{#import "./button.jinja" as Button #}
{#def title #}
{#css "card.css" #}

<div class="card">
  <h3>{{ title }}</h3>
  {{ content }}
  <Button label="Learn more" />
</div>
```

### Package Without Assets

If your package only provides components (no CSS/JS), omit `JX_ASSETS`:

```python title="my_icons/__init__.py"
from pathlib import Path

JX_COMPONENTS = Path(__file__).parent / "icons"
```

The `asset_resolver` will never be called for this package's components.
