---
title: Installable Packages
description: Creating and using installable component packages with assets
---

Python packages can bundle Jx components along with their CSS and JS assets. This lets you publish reusable component libraries that others install with `pip` and register with a single line of code.

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

This imports the `my_ui_kit` module, reads its `JX_COMPONENTS` and `JX_ASSETS` attributes, and registers them. Components are available under the `@ui/` prefix:

```html+jinja
{#import "@ui/button.jinja" as Button #}
{#import "@ui/card.jinja" as Card #}

<Button label="Click me" />
<Card title="Hello">Some content</Card>
```

### Register with `add_folder`

If you need more control, use `add_folder` directly with the `assets` parameter:

```python
catalog.add_folder(
    "/path/to/package/components",
    prefix="ui",
    assets="/path/to/package/assets",
)
```

## Asset Resolution

Components inside a package typically declare asset URLs relative to the package:

```html+jinja title="my_ui_kit/components/button.jinja"
{#css button.css #}
{#js button.js #}
{#def label #}

<button class="btn">{{ label }}</button>
```

But these files live in `site-packages`, not in your web server's static directory. An `asset_resolver` bridges this gap by transforming asset URLs at render time.

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

The resolver is **only invoked** for components whose prefix has a registered assets directory (via `assets=` or `JX_ASSETS`). Components from regular folders, even if they use a prefix, are not affected. This means your local components' asset URLs pass through unchanged.

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
    assets_dir = catalog.get_assets_dir(prefix)
    if assets_dir is None:
        abort(404)
    return send_from_directory(assets_dir, filename)
```

During development, the `/pkg/<prefix>/` route serves files directly from the package's assets directory. In production, you'd use `collect_assets` instead.

### FastAPI Example

```python
from pathlib import Path
from fastapi import FastAPI
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
    assets_dir = catalog.get_assets_dir(prefix)
    if assets_dir is None:
        raise HTTPException(404)
    return FileResponse(assets_dir / filename)
```

## Collecting Assets for Production

In production, you typically want static files served by Nginx, a CDN, or your framework's static file handler rather than a Python route. The `collect_assets` method copies all registered package assets to an output directory:

```python
catalog.collect_assets("static/pkg")
```

This copies files preserving the prefix structure:

```
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
catalog = Catalog(
    "components/",
    asset_resolver=lambda url, prefix: f"/static/pkg/{prefix}/{url}",
    auto_reload=False,
)
```

## Creating a Package

A Jx-compatible package exposes two module-level attributes:

- **`JX_COMPONENTS`** (required): Path to the directory containing `.jinja` component files.
- **`JX_ASSETS`** (optional): Path to the directory containing CSS/JS assets.

### Package Structure

```
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

### Components Can Import Siblings

Components within a package can import each other using relative paths:

```html+jinja title="my_ui_kit/components/card.jinja"
{#import "./button.jinja" as Button #}
{#def title #}

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

## API Reference

### `Catalog(asset_resolver=...)`

Optional callable `(url: str, prefix: str) -> str` that transforms asset URLs. Only invoked for components whose prefix has a registered assets directory.

### `catalog.add_package(package_name, *, prefix="", preload=True)`

Import a Python package and register its `JX_COMPONENTS` folder (and optionally `JX_ASSETS` directory). Raises `ValueError` if the module has no `JX_COMPONENTS` attribute.

### `catalog.add_folder(path, *, prefix="", assets=None, preload=True)`

The `assets` parameter registers a directory of static assets for the given prefix. When set, the `asset_resolver` will be invoked for asset URLs from these components.

### `catalog.get_assets_dir(prefix) -> Path | None`

Returns the resolved filesystem path of the assets directory for a prefix, or `None` if no assets directory was registered.

### `catalog.collect_assets(output) -> list[tuple[str, Path]]`

Copies all registered asset files to `<output>/<prefix>/`. Returns a list of `(prefix, relative_path)` tuples for every file copied.
