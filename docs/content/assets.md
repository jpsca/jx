---
title: Assets
description: Managing CSS and JavaScript in components
---

Any component can declare the URLs of the CSS and JavaScript files that uses. Jx automatically collects these assets from all the components you use and provides simple functions to render them.

## Why Per-Component Assets?

Traditional approaches put all CSS and JS in global files. This has problems:

- **Hard to maintain**: Which styles belong to which component?
- **Bloat**: Load everything even if you only use a few components
- **Coupling**: Can't move/share components without hunting down their styles

With per-component assets:

- **Portability**: Copy a component folder, and its assets come with it
- **Clarity**: Each component declares what it needs
- **Performance**: Only load assets for components you actually use
- **Testing**: Test component styles and behavior together

## Declaring Assets

Use `{#css ... #}` and `{#js ... #}` comments at the top of your component:

```html+jinja title="components/card.jinja"
{#css card.css, animations.css #}
{#js card.js #}
{#def title #}

<div class="card">
  <h3>{{ title }}</h3>
  <div class="card-body">
    {{ content }}
  </div>
</div>
```

Multiple files are comma-separated. Each file can be:

- **Relative**: `card.css` (relative to your static files)
- **Absolute path**: `/static/styles/global.css`
- **URL**: `https://cdn.example.com/library.js`

## The `assets` Global

When you render a component, Jx provides an `assets` global object with methods to collect and render assets.

### `assets.render()`

The simplest approach; renders both CSS and JS:

```html+jinja title="components/layout.jinja"
{#css layout.css #}
{#js layout.js #}

<!DOCTYPE html>
<html>
<head>
  <title>My App</title>
  {{ assets.render() }}
</head>
<body>
  {{ content }}
</body>
</html>
```

This collects assets from the layout component and all components it imports, then renders them as `<link>` and `<script>` tags.

### `assets.render_css()`

Renders only CSS as `<link>` tags:

```html+jinja
<head>
  <title>My App</title>
  {{ assets.render_css() }}
</head>
```

**Output:**

```html
<link rel="stylesheet" href="layout.css">
<link rel="stylesheet" href="card.css">
<link rel="stylesheet" href="button.css">
```

### `assets.render_js(module=True, defer=True)`

Renders JavaScript as `<script>` tags:

```html+jinja
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
```

**Output (default):**

```html
<script type="module" src="layout.js"></script>
<script type="module" src="card.js"></script>
```

**Options:**

- `module=True` (default): Add `type="module"`
- `module=False`: Regular scripts
- `defer=True`: Add `defer` attribute (only when `module=False`)

```html+jinja
{# ES modules (default) #}
{{ assets.render_js() }}
{# <script type="module" src="..."></script> #}

{# Regular deferred scripts #}
{{ assets.render_js(module=False) }}
{# <script src="..." defer></script> #}

{# Regular non-deferred scripts #}
{{ assets.render_js(module=False, defer=False) }}
{# <script src="..."></script> #}
```

## Collection Methods

For more control, use the collection methods:

### `assets.collect_css()`

Returns a list of all CSS file URLs:

```html+jinja
{% for url in assets.collect_css() %}
  <link rel="stylesheet" href="{{ url }}">
{% endfor %}
```

### `assets.collect_js()`

Returns a list of all JS file URLs:

```html+jinja
{% for url in assets.collect_js() %}
  <script type="module" src="{{ url }}"></script>
{% endfor %}
```

## How Asset Collection Works

Jx collects assets by walking the component tree:

1. Start with the root component you're rendering
2. Collect its CSS and JS declarations
3. Recursively collect from each imported component
4. Deduplicate (each file appears only once)
5. Return in dependency order

**Example:**

```html+jinja title="page.jinja"
{#import "./layout.jinja" as Layout #}
{#import "./card.jinja" as Card #}
{#css page.css #}

<Layout>
  <Card>...</Card>
</Layout>
```

```html+jinja title="layout.jinja"
{#import "./header.jinja" as Header #}
{#css layout.css #}

<div>
  <Header />
  {{ content }}
</div>
```

```html+jinja title="header.jinja"
{#css header.css #}
<header>...</header>
```

```html+jinja title="card.jinja"
{#css card.css #}
<div class="card">{{ content }}</div>
```

**Collected CSS (in order):**

```
page.css
layout.css
header.css
card.css
```

Each imported component's assets are collected recursively.

## Asset URLs

Jx doesn't process or rewrite asset URLs; they're used exactly as you write them.

### Relative URLs

```html+jinja
{#css card.css #}
{#js card.js #}
```

**Output:**

```html
<link rel="stylesheet" href="card.css">
<script type="module" src="card.js"></script>
```

How these resolve depends on your HTML base path and server configuration.

### Absolute Paths

```html+jinja
{#css /static/components/card.css #}
{#js /static/components/card.js #}
```

**Output:**

```html
<link rel="stylesheet" href="/static/components/card.css">
<script type="module" src="/static/components/card.js"></script>
```

### Full URLs

```html+jinja
{#css https://cdn.example.com/styles/card.css #}
{#js https://cdn.example.com/scripts/card.js #}
```

**Output:**

```html
<link rel="stylesheet" href="https://cdn.example.com/styles/card.css">
<script type="module" src="https://cdn.example.com/scripts/card.js"></script>
```

## Organizing Assets

### Option 1: Co-located Assets

Keep assets next to components:

```
components/
  card/
    card.jinja
    card.css
    card.js
  button/
    button.jinja
    button.css
    button.js
```

```html+jinja title="components/card/card.jinja"
{#css /static/components/card/card.css #}
{#js /static/components/card/card.js #}
```

### Option 2: Separate Assets Folder

Keep components and assets separate:

```
components/
  card.jinja
  button.jinja
static/
  css/
    card.css
    button.css
  js/
    card.js
    button.js
```

```html+jinja title="components/card.jinja"
{#css /static/css/card.css #}
{#js /static/js/card.js #}
```

### Option 3: Build Tool Integration

Use Vite, Webpack, or another bundler:

```html+jinja title="components/card.jinja"
{#css /dist/card.css #}
{#js /dist/card.js #}
```

Your build tool generates the files with hashes for cache-busting:

```html
<link rel="stylesheet" href="/dist/card.abc123.css">
<script type="module" src="/dist/card.def456.js"></script>
```

## Common Patterns

### Basic Layout

```html+jinja title="components/layout.jinja"
{#css layout.css #}
{#js layout.js #}
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

### Separate CSS and JS Placement

```html+jinja
<!DOCTYPE html>
<html>
<head>
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}

  {# Scripts at the bottom #}
  {{ assets.render_js() }}
</body>
</html>
```

### Global + Component Styles

```html+jinja
<head>
  {# Global styles first #}
  <link rel="stylesheet" href="/static/global.css">
  <link rel="stylesheet" href="/static/tailwind.css">

  {# Then component styles #}
  {{ assets.render_css() }}
</head>
```

### Custom Asset Rendering

```html+jinja
<head>
  {# Add integrity and crossorigin for CDN assets #}
  {% for url in assets.collect_css() %}
    {% if url.startswith('https://cdn.') %}
      <link rel="stylesheet" href="{{ url }}"
            integrity="sha384-..."
            crossorigin="anonymous">
    {% else %}
      <link rel="stylesheet" href="{{ url }}">
    {% endif %}
  {% endfor %}
</head>
```

### Conditional Loading

```html+jinja
{#def theme="light" #}

<head>
  {{ assets.render_css() }}

  {% if theme == "dark" %}
    <link rel="stylesheet" href="/static/dark-theme.css">
  {% endif %}
</head>
```

## Using External Libraries

### CDN Libraries

```html+jinja title="components/map.jinja"
{#css https://unpkg.com/leaflet@1.9.4/dist/leaflet.css #}
{#js https://unpkg.com/leaflet@1.9.4/dist/leaflet.js #}

<div id="map"></div>
```

### NPM Libraries

If you're using a build tool:

```html+jinja title="components/chart.jinja"
{#js /dist/chart.bundle.js #}  {# Built from node_modules/chart.js #}

<canvas id="chart"></canvas>
```

### Mixing Global and Component Assets

```html+jinja title="components/layout.jinja"
<!DOCTYPE html>
<html>
<head>
  {# Global framework #}
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>

  {# Component assets #}
  {{ assets.render() }}
</head>
<body>
  {{ content }}
</body>
</html>
```

## Best Practices

### 1. Use Relative Paths for Component Assets

```html+jinja
{# ✅ Good - relative to your static folder #}
{#css components/card.css #}

{# ❌ Avoid - hard to move between projects #}
{#css /home/user/myapp/static/components/card.css #}
```

### 2. Group Related Assets

```html+jinja
{# ✅ Good - related styles together #}
{#css card.css, card-animations.css #}
{#js card.js #}
```

### 3. Declare Third-Party Dependencies

```html+jinja
{# ✅ Good - explicit dependencies #}
{#css https://cdn.example.com/library.css #}
{#import "./component-using-library.jinja" as Component #}
```

### 4. Keep Asset Files Small

Each component should have focused styles and scripts:

```html+jinja
{# ✅ Good - focused component #}
{#css button.css #}  {# ~2KB #}
{#js button.js #}    {# ~1KB #}

{# ❌ Bad - too much stuff #}
{#css button-and-everything-else.css #}  {# ~50KB #}
```

### 5. Use CSS Scoping

Always scope your component styles:

```css
/* ✅ Good - scoped to component */
.Card {
  padding: 1rem;
}
.Card__title {
  font-size: 1.5rem;
}

/* ❌ Bad - will affect everything */
h3 {
  font-size: 1.5rem;
}
```

Modern browsers support [CSS nesting](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_nesting):

```css
.Card {
  padding: 1rem;

  & h3 {
    font-size: 1.5rem;
  }
}
```

## No Middleware Required

Unlike some component libraries, Jx doesn't require middleware to serve component assets. You serve them however you want:

- **Static files**: Configure your web framework to serve from `static/`
- **CDN**: Upload to S3/CloudFront and reference those URLs
- **Build tools**: Use Vite/Webpack to bundle and serve
- **Reverse proxy**: Nginx/Caddy serve static files

Jx just collects the URLs you declare and renders them as tags.

## Performance Considerations

### Asset Deduplication

Jx automatically deduplicates assets. If multiple components declare the same CSS file, it's only included once:

```html+jinja
{# card.jinja uses common.css #}
{# button.jinja uses common.css #}
{# page.jinja uses both #}
```

Results in:

```html
<link rel="stylesheet" href="common.css">  <!-- Only once! -->
<link rel="stylesheet" href="card.css">
<link rel="stylesheet" href="button.css">
```

### Loading Order

Assets are collected in dependency order:
1. Parent component assets first
2. Then imported component assets
3. In the order they're imported

This ensures proper cascade and dependency resolution.

