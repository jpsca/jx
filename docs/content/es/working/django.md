---
title: Trabaja con Django
description: Integra componentes de Jx con aplicaciones Django
---

[Django](https://www.djangoproject.com/){target=_blank} es un framework web de Python con todas las funcionalidades. Aunque Django tiene su propio motor de plantillas, también admite Jinja2 como backend alternativo. Esta guía muestra cómo integrar Jx con Django usando Jinja2.

## Resumen

La integración consta de tres pasos:

1. Configurar Django para usar Jinja2
2. Crear un entorno de Jinja2 con utilidades de Django
3. Crear un catálogo de Jx que use ese entorno

## Configuración básica

### Paso 1: Configura el backend de Jinja2

Agrega Jinja2 a tu ajuste `TEMPLATES`:

```python title="settings.py"
TEMPLATES = [
    # Mantén el motor de plantillas de Django para admin, etc.
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
    # Agrega Jinja2 para los componentes de Jx
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

### Paso 2: Crea el entorno de Jinja2

Crea un módulo que construya el entorno de Jinja2 con utilidades de Django:

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

### Paso 3: Crea el catálogo de Jx

Crea un módulo de catálogo que use el entorno de Jinja2:

```python title="myproject/components.py"
from django.conf import settings
from django.template import engines
from jx import Catalog

# Obtén el entorno de Jinja2 desde los motores de plantillas de Django
_jinja2_env = engines["jinja2"].env

# Crea el catálogo
catalog = Catalog(
    jinja_env=_jinja2_env,
    auto_reload=settings.DEBUG,
)
catalog.add_folder(settings.BASE_DIR / "components")
```

### Paso 4: Úsalo en las vistas

```python title="views.py"
from django.http import HttpResponse
from myproject.components import catalog


def home(request):
    return HttpResponse(catalog.render("pages/home.jx"))


def product_list(request):
    products = Product.objects.all()
    return HttpResponse(
        catalog.render("pages/products.jx", products=products)
    )
```

## Agrega utilidades de Django

### Globales esenciales

Extiende tu entorno de Jinja2 con utilidades de Django de uso común:

```python title="myproject/jinja2.py"
from django.conf import settings
from django.contrib import messages
from django.middleware.csrf import get_token
from django.templatetags.static import static
from django.urls import reverse
from django.utils.timezone import now
from jinja2 import Environment


def csrf_token(request):
    """Obtiene el token CSRF para la petición actual."""
    return get_token(request)


def get_messages(request):
    """Obtiene los mensajes para la petición actual."""
    return messages.get_messages(request)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        # Helpers de URL
        "static": static,
        "url": reverse,

        # Acceso a la configuración
        "settings": settings,
        "DEBUG": settings.DEBUG,

        # Utilidades
        "now": now,
    })
    return env
```

### Contexto específico de la petición

Para datos específicos de la petición como `csrf_token`, `user` y `messages`, pásalos al renderizar:

```python title="views.py"
from django.middleware.csrf import get_token
from django.contrib import messages as django_messages
from myproject.components import catalog


def render_component(request, component, **kwargs):
    """Helper para renderizar un componente con el contexto de la petición."""
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
        render_component(request, "pages/dashboard.jx", stats=get_stats())
    )
```

### Crea un atajo de renderizado

Por comodidad, crea un helper de respuesta similar al `render()` de Django:

```python title="myproject/shortcuts.py"
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.contrib import messages as django_messages
from myproject.components import catalog


def render(request, component, context=None, status=200, content_type=None):
    """
    Renderiza un componente Jx con el contexto de la petición de Django.

    Similar a django.shortcuts.render pero para componentes Jx.
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
    return render(request, "pages/product.jx", {"product": product})
```

## Protección CSRF

Crea un componente de input CSRF:

```html+jinja title="components/csrf-input.jx"
<input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
```

Úsalo en componentes de formulario:

```html+jinja title="components/form.jx"
{#import "./csrf-input.jx" as CsrfInput #}
{#def action, method="post" #}

<form action="{{ action }}" method="{{ method }}" {{ attrs.render() }}>
  {% if method.lower() != "get" %}
    <CsrfInput />
  {% endif %}
  {{ content }}
</form>
```

## Framework de mensajes

Crea un componente para mostrar los mensajes de Django:

```html+jinja title="components/messages.jx"
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

```html+jinja title="components/layout.jx"
{#import "./messages.jx" as Messages #}
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
    # ... lógica de guardado ...
    messages.success(request, "Item saved successfully!")
    return redirect("item_list")
```

## Autenticación

Accede al usuario y a los permisos en los componentes:

```html+jinja title="components/nav.jx"
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

### Verificación de permisos

```html+jinja title="components/admin-panel.jx"
{#def user #}

{% if user.is_authenticated and user.has_perm('myapp.change_product') %}
  <div class="admin-panel">
    <h3>Admin Actions</h3>
    <a href="{{ url('admin:myapp_product_changelist') }}">Manage Products</a>
  </div>
{% endif %}
```

## Archivos estáticos

### Usa el helper estático de Django

La función `static` está disponible en tu entorno:

```html+jinja title="components/layout.jx"
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

### Assets de componentes

Para el CSS y JS de los componentes, usa rutas relativas a tu carpeta de archivos estáticos:

```html+jinja title="components/card.jx"
{#css css/components/card.css #}
{#def title #}

<div {{ attrs.render(class="card") }}>
  <h3>{{ title }}</h3>
  {{ content }}
</div>
```

Luego renderízalos usando el helper `static`:

```html+jinja title="components/layout.jx"
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

## Vistas basadas en clases

Crea un mixin para vistas basadas en clases:

```python title="myproject/mixins.py"
from django.http import HttpResponse
from myproject.shortcuts import render


class JxMixin:
    """Mixin para vistas basadas en clases para renderizar componentes Jx."""

    component_name = None

    def render_component(self, context=None, **kwargs):
        """Renderiza el componente con el contexto dado."""
        return render(self.request, self.component_name, context, **kwargs)


class JxTemplateView(JxMixin):
    """Una vista que renderiza un componente Jx."""

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
    component_name = "pages/home.jx"


class ProductListView(JxMixin, View):
    component_name = "pages/products.jx"

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

## Configuración multi-app

Organiza componentes a través de varias apps de Django:

```python title="myproject/components.py"
from django.conf import settings
from django.template import engines
from jx import Catalog

_jinja2_env = engines["jinja2"].env

catalog = Catalog(
    jinja_env=_jinja2_env,
    auto_reload=settings.DEBUG,
)

# Componentes compartidos
catalog.add_folder(settings.BASE_DIR / "components")

# Componentes específicos de cada app con prefijos
catalog.add_folder(settings.BASE_DIR / "blog" / "components", prefix="blog")
catalog.add_folder(settings.BASE_DIR / "shop" / "components", prefix="shop")
```

```html+jinja title="uso"
{#import "layout.jx" as Layout #}
{#import "@blog/post-card.jx" as PostCard #}
{#import "@shop/product-card.jx" as ProductCard #}

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

## Páginas de error

Crea manejadores de error personalizados:

```python title="myproject/views.py"
from myproject.components import catalog
from django.http import HttpResponse


def handler404(request, exception):
    html = catalog.render(
        "errors/404.jx",
        globals={"request": request},
    )
    return HttpResponse(html, status=404)


def handler500(request):
    html = catalog.render("errors/500.jx")
    return HttpResponse(html, status=500)
```

```python title="urls.py"
handler404 = "myproject.views.handler404"
handler500 = "myproject.views.handler500"
```

```html+jinja title="components/errors/404.jx"
{#import "../layout.jx" as Layout #}

<Layout title="Page Not Found">
  <div class="error-page">
    <h1>404</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="{{ url('home') }}" class="btn">Go Home</a>
  </div>
</Layout>
```

## Ejemplo completo

Aquí tienes una configuración completa:

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
    return render(request, "pages/products.jx", {"products": products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "pages/product.jx", {"product": product})


def product_create(request):
    if request.method == "POST":
        # ... lógica de creación ...
        messages.success(request, "Product created!")
        return redirect("product_list")
    return render(request, "pages/product-form.jx")
```

## Configuración para producción

Para producción, desactiva la recarga automática:

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
    auto_reload=settings.DEBUG,  # False en producción
)
catalog.add_folder(settings.BASE_DIR / "components")
```
