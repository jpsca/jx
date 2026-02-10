---
title: Working with Flask
description: Integrating Jx components with Flask applications
---

[Flask](https://flask.palletsprojects.com/){target=_blank} is a lightweight Python web framework. Jx integrates seamlessly with Flask, giving you component-based templates while keeping access to Flask's utilities like `url_for`, `flash`, and session management.

## Basic Setup

Create a catalog and use it in your views:

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
    return catalog.render("pages/home.jinja")
```

## Using Flask's Jinja Environment

Flask comes with its own Jinja environment that includes useful globals like `url_for`, `g`, `request`, `session`, and `config`. To access these in your components, share Flask's environment with Jx:

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)

# Share Flask's Jinja environment with Jx
catalog = Catalog(
    "components/",
    jinja_env=app.jinja_env,
    auto_reload=app.debug,
)
```

Now your components have access to all Flask template utilities:

```html+jinja title="components/nav.jinja"
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

This is also true for any Flask extension that add globals to the templates.

## Adding Flask Globals Manually

If you prefer not to share the entire Jinja environment, pass specific Flask utilities as globals:

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

For request-specific values, pass them when rendering:

```python title="views.py"
from flask import request, session, g

@app.route("/dashboard")
def dashboard():
    return catalog.render(
        "pages/dashboard.jinja",
        globals={
            "request": request,
            "session": session,
            "g": g,
        },
        user=g.user,
    )
```

## Flash Messages

Create a component to display Flask flash messages:

```html+jinja title="components/flash-messages.jinja"
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

```html+jinja title="components/layout.jinja"
{#import "./flash-messages.jinja" as FlashMessages #}
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
    # ... save logic ...
    flash("Changes saved successfully!", "success")
    return redirect(url_for("dashboard"))
```

## CSRF Protection

### With Flask-WTF

If you're using Flask-WTF for CSRF protection, create a component for the token:

```html+jinja title="components/csrf-input.jinja"
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

Use it in forms:

```html+jinja title="components/login-form.jinja"
{#import "./csrf-input.jinja" as CsrfInput #}
{#def action #}

<form method="post" action="{{ action }}" {{ attrs.render() }}>
  <CsrfInput />
  {{ content }}
</form>
```

```html+jinja title="usage"
{#import "login-form.jinja" as Form #}
{#import "input.jinja" as Input #}

<Form action="{{ url_for('login') }}">
  <Input name="email" type="email" label="Email" required />
  <Input name="password" type="password" label="Password" required />
  <button type="submit">Login</button>
</Form>
```

## Blueprints

Jx works well with Flask blueprints. You can use a single shared catalog or create separate catalogs per blueprint:

### Shared Catalog

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)
catalog = Catalog("components/", jinja_env=app.jinja_env, auto_reload=app.debug)

# Make catalog available to blueprints
app.catalog = catalog
```

```python title="blueprints/blog.py"
from flask import Blueprint, current_app

blog = Blueprint("blog", __name__, url_prefix="/blog")

@blog.route("/")
def index():
    posts = get_posts()
    return current_app.catalog.render("blog/index.jinja", posts=posts)

@blog.route("/<slug>")
def post(slug):
    post = get_post_by_slug(slug)
    return current_app.catalog.render("blog/post.jinja", post=post)
```

### Blueprint-Specific Components

Add component folders with prefixes for each blueprint:

```python title="app.py"
from flask import Flask
from jx import Catalog

app = Flask(__name__)
catalog = Catalog(jinja_env=app.jinja_env, auto_reload=app.debug)

# Shared components
catalog.add_folder("components/")

# Blueprint-specific components
catalog.add_folder("blueprints/blog/components/", prefix="blog")
catalog.add_folder("blueprints/admin/components/", prefix="admin")

app.catalog = catalog
```

```html+jinja title="blueprints/blog/components/post-card.jinja"
{#import "card.jinja" as Card #}
{#def post #}

<Card class="post-card">
  <h2><a href="{{ url_for('blog.post', slug=post.slug) }}">{{ post.title }}</a></h2>
  <p>{{ post.excerpt }}</p>
</Card>
```

```html+jinja title="usage in blog templates"
{#import "@blog/post-card.jinja" as PostCard #}

{% for post in posts %}
  <PostCard post={{ post }} />
{% endfor %}
```

## Context Processors

Use Flask's context processors to make variables available to all components:

```python title="app.py"
@app.context_processor
def inject_globals():
    return {
        "site_name": "My App",
        "current_year": 2025,
        "is_authenticated": lambda: session.get("user_id") is not None,
    }
```

These are automatically available when using Flask's Jinja environment:

```html+jinja title="components/footer.jinja"
<footer>
  <p>&copy; {{ current_year }} {{ site_name }}</p>
</footer>
```

## Static Files

Use Flask's `url_for` to reference static files:

```html+jinja title="components/layout.jinja"
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

For component assets, you can use absolute paths that map to your static folder:

```html+jinja title="components/card.jinja"
{#css /static/css/card.css #}
{#def title #}

<div {{ attrs.render(class="card") }}>
  <h3>{{ title }}</h3>
  {{ content }}
</div>
```

Or use `url_for` in a custom render loop:

```html+jinja title="components/layout.jinja"
<head>
  {% for css_file in assets.collect_css() %}
    <link rel="stylesheet" href="{{ url_for('static', filename=css_file) }}">
  {% endfor %}
</head>
```

## Complete Example

Here's a complete Flask application using Jx:

```python title="app.py"
from flask import Flask, redirect, url_for, flash, session, g
from flask_wtf.csrf import CSRFProtect
from jx import Catalog

app = Flask(__name__)
app.secret_key = "your-secret-key"
csrf = CSRFProtect(app)

# Create catalog with Flask's Jinja environment
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
    return catalog.render("pages/home.jinja")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form["email"], request.form["password"])
        if user:
            session["user_id"] = user.id
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "error")
    return catalog.render("pages/login.jinja")

@app.route("/dashboard")
def dashboard():
    if not g.user:
        return redirect(url_for("login"))
    return catalog.render("pages/dashboard.jinja", user=g.user)

@app.errorhandler(404)
def not_found(e):
    return catalog.render("errors/404.jinja"), 404

if __name__ == "__main__":
    app.run(debug=True)
```

```html+jinja title="components/layout.jinja"
{#import "./nav.jinja" as Nav #}
{#import "./flash-messages.jinja" as FlashMessages #}
{#import "./footer.jinja" as Footer #}
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

```html+jinja title="components/pages/dashboard.jinja"
{#import "../layout.jinja" as Layout #}
{#import "../card.jinja" as Card #}
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

## Production Settings

For production, disable auto-reload and consider preloading components:

```python title="app.py"
import os

app = Flask(__name__)
is_production = os.environ.get("FLASK_ENV") == "production"

catalog = Catalog(
    jinja_env=app.jinja_env,
    auto_reload=not is_production,
)
catalog.add_folder("components/", preload=is_production)
```
