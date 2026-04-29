---
title: Trabaja con Flask
description: Integra componentes Jx con aplicaciones Flask
---

[Flask](https://flask.palletsprojects.com/){target=_blank} es un framework web ligero para Python. Jx se integra sin fricciones con Flask, dándote plantillas basadas en componentes mientras conservas el acceso a las utilidades de Flask como `url_for`, `flash` y la gestión de sesiones.

## Configuración básica

Crea un catálogo y úsalo en tus vistas:

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)
catalog = Catalog(
    "components/",
    auto_reload=app.debug,
)

@app.route("/")
def home():
    return catalog.render("pages/home.jx")
```

## Usa el entorno Jinja de Flask

Flask viene con su propio entorno Jinja que incluye globales útiles como `url_for`, `g`, `request`, `session` y `config`. Para acceder a ellos en tus componentes, comparte el entorno de Flask con Jx:

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)

# Comparte el entorno Jinja de Flask con Jx
catalog = Catalog(
    "components/",
    jinja_env=app.jinja_env,
    auto_reload=app.debug,
)
```

Ahora tus componentes tienen acceso a todas las utilidades de plantillas de Flask:

```html+jinja title="components/nav.jx"
<nav>
  <a href="{{ url_for('home') }}">Home</a>
  <a href="{{ url_for('about') }}">About</a>
  {% if session.get('user_id') %}
    <a href="{{ url_for('profile') }}">Profile</a>
    <a href="{{ url_for('logout') }}">Logout</a>
  {% else %}
    <a href="{{ url_for('login') }}">Login</a>
  {% endif %}
</nav>
```

Esto también aplica a cualquier extensión de Flask que agregue globales a las plantillas.

## Agrega globales de Flask manualmente

Si prefieres no compartir todo el entorno Jinja, pasa utilidades específicas de Flask como globales:

```python title="app.py"
from flask import Flask, url_for, request, g, session
from jx import Catalog

app = Flask(__name__)

catalog = Catalog(
    "components/",
    auto_reload=app.debug,
    url_for=url_for,
)
```

Para valores específicos de la petición, pásalos al renderizar:

```python title="views.py"
from flask import request, session, g

@app.route("/dashboard")
def dashboard():
    return catalog.render(
        "pages/dashboard.jx",
        globals={
            "request": request,
            "session": session,
            "g": g,
        },
        user=g.user,
    )
```

## Mensajes flash

Crea un componente para mostrar los mensajes flash de Flask:

```html+jinja title="components/flash-messages.jx"
{#css flash-messages.css #}

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-messages">
      {% for category, message in messages %}
        <div class="flash flash-{{ category }}">
          {{ message }}
          <button type="button" class="flash-close" onclick="this.parentElement.remove()">&times;</button>
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

```html+jinja title="components/layout.jx"
{#import "./flash-messages.jx" as FlashMessages #}
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {{ assets.render_css() }}
</head>
<body>
  <FlashMessages />
  <main>
    {{ content }}
  </main>
  {{ assets.render_js() }}
</body>
</html>
```

```python title="views.py"
from flask import flash, redirect, url_for

@app.route("/save", methods=["POST"])
def save():
    # ... lógica para guardar ...
    flash("Changes saved successfully!", "success")
    return redirect(url_for("dashboard"))
```

## Protección CSRF

### Con Flask-WTF

Si estás usando Flask-WTF para protección CSRF, crea un componente para el token:

```html+jinja title="components/csrf-input.jx"
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

Úsalo en formularios:

```html+jinja title="components/login-form.jx"
{#import "./csrf-input.jx" as CsrfInput #}
{#def action #}

<form method="post" action="{{ action }}" {{ attrs.render() }}>
  <CsrfInput />
  {{ content }}
</form>
```

```html+jinja title="uso"
{#import "login-form.jx" as Form #}
{#import "input.jx" as Input #}

<Form action="{{ url_for('login') }}">
  <Input name="email" type="email" label="Email" required />
  <Input name="password" type="password" label="Password" required />
  <button type="submit">Login</button>
</Form>
```

## Blueprints

Jx funciona bien con los blueprints de Flask. Puedes usar un único catálogo compartido o crear catálogos separados por blueprint:

### Catálogo compartido

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)
catalog = Catalog("components/", jinja_env=app.jinja_env, auto_reload=app.debug)

# Haz el catálogo accesible desde los blueprints
app.catalog = catalog
```

```python title="blueprints/blog.py"
from flask import Blueprint, current_app

blog = Blueprint("blog", __name__, url_prefix="/blog")

@blog.route("/")
def index():
    posts = get_posts()
    return current_app.catalog.render("blog/index.jx", posts=posts)

@blog.route("/<slug>")
def post(slug):
    post = get_post_by_slug(slug)
    return current_app.catalog.render("blog/post.jx", post=post)
```

### Componentes específicos por blueprint

Agrega carpetas de componentes con prefijos para cada blueprint:

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)
catalog = Catalog(jinja_env=app.jinja_env, auto_reload=app.debug)

# Componentes compartidos
catalog.add_folder("components/")

# Componentes específicos por blueprint
catalog.add_folder("blueprints/blog/components/", prefix="blog")
catalog.add_folder("blueprints/admin/components/", prefix="admin")

app.catalog = catalog
```

```html+jinja title="blueprints/blog/components/post-card.jx"
{#import "card.jx" as Card #}
{#def post #}

<Card class="post-card">
  <h2><a href="{{ url_for('blog.post', slug=post.slug) }}">{{ post.title }}</a></h2>
  <p>{{ post.excerpt }}</p>
</Card>
```

```html+jinja title="uso en plantillas del blog"
{#import "@blog/post-card.jx" as PostCard #}

{% for post in posts %}
  <PostCard post={{ post }} />
{% endfor %}
```

## Procesadores de contexto

Usa los procesadores de contexto de Flask para que ciertas variables estén disponibles en todos los componentes:

```python title="app.py"
@app.context_processor
def inject_globals():
    return {
        "site_name": "My App",
        "current_year": 2026,
        "is_authenticated": lambda: session.get("user_id") is not None,
    }
```

Estos están disponibles automáticamente al usar el entorno Jinja de Flask:

```html+jinja title="components/footer.jx"
<footer>
  <p>&copy; {{ current_year }} {{ site_name }}</p>
</footer>
```

## Archivos estáticos

Usa el `url_for` de Flask para referenciar archivos estáticos:

```html+jinja title="components/layout.jx"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  <link rel="icon" href="{{ url_for('static', filename='favicon.ico') }}">
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

Para los assets de los componentes, puedes usar rutas absolutas que apunten a tu carpeta de archivos estáticos:

```html+jinja title="components/card.jx"
{#css /static/css/card.css #}
{#def title #}

<div {{ attrs.render(class="card") }}>
  <h3>{{ title }}</h3>
  {{ content }}
</div>
```

O usa `url_for` en un loop de renderizado personalizado:

```html+jinja title="components/layout.jx"
<head>
  {% for css_file in assets.collect_css() %}
    <link rel="stylesheet" href="{{ url_for('static', filename=css_file) }}">
  {% endfor %}
</head>
```

## Ejemplo completo

Aquí tienes una aplicación Flask completa usando Jx:

```python title="app.py"
from flask import Flask, redirect, url_for, flash, session, g, request
from flask_wtf.csrf import CSRFProtect
from jx import Catalog

app = Flask(__name__)
app.secret_key = "your-secret-key"
csrf = CSRFProtect(app)

# Crea catálogo con el entorno Jinja de Flask
catalog = Catalog(
    "components/",
    jinja_env=app.jinja_env,
    auto_reload=app.debug,
)

@app.before_request
def load_user():
    user_id = session.get("user_id")
    g.user = get_user_by_id(user_id) if user_id else None

@app.route("/")
def home():
    return catalog.render("pages/home.jx")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form["email"], request.form["password"])
        if user:
            session["user_id"] = user.id
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "error")
    return catalog.render("pages/login.jx")

@app.route("/dashboard")
def dashboard():
    if not g.user:
        return redirect(url_for("login"))
    return catalog.render("pages/dashboard.jx", user=g.user)

@app.errorhandler(404)
def not_found(e):
    return catalog.render("errors/404.jx"), 404

if __name__ == "__main__":
    app.run(debug=True)
```

```html+jinja title="components/layout.jx"
{#import "./nav.jx" as Nav #}
{#import "./flash-messages.jx" as FlashMessages #}
{#import "./footer.jx" as Footer #}
{#css layout.css #}
{#def title #}

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }} | My App</title>
  {{ assets.render_css() }}
</head>
<body>
  <Nav />
  <FlashMessages />
  <main>
    {{ content }}
  </main>
  <Footer />
  {{ assets.render_js() }}
</body>
</html>
```

```html+jinja title="components/pages/dashboard.jx"
{#import "../layout.jx" as Layout #}
{#import "../card.jx" as Card #}
{#def user #}

<Layout title="Dashboard">
  <h1>Welcome, {{ user.name }}!</h1>

  <div class="dashboard-grid">
    <Card title="Profile">
      <p>{{ user.email }}</p>
      <a href="{{ url_for('profile') }}">Edit Profile</a>
    </Card>

    <Card title="Settings">
      <a href="{{ url_for('settings') }}">Manage Settings</a>
    </Card>
  </div>
</Layout>
```

## Configuración para producción

Para producción, desactiva la recarga automática:

```python title="app.py"
import os

app = Flask(__name__)
is_production = os.environ.get("FLASK_ENV") == "production"

catalog = Catalog(
    "components/", 
    jinja_env=app.jinja_env,
    auto_reload=not is_production,
)
```
