# Catalog reference

The `Catalog` is the central manager: it loads components, caches them, and renders them. One `Catalog` per application is the norm.

## Constructor

```python
from jx import Catalog

catalog = Catalog(
    folder="components/",       # Optional initial folder (shortcut for add_folder)
    *,                          # everything below is keyword-only
    jinja_env=None,             # Use an existing Jinja2 Environment
    extensions=None,            # Extra Jinja2 extensions (jinja2.ext.do is always on)
    filters=None,               # {"name": fn, ...}
    tests=None,                 # {"name": fn, ...}
    auto_reload=True,           # Re-check file mtimes; turn OFF in production
    asset_resolver=None,        # callback(url, prefix) -> str
    file_ext=".jx",             # Component file extension
    **template_globals,         # Extra template globals (site_name=..., url_for=..., etc.)
)
```

### Constructor options in detail

- **`folder`**: shortcut for one immediate `add_folder(folder)`. Equivalent to `Catalog()` followed by `catalog.add_folder("components/")`.
- **`file_ext`**: change to `.jinja` or anything else if you have an existing convention.
- **`auto_reload`**: when `True` (dev default), Jx stats every component file on each render. Set to `False` in production. A common idiom: `auto_reload=app.debug`.
- **`globals`**: arbitrary kwargs become template globals visible to every component. Pass framework helpers here (e.g. `url_for=url_for` for Flask).
- **`filters` / `tests`**: dicts of name → callable. Available everywhere as `{{ x | name }}` or `{% if x is name %}`.
- **`extensions`**: additional Jinja2 extensions. `jinja2.ext.do` is always enabled (Jx requires it for `attrs` manipulation).
- **`jinja_env`**: pass an existing `jinja2.Environment` instead of creating a new one. Use this to share filters/globals/loaders with a framework.
- **`asset_resolver`**: callback for transforming component asset URLs. Signature `(url: str, prefix: str) -> str`. Only invoked for components whose folder was registered with an `assets=` argument. See `reference/assets.md`.

## Adding folders

```python
catalog.add_folder(path, *, prefix="", assets=None)
```

`prefix` and `assets` are **keyword-only** (note the `*` in the signature).

```python
catalog = Catalog()
catalog.add_folder("components/")              # default (no prefix)
catalog.add_folder("layouts/")                 # multiple folders are merged
catalog.add_folder("vendor/ui-lib", prefix="ui", assets="vendor/ui-lib/static")
```

`assets=` requires `prefix=` to be set — `add_folder("path", assets="...")` without a prefix raises `ValueError("Cannot register assets folder without a prefix")`.

Components are imported by their path relative to the folder:

```html+jinja
{#import "button.jx" as Button #}
{#import "forms/input.jx" as Input #}
```

### Prefixes

A prefix namespaces a folder, mainly for third-party libraries. Imports use `@prefix/path`:

```html+jinja
{#import "@ui/button.jx" as Button #}
{#import "@ui/modal.jx" as Modal #}
```

The `assets` argument is the folder containing CSS/JS files for that prefix; together with `asset_resolver` it lets installable packages serve their assets via your URL conventions.

## Rendering

### `render(relpath, globals=None, **kwargs)`

```python
html = catalog.render("pages/home.jx", user=user, products=products)

html = catalog.render(
    "page.jx",
    globals={"request": request, "csrf_token": token},  # available everywhere in the tree
    title="Dashboard",                                   # only available in page.jx
)
```

- **`relpath`**: path to the component, relative to one of the registered folders.
- **`globals`**: dict of variables available to this component and every imported child. Use this for cross-cutting context (request, current user, CSRF tokens).
- **`**kwargs`**: passed directly to the root component as props. Arrive only at the root; not visible inside children unless re-passed.

### `render_string(source, globals=None, **kwargs)`

Render a component from a string instead of a file:

```python
source = "{#def name #}\n<h1>Hello, {{ name }}!</h1>"
html = catalog.render_string(source, name="World")
```

Useful for tests, snippets stored in a database, or one-off renders. Limitation: relative imports (`./sibling.jx`) don't work — there's no file path to resolve from. Absolute imports (`button.jx`, `@ui/button.jx`) do work.

## Introspection

### `list_components()`

Returns every registered component path:

```python
catalog.list_components()
# ["button.jx", "card.jx", "forms/input.jx", "@ui/modal.jx"]
```

### `get_signature(relpath)`

Inspect a component's interface:

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

Useful for documentation generators, IDE tooling, or a runtime registry.

### `collect_assets(output)`

Copy package assets (registered via `add_folder(..., assets=...)`) into a build folder. Each prefix's files end up under `<output>/<prefix>/`:

```python
copied = catalog.collect_assets("static/vendor")
# [("ui", Path("button.css")), ("ui", Path("button.js")), ...]
```

Returns a list of `(prefix, relative_path)` tuples — handy when you want to log or post-process the copy.

## Built-in template globals

Beyond anything you pass in, every component has access to:

- **`_get_random_id(prefix="id")`** — returns a unique-per-call string suitable for HTML IDs. Each call produces a different value, e.g. `popover-a1b2c3d4...`. Use it for components that need internal IDs (popover targets, `<label for>`, `<input>`) without forcing callers to pass one in.

```html+jinja
{% set input_id = id or _get_random_id(name) %}
{% if label %}<label for="{{ input_id }}">{{ label }}</label>{% endif %}
<input id="{{ input_id }}" name="{{ name }}" {{ attrs.render() }} />
```

## Production checklist

- `auto_reload=False` (or tied to a debug flag).
- A single `Catalog` instance, created at startup, reused across requests.
- If sharing a Jinja env with a framework, pass `jinja_env=` so you don't end up with two parallel envs and divergent filters/globals.
