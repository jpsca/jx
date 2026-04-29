# Assets reference

Per-component CSS and JS, declared inline, collected automatically across the entire render tree.

## Declaring assets

```html+jinja title="card.jx"
{#css card.css, animations.css #}
{#js card.js #}
{#def title #}

<div class="card">...</div>
```

Multiple files: comma-separated. Each entry can be:

- **Relative** (`card.css`) — resolved by your web server / build tool.
- **Absolute path** (`/static/styles/global.css`).
- **Full URL** (`https://cdn.example.com/lib.js`).

Jx does not rewrite the URLs (except via `asset_resolver`, see below) — they're passed through verbatim.

## Rendering assets

In your layout/page component:

```html+jinja title="layout.jx"
<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {{ assets.render() }}     {# both CSS and JS #}
</head>
<body>
  {{ content }}
</body>
</html>
```

### Granular methods

```html+jinja
{{ assets.render_css() }}
{# <link rel="stylesheet" href="...">  for every collected CSS #}

{{ assets.render_js() }}
{# <script type="module" src="..."></script>  by default #}

{{ assets.render_js(module=False) }}
{# <script src="..." defer></script>   regular deferred #}

{{ assets.render_js(module=False, defer=False) }}
{# <script src="..."></script>          plain #}
```

Options:

- `module=True` (default) → `type="module"`.
- `module=False` → no module attribute; you can opt into `defer`.
- `defer=True` → adds the `defer` attribute (only when `module=False`; modules are deferred by default).

### Manual collection

```html+jinja
{% for url in assets.collect_css() %}
  <link rel="stylesheet" href="{{ url_for('static', filename=url) }}">
{% endfor %}
{% for url in assets.collect_js() %}
  <script type="module" src="{{ url_for('static', filename=url) }}"></script>
{% endfor %}
```

`collect_css()` / `collect_js()` return Python lists in the order they were collected. Use them when you need to wrap each URL with framework helpers (e.g. Flask's `url_for("static", ...)`).

## How collection works

Walking starts at the component you pass to `catalog.render(...)` and recurses into every imported child:

1. Root component's CSS, then its JS.
2. Each `{#import ... #}`'d child, recursively.
3. Deduplicate — each URL appears at most once.
4. Order preserved: parents before children, imports in declaration order.

Practical consequence: declaring `transitions.css` in 12 components only emits one `<link>` tag.

## URL strategies

### Co-located assets

```
components/
  card/
    card.jx
    card.css
    card.js
```

```html+jinja
{#css /static/components/card/card.css #}
{#js /static/components/card/card.js #}
```

### Centralized static folder

```
components/
  card.jx           {#css /static/css/card.css #}
                     {#js /static/js/card.js #}
static/
  css/card.css
  js/card.js
```

### Build tool (Vite / esbuild / webpack)

```html+jinja
{#css /dist/card.css #}
{#js /dist/card.js #}
```

The build tool produces hashed output (`card.abc123.css`); use a manifest lookup or `asset_resolver` to map source paths to hashed paths at render time.

## Installable component packages

When you `add_folder(path, prefix="ui", assets="path/to/static")`, two things happen:

1. The `assets=` folder is registered as the source of CSS/JS files for components in that prefix.
2. `asset_resolver` (a `Catalog` constructor option) is invoked at render time for every asset URL declared by a component in that prefix.

```python
def my_resolver(url, prefix):
    # `url` is what the component declared (e.g. "button.css")
    # `prefix` is the folder's prefix (e.g. "ui")
    return f"/static/vendor/{prefix}/{url}"

catalog = Catalog("components/", asset_resolver=my_resolver)
catalog.add_folder("vendor/ui-lib", prefix="ui", assets="vendor/ui-lib/static")
```

At deploy time, ship those assets to your CDN/static folder:

```python
catalog.collect_assets("static/vendor")
# Copies vendor/ui-lib/static/* into static/vendor/ui/*
```

Now `<link href="/static/vendor/ui/button.css">` resolves correctly.

## Best practices

- **Component-scoped CSS.** Use a class with the component's name (`.Card`, `.Card__title`) so styles don't leak. Modern CSS nesting works well: `.Card { & h3 { ... } }`.
- **One concern per file.** A `button.css` should weigh kilobytes, not megabytes. If you find yourself declaring `button-and-everything-else.css`, split it.
- **Third-party deps live in declarations, not in HTML.** Declare `{#css https://cdn.../lib.css #}` so that any component using the lib drags it in automatically and dedup works.
- **No middleware needed.** Jx doesn't serve assets; it just emits URLs. Use whatever your stack already does for static files (Flask, nginx, S3, Vite).
