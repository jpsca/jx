---
title: Working with Django
description: Integrating Jx components with Django applications
---

[Django](https://www.djangoproject.com/){target=_blank} is a full-featured Python web framework. While Django has its own template engine, it also supports Jinja2 as an alternative backend. This guide shows how to integrate Jx with Django using Jinja2.

## Overview

The integration involves three steps:

1. Configure Django to use Jinja2
2. Create a Jinja2 environment with Django utilities
3. Create a Jx catalog that uses this environment

## Basic Setup

### Step 1: Configure Jinja2 Backend

Add Jinja2 to your `TEMPLATES` setting:

```python title="settings.py"
TEMPLATES = [
    # Keep Django's template engine for admin, etc.
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    # Add Jinja2 for Jx components
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "components"],
        "APP_DIRS": False,
        "OPTIONS": {
            "environment": "myproject.jinja2.environment",
        },
    },
]
```

### Step 2: Create the Jinja2 Environment

Create a module that builds the Jinja2 environment with Django utilities:

```python title="myproject/jinja2.py"
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        "static": static,
        "url": reverse,
    })
    return env
```

### Step 3: Create the Jx Catalog

Create a catalog module that uses the Jinja2 environment:

```python title="myproject/components.py"
from django.conf import settings
from django.template import engines
from jx import Catalog

# Get the Jinja2 environment from Django's template engines
_jinja2_env = engines["jinja2"].env

# Create the catalog
catalog = Catalog(
    jinja_env=_jinja2_env,
    auto_reload=settings.DEBUG,
)
catalog.add_folder(settings.BASE_DIR / "components")
```

### Step 4: Use in Views

```python title="views.py"
from django.http import HttpResponse
from myproject.components import catalog


def home(request):
    return HttpResponse(catalog.render("pages/home.jinja"))


def product_list(request):
    products = Product.objects.all()
    return HttpResponse(
        catalog.render("pages/products.jinja", products=products)
    )
```

## Adding Django Utilities

### Essential Globals

Extend your Jinja2 environment with commonly needed Django utilities:

```python title="myproject/jinja2.py"
from django.conf import settings
from django.contrib import messages
from django.middleware.csrf import get_token
from django.templatetags.static import static
from django.urls import reverse
from django.utils.timezone import now
from jinja2 import Environment


def csrf_token(request):
    """Get CSRF token for the current request."""
    return get_token(request)


def get_messages(request):
    """Get messages for the current request."""
    return messages.get_messages(request)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        # URL helpers
        "static": static,
        "url": reverse,

        # Settings access
        "settings": settings,
        "DEBUG": settings.DEBUG,

        # Utilities
        "now": now,
    })
    return env
```

### Request-Specific Context

For request-specific data like `csrf_token`, `user`, and `messages`, pass them when rendering:

```python title="views.py"
from django.middleware.csrf import get_token
from django.contrib import messages as django_messages
from myproject.components import catalog


def render_component(request, component, **kwargs):
    """Helper to render a component with request context."""
    return catalog.render(
        component,
        globals={
            "request": request,
            "user": request.user,
            "csrf_token": get_token(request),
            "messages": django_messages.get_messages(request),
        },
        **kwargs,
    )


def dashboard(request):
    return HttpResponse(
        render_component(request, "pages/dashboard.jinja", stats=get_stats())
    )
```

### Creating a Render Shortcut

For convenience, create a response helper similar to Django's `render()`:

```python title="myproject/shortcuts.py"
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.contrib import messages as django_messages
from myproject.components import catalog


def render(request, component, context=None, status=200, content_type=None):
    """
    Render a Jx component with Django request context.

    Similar to django.shortcuts.render but for Jx components.
    """
    context = context or {}

    html = catalog.render(
        component,
        globals={
            "request": request,
            "user": request.user,
            "csrf_token": get_token(request),
            "messages": django_messages.get_messages(request),
            "perms": request.user.get_all_permissions() if request.user.is_authenticated else set(),
        },
        **context,
    )

    return HttpResponse(html, status=status, content_type=content_type)
```

```python title="views.py"
from myproject.shortcuts import render


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "pages/product.jinja", {"product": product})
```

## CSRF Protection

Create a CSRF input component:

```html+jinja title="components/csrf-input.jinja"
<input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
```

Use it in form components:

```html+jinja title="components/form.jinja"
{#import "./csrf-input.jinja" as CsrfInput #}
{#def action, method="post" #}

<form action="{{ action }}" method="{{ method }}" {{ attrs.render() }}>
  {% if method.lower() != "get" %}
    <CsrfInput />
  {% endif %}
  {{ content }}
</form>
```

## Messages Framework

Create a component to display Django messages:

```html+jinja title="components/messages.jinja"
{#css messages.css #}

{% if messages %}
  <div class="messages">
    {% for message in messages %}
      <div class="message message-{{ message.tags }}">
        {{ message }}
        <button type="button" class="message-close" onclick="this.parentElement.remove()">&times;</button>
      </div>
    {% endfor %}
  </div>
{% endif %}
```

```html+jinja title="components/layout.jinja"
{#import "./messages.jinja" as Messages #}
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {{ assets.render_css() }}
</head>
<body>
  <Messages />
  <main>
    {{ content }}
  </main>
  {{ assets.render_js() }}
</body>
</html>
```

```python title="views.py"
from django.contrib import messages

def save_item(request):
    # ... save logic ...
    messages.success(request, "Item saved successfully!")
    return redirect("item_list")
```

## Authentication

Access user and permissions in components:

```html+jinja title="components/nav.jinja"
<nav>
  <a href="{{ url('home') }}">Home</a>

  {% if user.is_authenticated %}
    <a href="{{ url('profile') }}">{{ user.username }}</a>

    {% if user.is_staff %}
      <a href="{{ url('admin:index') }}">Admin</a>
    {% endif %}

    <form action="{{ url('logout') }}" method="post" class="inline">
      <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
      <button type="submit">Logout</button>
    </form>
  {% else %}
    <a href="{{ url('login') }}">Login</a>
    <a href="{{ url('register') }}">Register</a>
  {% endif %}
</nav>
```

### Permission Checks

```html+jinja title="components/admin-panel.jinja"
{#def user #}

{% if user.is_authenticated and user.has_perm('myapp.change_product') %}
  <div class="admin-panel">
    <h3>Admin Actions</h3>
    <a href="{{ url('admin:myapp_product_changelist') }}">Manage Products</a>
  </div>
{% endif %}
```

## Static Files

### Using Django's Static Helper

The `static` function is available in your environment:

```html+jinja title="components/layout.jinja"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  <link rel="icon" href="{{ static('favicon.ico') }}">
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

### Component Assets

For component CSS and JS, use paths relative to your static folder:

```html+jinja title="components/card.jinja"
{#css css/components/card.css #}
{#def title #}

<div {{ attrs.render(class="card") }}>
  <h3>{{ title }}</h3>
  {{ content }}
</div>
```

Then render them using the `static` helper:

```html+jinja title="components/layout.jinja"
<head>
  {% for css_file in assets.collect_css() %}
    <link rel="stylesheet" href="{{ static(css_file) }}">
  {% endfor %}
</head>
<body>
  {{ content }}
  {% for js_file in assets.collect_js() %}
    <script type="module" src="{{ static(js_file) }}"></script>
  {% endfor %}
</body>
```

## Class-Based Views

Create a mixin for class-based views:

```python title="myproject/mixins.py"
from django.http import HttpResponse
from myproject.shortcuts import render


class JxMixin:
    """Mixin for class-based views to render Jx components."""

    component_name = None

    def render_component(self, context=None, **kwargs):
        """Render the component with the given context."""
        return render(self.request, self.component_name, context, **kwargs)


class JxTemplateView(JxMixin):
    """A view that renders a Jx component."""

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_component(context)

    def get_context_data(self, **kwargs):
        return kwargs
```

```python title="views.py"
from django.views import View
from myproject.mixins import JxMixin, JxTemplateView


class HomeView(JxTemplateView):
    component_name = "pages/home.jinja"


class ProductListView(JxMixin, View):
    component_name = "pages/products.jinja"

    def get(self, request):
        products = Product.objects.all()
        return self.render_component({"products": products})
```

```python title="urls.py"
from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("products/", views.ProductListView.as_view(), name="products"),
]
```

## Multi-App Setup

Organize components across Django apps:

```python title="myproject/components.py"
from django.conf import settings
from django.template import engines
from jx import Catalog

_jinja2_env = engines["jinja2"].env

catalog = Catalog(
    jinja_env=_jinja2_env,
    auto_reload=settings.DEBUG,
)

# Shared components
catalog.add_folder(settings.BASE_DIR / "components")

# App-specific components with prefixes
catalog.add_folder(settings.BASE_DIR / "blog" / "components", prefix="blog")
catalog.add_folder(settings.BASE_DIR / "shop" / "components", prefix="shop")
```

```html+jinja title="usage"
{#import "layout.jinja" as Layout #}
{#import "@blog/post-card.jinja" as PostCard #}
{#import "@shop/product-card.jinja" as ProductCard #}

<Layout title="Home">
  <section>
    <h2>Latest Posts</h2>
    {% for post in posts %}
      <PostCard post={{ post }} />
    {% endfor %}
  </section>

  <section>
    <h2>Featured Products</h2>
    {% for product in products %}
      <ProductCard product={{ product }} />
    {% endfor %}
  </section>
</Layout>
```

## Error Pages

Create custom error handlers:

```python title="myproject/views.py"
from myproject.components import catalog
from django.http import HttpResponse


def handler404(request, exception):
    html = catalog.render(
        "errors/404.jinja",
        globals={"request": request},
    )
    return HttpResponse(html, status=404)


def handler500(request):
    html = catalog.render("errors/500.jinja")
    return HttpResponse(html, status=500)
```

```python title="urls.py"
handler404 = "myproject.views.handler404"
handler500 = "myproject.views.handler500"
```

```html+jinja title="components/errors/404.jinja"
{#import "../layout.jinja" as Layout #}

<Layout title="Page Not Found">
  <div class="error-page">
    <h1>404</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="{{ url('home') }}" class="btn">Go Home</a>
  </div>
</Layout>
```

## Complete Example

Here's a complete setup:

```python title="myproject/jinja2.py"
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        "static": static,
        "url": reverse,
        "DEBUG": settings.DEBUG,
    })
    return env
```

```python title="myproject/components.py"
from django.conf import settings
from django.template import engines
from jx import Catalog

_jinja2_env = engines["jinja2"].env

catalog = Catalog(
    jinja_env=_jinja2_env,
    auto_reload=settings.DEBUG,
)
catalog.add_folder(settings.BASE_DIR / "components")
```

```python title="myproject/shortcuts.py"
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.contrib import messages as django_messages
from .components import catalog


def render(request, component, context=None, status=200):
    context = context or {}
    html = catalog.render(
        component,
        globals={
            "request": request,
            "user": request.user,
            "csrf_token": get_token(request),
            "messages": django_messages.get_messages(request),
        },
        **context,
    )
    return HttpResponse(html, status=status)
```

```python title="views.py"
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from myproject.shortcuts import render
from .models import Product


def product_list(request):
    products = Product.objects.all()
    return render(request, "pages/products.jinja", {"products": products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "pages/product.jinja", {"product": product})


def product_create(request):
    if request.method == "POST":
        # ... create logic ...
        messages.success(request, "Product created!")
        return redirect("product_list")
    return render(request, "pages/product-form.jinja")
```

## Production Settings

For production, disable auto-reload:

```python title="settings.py"
# settings.py
DEBUG = False
```

```python title="myproject/components.py"
from django.conf import settings
from django.template import engines
from jx import Catalog

_jinja2_env = engines["jinja2"].env

catalog = Catalog(
    jinja_env=_jinja2_env,
    auto_reload=settings.DEBUG,  # False in production
)
catalog.add_folder(settings.BASE_DIR / "components")
```
