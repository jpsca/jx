---
title: Home
---

<section markdown="1" class="home__code">
<div markdown="1">
**Before**: strongly coupled, verbose, chaotic 😵.

/// tab | view.html

```html+jinja
{% extends "layout.html" %}
{% block title %}My title{% endblock %}

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

///
</div>
<div markdown="1">
**After**: decoupled, re-usable, clean ✨.

/// tab | view.jinja

```html+jinja
{# import "layout.jinja" as Layout #}
{# import "product.jinja" as Product #}
{# import "pagination.jinja" as Pagination #}
{# def products #}

<Layout title="My title">
  {% for product in products %}
    <Product product={{ product }} />
  {% endfor %}
  <Pagination items={{ products }} />
</Layout>
```

///

/// tab | product.jinja

```html+jinja
{# import "card.jinja" as Card #}
{# def product #}

<Card class="product"
  title={{ product.title }}
  img_url={{ product.img_url }}
>
  <div class="product_price">{{ product.price }}</div>
  {{ product.description }}
</Card>
```

///

/// tab | card.jinja

```html+jinja
{# def title, img_url #}

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

///
</div>
</section>

<section markdown="1" class="home__actions">
  <p><a href="/docs/" class="btn btn--primary">Get started »</a></p>
</section>

<div markdown="1" class="bg">
<section markdown="1" class="home__spaghetti">

## Say no to spaghetti templates

![Spaghetti code](/assets/images/spaghetti_code.png){ .left width="300" }

Your Python code should be easy to read and maintain.

Yet, template code often breaks even **the most basic standards**: long methods, deep nesting, and mysterious variables everywhere.

With components, **everything is clear**: you know where each piece lives, what states it can be in, and exactly what data it needs.

Try replacing all your templates with components, or just start with one page.
</section>
</div>


<section markdown="1" class="home__better">
## Why components are better?

Compared to Jinja's `{% include %}` or macros:

### ✅ Clear Dependencies

All imports are listed at the top; you can see exactly what a component uses.

### ✅ Composable

Components wrap content naturally using the `{{ content }}` variable or the slots feature, making them easy to nest and combine.

### ✅ Type-Safe

Required arguments are enforced; if you forget to pass a required prop, you get an error at load time, not render time.

### ✅ Testable

Each component can be tested independently with different props and content.

### ✅ Portable

With relative imports, you can move entire folders of related components without breaking anything.

### ✅ Encapsulated Assets

Each component can declare its own CSS and JS files, which are automatically collected and rendered.
</section>

----