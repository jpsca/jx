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
  <Paginator items={{ products }} />
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
[Get started »](/docs/){ .button }
</section>

<div markdown="1" class="bg">
<section markdown="1" class="home__spaghetti">
## Say no to spaghetti templates

![Spaguetti code](/assets/images/spaghetti_code.png){ .left width="300" }

Your Python code should be easy to read and maintain.

Yet, template code often breaks even **the most basic standards**: long methods, deep nesting, and mysterious variables everywhere.

With components, **everything is clear**: you know where each piece lives, what states it can be in, and exactly what data it needs.

Try replacing all your templates with components, or just start with one page.
</section>
</div>