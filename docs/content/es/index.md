---
title: Inicio
---

::::::: div home__section home__code
::::: div
**Antes**: fuertemente acoplado, verboso, caótico 😵.

::: tab | view.html

```html+jinja
{% extends "layout.html" %}
{% block title %}Mi título{% endblock %}

{% block body %}
  {% for prod in products %}
  <div class="card product">
    <div class="card_header">
      <img src="{{ url_for(
        'static',
        prod.img_url or 'default.png'
      ) }}" />
      <h1>{{ prod.title }}</h1>
    </div>
    <div class="card_content">
      <div class="product_price">{{ prod.price }}</div>
      {{ prod.description }}
    </div>
  </div>
  {% endfor %}
  {% with items=products %}
    {% include "pagination.html" %}
  {% endwith %}
{% endblock %}
```

:::
:::::

::::: div
**Después**: desacoplado, reutilizable, limpio ✨.

::: tab | view.jx

```html+jinja
{#import "layout.jx" as Layout #}
{#import "product.jx" as Product #}
{#import "pagination.jx" as Pagination #}
{#def products #}

<Layout title="Mi título">
  {% for product in products %}
    <Product product={{ product }} />
  {% endfor %}
  <Pagination items={{ products }} />
</Layout>
```

:::

::: tab | product.jx

```html+jinja
{#import "card.jx" as Card #}
{#def product #}

<Card class="product"
  title={{ product.title }}
  img_url={{ product.img_url }}
>
  <div class="product_price">{{ product.price }}</div>
  {{ product.description }}
</Card>
```

:::

::: tab | card.jx

```html+jinja
{#def title, img_url #}

<div {{ attrs.render(class="card") }}>
  <div class="card_header">
    <img src="{{ url_for('static', img_url) }}" />
    <h1>{{ title }}</h1>
  </div>
  <div class="card_content">
    {{ content }}
  </div>
</div>
```

:::
:::::
:::::::

::::: div home__section home__actions
[Comenzar »](/docs/){ .btn .btn--primary }
:::::

:::::: div bg
::::: div home__section home__spaghetti
## Dile no a las plantillas tipo espagueti

![Código espagueti](/assets/images/spaghetti_code.png){ .left width="300" }

Tu código Python debería ser fácil de leer y mantener.

Sin embargo, el código de las plantillas suele incumplir **incluso los estándares más básicos**: métodos largos, anidamiento profundo y variables misteriosas por todas partes.

Con componentes, **todo es claro**: sabes dónde vive cada pieza, en qué estados puede estar y exactamente qué datos necesita.

Prueba reemplazar todas tus plantillas con componentes, o simplemente comienza con una sola página.
:::::
::::::

::::: div home__section home__better
## ¿Por qué los componentes son mejores?

Comparados con `{% include %}` o las macros de Jinja:

### ✅ Dependencias claras

Todas las importaciones están listadas al principio; puedes ver exactamente qué usa un componente.

### ✅ Componibles

Los componentes envuelven contenido de forma natural usando la variable `{{ content }}` o la funcionalidad de slots, lo que hace fácil anidarlos y combinarlos.

### ✅ Con seguridad de tipos

Los argumentos requeridos se imponen; si olvidas pasar un prop requerido, obtienes un error al cargar, no al renderizar.

### ✅ Testeables

Cada componente puede ser probado de forma independiente con diferentes props y contenido.

### ✅ Portables

Con importaciones relativas, puedes mover carpetas enteras de componentes relacionados sin romper nada.

### ✅ Assets encapsulados

Cada componente puede declarar sus propios archivos CSS y JS, que se recolectan y renderizan automáticamente.
:::::

----