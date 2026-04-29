---
title: Assets
description: Manejo de CSS y JavaScript en componentes
---

Cualquier componente puede declarar las URLs de los archivos CSS y JavaScript que utiliza. Jx recolecta automáticamente estos assets de todos los componentes que uses y proporciona funciones simples para renderizarlos.

## ¿Por qué assets por componente?

Los enfoques tradicionales ponen todo el CSS y JS en archivos globales. Esto tiene problemas:

- **Difícil de mantener**: ¿Qué estilos pertenecen a qué componente?
- **Sobrecarga**: Cargas todo aunque solo uses unos pocos componentes
- **Acoplamiento**: No puedes mover/compartir componentes sin rastrear sus estilos

Con assets por componente:

- **Portabilidad**: Copias una carpeta de componente y sus assets vienen con ella
- **Claridad**: Cada componente declara lo que necesita
- **Rendimiento**: Solo cargas los assets de los componentes que realmente usas
- **Pruebas**: Pruebas los estilos y el comportamiento del componente juntos

## Declarando assets

Usa los comentarios `{#css ... #}` y `{#js ... #}` al inicio de tu componente:

```html+jinja title="components/card.jx"
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

Múltiples archivos se separan por comas. Cada archivo puede ser:

- **Relativo**: `card.css` (relativo a tus archivos estáticos)
- **Ruta absoluta**: `/static/styles/global.css`
- **URL**: `https://cdn.example.com/library.js`

## El global `assets`

Cuando renderizas un componente, Jx proporciona un objeto global `assets` con métodos para recolectar y renderizar assets.

### `assets.render()`

El enfoque más simple; renderiza tanto CSS como JS:

```html+jinja title="components/layout.jx"
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

Esto recolecta los assets del componente layout y todos los componentes que importa, luego los renderiza como etiquetas `<link>` y `<script>`.

### `assets.render_css()`

Renderiza solo CSS como etiquetas `<link>`:

```html+jinja
<head>
  <title>My App</title>
  {{ assets.render_css() }}
</head>
```

**Salida:**

```html
<link rel="stylesheet" href="layout.css">
<link rel="stylesheet" href="card.css">
<link rel="stylesheet" href="button.css">
```

### `assets.render_js(module=True, defer=True)`

Renderiza JavaScript como etiquetas `<script>`:

```html+jinja
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
```

**Salida (por defecto):**

```html
<script type="module" src="layout.js"></script>
<script type="module" src="card.js"></script>
```

**Opciones:**

- `module=True` (por defecto): Agrega `type="module"`
- `module=False`: Scripts regulares
- `defer=True`: Agrega el atributo `defer` (solo cuando `module=False`)

```html+jinja
{# Módulos ES (por defecto) #}
{{ assets.render_js() }}
{# <script type="module" src="..."></script> #}

{# Scripts regulares con defer #}
{{ assets.render_js(module=False) }}
{# <script src="..." defer></script> #}

{# Scripts regulares sin defer #}
{{ assets.render_js(module=False, defer=False) }}
{# <script src="..."></script> #}
```

## Métodos de recolección

Para mayor control, usa los métodos de recolección:

### `assets.collect_css()`

Devuelve una lista de todas las URLs de archivos CSS:

```html+jinja
{% for url in assets.collect_css() %}
  <link rel="stylesheet" href="{{ url }}">
{% endfor %}
```

### `assets.collect_js()`

Devuelve una lista de todas las URLs de archivos JS:

```html+jinja
{% for url in assets.collect_js() %}
  <script type="module" src="{{ url }}"></script>
{% endfor %}
```

## Cómo funciona la recolección de assets

Jx recolecta los assets recorriendo el árbol de componentes:

1. Comienza con el componente raíz que estás renderizando
2. Recolecta sus declaraciones de CSS y JS
3. Recolecta recursivamente desde cada componente importado
4. Deduplica (cada archivo aparece solo una vez)
5. Devuelve en orden de dependencia

**Ejemplo:**

```html+jinja title="page.jx"
{#import "./layout.jx" as Layout #}
{#import "./card.jx" as Card #}
{#css page.css #}

<Layout>
  <Card>...</Card>
</Layout>
```

```html+jinja title="layout.jx"
{#import "./header.jx" as Header #}
{#css layout.css #}

<div>
  <Header />
  {{ content }}
</div>
```

```html+jinja title="header.jx"
{#css header.css #}
<header>...</header>
```

```html+jinja title="card.jx"
{#css card.css #}
<div class="card">{{ content }}</div>
```

**CSS recolectado (en orden):**

```
page.css
layout.css
header.css
card.css
```

Los assets de cada componente importado se recolectan recursivamente.

## URLs de assets

Jx no procesa ni reescribe las URLs de los assets; se usan exactamente como las escribes.

### URLs relativas

```html+jinja
{#css card.css #}
{#js card.js #}
```

**Salida:**

```html
<link rel="stylesheet" href="card.css">
<script type="module" src="card.js"></script>
```

Cómo se resuelvan estas URLs depende de la ruta base de tu HTML y la configuración del servidor.

## Organizando los assets

### Opción 1: Mantén los assets junto a los componentes

```
components/
  card/
    card.jx
    card.css
    card.js
  button/
    button.jx
    button.css
    button.js
```

```html+jinja title="components/card/card.jx"
{#css /static/components/card/card.css #}
{#js /static/components/card/card.js #}
```

### Opción 2: Pon los assets de los componentes en una carpeta estática

Mantén los componentes y los assets separados:

```
components/
  card.jx
  button.jx
static/
  css/
    card.css
    button.css
  js/
    card.js
    button.js
```

Usa rutas absolutas:

```html+jinja title="components/card.jx"
{#css /static/css/card.css #}
{#js /static/js/card.js #}
```

```html+jinja title="components/layout.jx"
{{ assets.render() }}
```

O relativas y usa tu framework web para resolverlas:

```html+jinja title="components/card.jx"
{#css css/card.css #}
{#js js/card.js #}
```

```html+jinja title="components/layout.jx"
{% for name in assets.collect_css() %}
  <link rel="stylesheet" href="{{ url_for('static', filename=name) }}">
{% endfor %}
{% for name in assets.collect_js() %}
  <script type="module" src="{{ url_for('static', filename=name) }}"></script>
{% endfor %}
```

### Opción 3: Integración con herramientas de build

Usa Vite, Webpack u otro bundler:

```html+jinja title="components/card.jx"
{#css /dist/card.css #}
{#js /dist/card.js #}
```

Tu herramienta de build generará los archivos con hashes para invalidar la caché:

```html
<link rel="stylesheet" href="/dist/card.abc123.css">
<script type="module" src="/dist/card.def456.js"></script>
```

## Buenas prácticas

### 1. Declara las dependencias de terceros

```html+jinja
{# ✅ Bien - dependencias explícitas #}
{#css https://cdn.example.com/library.css #}
{#import "./component-using-library.jx" as Component #}
```

### 2. Mantén los archivos de assets pequeños

Cada componente debería tener estilos y scripts enfocados:

```html+jinja
{# ✅ Bien - componente enfocado #}
{#css button.css #}  {# ~2KB #}
{#js button.js #}    {# ~1KB #}

{# ❌ Mal - demasiadas cosas #}
{#css button-and-everything-else.css #}  {# ~50KB #}
```

### 3. Usa CSS con scope


```css
/* ✅ Bien - con scope para el componente */
.Card {
  padding: 1rem;
}
.Card__title {
  font-size: 1.5rem;
}

/* ❌ Mal - afectará a todo */
h3 {
  font-size: 1.5rem;
}
```

Los navegadores modernos admiten [CSS nesting](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_nesting):

```css
.Card {
  padding: 1rem;

  & h3 {
    font-size: 1.5rem;
  }
}
```

## No se requiere middleware

Jx no requiere middleware para servir los assets de los componentes. Los sirves como prefieras:

- **Archivos estáticos**: Configura tu framework web para servir desde `static/`
- **CDN**: Sube a S3/CloudFront y referencia esas URLs
- **Herramientas de build**: Usa Vite/Webpack para empaquetar y servir
- **Proxy inverso**: Nginx/Caddy sirven archivos estáticos

Jx solo recolecta las URLs que declaras y las renderiza como etiquetas.


## Consideraciones de rendimiento

### Deduplicación de assets

Jx deduplica automáticamente los assets. Si múltiples componentes declaran el mismo archivo CSS, se incluye solo una vez:

```html+jinja
{# card.jx usa common.css #}
{# button.jx usa common.css #}
{# page.jx usa ambos #}
```

Resulta en:

```html
<link rel="stylesheet" href="common.css">  <!-- ¡Solo una vez! -->
<link rel="stylesheet" href="card.css">
<link rel="stylesheet" href="button.css">
```

### Orden de carga

Los assets se recolectan en orden de dependencia:
1. Primero los assets del componente padre
2. Luego los assets de los componentes importados
3. En el orden en que se importan

Esto asegura una resolución correcta de la cascada y las dependencias.

