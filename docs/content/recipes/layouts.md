---
title: Layout Components
description: Creating reusable page layouts
---

Layouts are components that wrap entire pages, providing consistent structure like headers, footers, and navigation.

## Basic Layout

```html+jinja title="components/layout.jinja"
{#def title #}
{#css layout.css #}

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  {{ assets.render_css() }}
  {{ assets.render_js() }}
</head>
<body>
  <header>
    <nav>
      <a href="/">Home</a>
      <a href="/about">About</a>
    </nav>
  </header>

  <main>
    {{ content }}
  </main>

  <footer>
    <p>&copy; 2026 My Site</p>
  </footer>

</body>
</html>
```

```html+jinja title="components/pages/home.jinja"
{#import "../layout.jinja" as Layout #}

<Layout title="Home">
  <h1>Welcome!</h1>
  <p>This is the home page.</p>
</Layout>
```

## Layout with Slots

Use named slots for customizable sections:

```html+jinja title="components/layout.jinja"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {% slot head %}{% endslot %}
  {{ assets.render_css() }}
</head>
<body>
  <header>
    {% slot header %}
      <nav><a href="/">Home</a></nav>
    {% endslot %}
  </header>

  <main>
    {{ content }}
  </main>

  <footer>
    {% slot footer %}
      <p>&copy; 2026</p>
    {% endslot %}
  </footer>

  {% slot scripts %}{% endslot %}
  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="usage"
{#import "layout.jinja" as Layout #}

<Layout title="Dashboard">
  {% fill head %}
    <meta name="robots" content="noindex">
  {% endfill %}

  {% fill header %}
    <nav>
      <a href="/dashboard">Dashboard</a>
      <a href="/settings">Settings</a>
    </nav>
  {% endfill %}

  <h1>Dashboard</h1>
  <p>Welcome back!</p>

  {% fill scripts %}
    <script>console.log('Page loaded');</script>
  {% endfill %}
</Layout>
```

## Nested Layouts

Create specialized layouts that extend a base:

```html+jinja title="components/layouts/base.jinja"
{#def title #}
{#css base.css #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }} | My App</title>
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="components/layouts/app.jinja"
{#import "./base.jinja" as Base #}
{#import "../sidebar.jinja" as Sidebar #}
{#def title #}
{#css app.css #}

<Base title={{ title }}>
  <div class="app-layout">
    <Sidebar />
    <main class="app-content">
      {{ content }}
    </main>
  </div>
</Base>
```

```html+jinja title="components/layouts/auth.jinja"
{#import "./base.jinja" as Base #}
{#def title #}
{#css auth.css #}

<Base title={{ title }}>
  <div class="auth-layout">
    <div class="auth-card">
      {{ content }}
    </div>
  </div>
</Base>
```

```html+jinja title="usage"
{#import "layouts/app.jinja" as App #}

<App title="Dashboard">
  <h1>Dashboard</h1>
</App>
```

```html+jinja title="usage"
{#import "layouts/auth.jinja" as Auth #}

<Auth title="Login">
  <h1>Sign In</h1>
  <form>...</form>
</Auth>
```

## Layout with Navigation Highlighting

Pass the current page to highlight active nav items:

```html+jinja title="components/layout.jinja"
{#def title, current_page="" #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {{ assets.render_css() }}
</head>
<body>
  <nav>
    <a href="/" class="{{ 'active' if current_page == 'home' else '' }}">Home</a>
    <a href="/about" class="{{ 'active' if current_page == 'about' else '' }}">About</a>
    <a href="/contact" class="{{ 'active' if current_page == 'contact' else '' }}">Contact</a>
  </nav>

  <main>{{ content }}</main>

  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="pages/about.jinja"
{#import "layout.jinja" as Layout #}

<Layout title="About Us" current_page="about">
  <h1>About Us</h1>
</Layout>
```

## Conditional Layout Sections

```html+jinja title="components/layout.jinja"
{#def title, show_sidebar=true, show_footer=true #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {{ assets.render_css() }}
</head>
<body>
  <div class="layout {{ 'has-sidebar' if show_sidebar else '' }}">
    {% if show_sidebar %}
      <aside class="sidebar">
        {% slot sidebar %}
          <nav>Default sidebar</nav>
        {% endslot %}
      </aside>
    {% endif %}

    <main>{{ content }}</main>
  </div>

  {% if show_footer %}
    <footer>
      {% slot footer %}<p>&copy; 2026</p>{% endslot %}
    </footer>
  {% endif %}

  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="usage"
{# Full layout with sidebar #}
<Layout title="Dashboard">
  {% fill sidebar %}
    <nav>Custom sidebar</nav>
  {% endfill %}
  <h1>Dashboard</h1>
</Layout>

{# Minimal layout without sidebar #}
<Layout title="Login" show_sidebar={{ false }} show_footer={{ false }}>
  <form>Login form</form>
</Layout>
```
