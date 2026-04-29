---
title: Componentes de layout
description: Crea layouts de página reutilizables
---

Los layouts son componentes que envuelven páginas completas, proporcionando una estructura consistente como encabezados, pies de página y navegación.

## Layout básico

```html+jinja title="components/layout.jx"
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
      <a href="/">Inicio</a>
      <a href="/about">Acerca de</a>
    </nav>
  </header>

  <main>
    {{ content }}
  </main>

  <footer>
    <p>&copy; 2026 Mi sitio</p>
  </footer>

</body>
</html>
```

```html+jinja title="components/pages/home.jx"
{#import "../layout.jx" as Layout #}

<Layout title="Inicio">
  <h1>¡Bienvenido!</h1>
  <p>Esta es la página de inicio.</p>
</Layout>
```

## Layout con slots

Usa slots con nombre para secciones personalizables:

```html+jinja title="components/layout.jx"
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
      <nav><a href="/">Inicio</a></nav>
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
{#import "layout.jx" as Layout #}

<Layout title="Panel">
  {% fill head %}
    <meta name="robots" content="noindex">
  {% endfill %}

  {% fill header %}
    <nav>
      <a href="/dashboard">Panel</a>
      <a href="/settings">Configuración</a>
    </nav>
  {% endfill %}

  <h1>Panel</h1>
  <p>¡Bienvenido de vuelta!</p>

  {% fill scripts %}
    <script>console.log('Page loaded');</script>
  {% endfill %}
</Layout>
```

## Layouts anidados

Crea layouts especializados que extiendan uno base:

```html+jinja title="components/layouts/base.jx"
{#def title #}
{#css base.css #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }} | Mi App</title>
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="components/layouts/app.jx"
{#import "./base.jx" as Base #}
{#import "../sidebar.jx" as Sidebar #}
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

```html+jinja title="components/layouts/auth.jx"
{#import "./base.jx" as Base #}
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
{#import "layouts/app.jx" as App #}

<App title="Panel">
  <h1>Panel</h1>
</App>
```

```html+jinja title="usage"
{#import "layouts/auth.jx" as Auth #}

<Auth title="Iniciar sesión">
  <h1>Inicia sesión</h1>
  <form>...</form>
</Auth>
```

## Layout con resaltado de navegación

Pasa la página actual para resaltar los enlaces de navegación activos:

```html+jinja title="components/layout.jx"
{#def title, current_page="" #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {{ assets.render_css() }}
</head>
<body>
  <nav>
    <a href="/" class="{{ 'active' if current_page == 'home' else '' }}">Inicio</a>
    <a href="/about" class="{{ 'active' if current_page == 'about' else '' }}">Acerca de</a>
    <a href="/contact" class="{{ 'active' if current_page == 'contact' else '' }}">Contacto</a>
  </nav>

  <main>{{ content }}</main>

  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="pages/about.jx"
{#import "layout.jx" as Layout #}

<Layout title="Acerca de nosotros" current_page="about">
  <h1>Acerca de nosotros</h1>
</Layout>
```

## Secciones de layout condicionales

```html+jinja title="components/layout.jx"
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
          <nav>Barra lateral por defecto</nav>
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
{# Layout completo con barra lateral #}
<Layout title="Panel">
  {% fill sidebar %}
    <nav>Barra lateral personalizada</nav>
  {% endfill %}
  <h1>Panel</h1>
</Layout>

{# Layout mínimo sin barra lateral #}
<Layout title="Iniciar sesión" show_sidebar={{ false }} show_footer={{ false }}>
  <form>Formulario de inicio de sesión</form>
</Layout>
```
