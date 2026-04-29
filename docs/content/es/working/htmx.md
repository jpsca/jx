---
title: Trabaja con HTMX
description: Usa componentes Jx con htmx para interacciones dinámicas
---

[htmx](https://htmx.org) te da AJAX, transiciones CSS, WebSockets y Server-Sent Events directamente en HTML. Se combina muy bien con los componentes de Jx.

::: warning
Esta página está en construcción y puede contener errores.
:::

## Configuración

Incluye htmx en tu layout:

```html+jinja title="components/layout.jx"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

## Pasa atributos de htmx

Jx convierte automáticamente los guiones bajos en guiones, así que los atributos de htmx funcionan de forma natural:

```html+jinja
{#import "button.jx" as Button #}

<Button
  hx_get="/api/data"
  hx_target="#results"
  hx_swap="innerHTML"
>
  Load Data
</Button>
```

Se renderiza como:

```html
<button hx-get="/api/data" hx-target="#results" hx-swap="innerHTML">
  Load Data
</button>
```

## Componente de botón htmx

```html+jinja title="components/htmx-button.jx"
{#def
  text,
  url,
  method="get",
  target="",
  swap="innerHTML",
  confirm=""
#}

<button
  hx-{{ method }}="{{ url }}"
  {% if target %}hx-target="{{ target }}"{% endif %}
  hx-swap="{{ swap }}"
  {% if confirm %}hx-confirm="{{ confirm }}"{% endif %}
  {{ attrs.render(class="btn") }}
>
  {{ text }}
</button>
```

```html+jinja title="uso"
{#import "htmx-button.jx" as HtmxButton #}

<HtmxButton
  text="Load More"
  url="/api/items?page=2"
  target="#item-list"
  swap="beforeend"
/>

<HtmxButton
  text="Delete"
  url="/api/items/123"
  method="delete"
  confirm="Are you sure?"
  class="btn-danger"
/>
```

## Estados de carga

```html+jinja title="components/loading-button.jx"
{#def text, loading_text="Loading..." #}
{#css loading-button.css #}

<button {{ attrs.render(class="btn") }}>
  <span class="btn-text">{{ text }}</span>
  <span class="btn-loading">{{ loading_text }}</span>
</button>
```

```css title="loading-button.css"
.btn .btn-loading {
  display: none;
}

.btn.htmx-request .btn-text {
  display: none;
}

.btn.htmx-request .btn-loading {
  display: inline;
}
```

```html+jinja title="uso"
<LoadingButton
  text="Submit"
  loading_text="Submitting..."
  hx_post="/api/form"
/>
```

## Componentes parciales

Crea componentes que rendericen solo la parte que cambia:

```html+jinja title="components/todo-item.jx"
{#def todo #}

<li id="todo-{{ todo.id }}" class="todo-item">
  <span class="{{ 'completed' if todo.done else '' }}">
    {{ todo.text }}
  </span>
  <button
    hx-patch="/todos/{{ todo.id }}/toggle"
    hx-target="#todo-{{ todo.id }}"
    hx-swap="outerHTML"
  >
    {{ "Undo" if todo.done else "Done" }}
  </button>
  <button
    hx-delete="/todos/{{ todo.id }}"
    hx-target="#todo-{{ todo.id }}"
    hx-swap="outerHTML"
  >
    Delete
  </button>
</li>
```

```python title="views.py"
@app.patch("/todos/<id>/toggle")
def toggle_todo(id):
    todo = toggle_todo_status(id)
    return catalog.render("todo-item.jx", todo=todo)

@app.delete("/todos/<id>")
def delete_todo(id):
    delete_todo_by_id(id)
    return ""  # Una respuesta vacía elimina el elemento
```

## Búsqueda con debounce

```html+jinja title="components/search-input.jx"
{#def url, target, placeholder="Search..." #}

<input
  type="search"
  name="q"
  placeholder="{{ placeholder }}"
  hx-get="{{ url }}"
  hx-target="{{ target }}"
  hx-trigger="input changed delay:300ms, search"
  hx-indicator="#search-indicator"
  {{ attrs.render(class="search-input") }}
/>
<span id="search-indicator" class="htmx-indicator">Searching...</span>
```

```html+jinja title="uso"
{#import "search-input.jx" as SearchInput #}

<SearchInput url="/api/search" target="#results" />
<div id="results"></div>
```

## Scroll infinito

```html+jinja title="components/infinite-scroll.jx"
{#def items, next_url="" #}

{% for item in items %}
  <div class="item">{{ item.name }}</div>
{% endfor %}

{% if next_url %}
  <div
    hx-get="{{ next_url }}"
    hx-trigger="revealed"
    hx-swap="outerHTML"
    class="loading-more"
  >
    Loading more...
  </div>
{% endif %}
```

```python title="views.py"
@app.get("/items")
def list_items():
    page = request.args.get("page", 1, type=int)
    items = get_items(page=page, per_page=20)
    next_url = f"/items?page={page + 1}" if items.has_next else ""
    return catalog.render("infinite-scroll.jx", items=items, next_url=next_url)
```

## Modal con htmx

```html+jinja title="components/htmx-modal.jx"
{#def id, title="" #}
{#css modal.css #}

<div id="{{ id }}" class="modal">
  <div class="modal-backdrop" hx-on:click="this.closest('.modal').remove()"></div>
  <div class="modal-content">
    {% if title %}
      <div class="modal-header">
        <h2>{{ title }}</h2>
        <button hx-on:click="this.closest('.modal').remove()">&times;</button>
      </div>
    {% endif %}
    <div class="modal-body">
      {{ content }}
    </div>
  </div>
</div>
```

```html+jinja title="uso"
{# Botón que carga el contenido del modal #}
<button
  hx-get="/modals/edit-user/123"
  hx-target="body"
  hx-swap="beforeend"
>
  Edit User
</button>
```

```python title="views.py"
@app.get("/modals/edit-user/<id>")
def edit_user_modal(id):
    user = get_user(id)
    return catalog.render("modals/edit-user.jx", user=user)
```

```html+jinja title="components/modals/edit-user.jx"
{#import "../htmx-modal.jx" as Modal #}
{#import "../forms/input.jx" as Input #}

<Modal id="edit-user-modal" title="Edit User">
  <form hx-put="/users/{{ user.id }}" hx-swap="none">
    <Input name="name" label="Name" value={{ user.name }} />
    <Input name="email" label="Email" value={{ user.email }} />
    <button type="submit">Save</button>
  </form>
</Modal>
```

## Validación de formularios

```html+jinja title="components/validated-input.jx"
{#def name, label, validation_url #}

<div class="form-group">
  <label for="{{ name }}">{{ label }}</label>
  <input
    name="{{ name }}"
    id="{{ name }}"
    hx-post="{{ validation_url }}"
    hx-trigger="blur"
    hx-target="next .error"
    hx-swap="innerHTML"
    {{ attrs.render(class="form-control") }}
  />
  <span class="error"></span>
</div>
```

```python title="views.py"
@app.post("/validate/email")
def validate_email():
    email = request.form.get("email")
    if not is_valid_email(email):
        return "Please enter a valid email"
    if email_exists(email):
        return "This email is already registered"
    return ""  # Sin error
```

## Actualizaciones fuera de banda

Actualiza varias partes de la página:

```html+jinja title="components/notification-badge.jx"
{#def count #}

<span id="notification-count" hx-swap-oob="true" class="badge">
  {{ count }}
</span>
```

```python title="views.py"
@app.post("/notifications/mark-read/<id>")
def mark_read(id):
    mark_notification_read(id)
    count = get_unread_count()
    # Devuelve tanto la respuesta principal como la actualización OOB
    return catalog.render_string("""
        <div>Notification marked as read</div>
        {#import "notification-badge.jx" as Badge #}
        <Badge count={{ count }} />
    """, count=count)
```

## Consejos

1. **Usa `hx-boost`** en enlaces y formularios para una mejora progresiva sencilla
2. **Renderiza plantillas parciales** - Crea componentes pequeños que devuelvan solo lo que cambió
3. **Usa indicadores de carga** con `hx-indicator` para una mejor UX
4. **Aprovecha los swaps OOB** para actualizar varias secciones de la página
5. **Mantén los componentes pequeños** - htmx funciona mejor con plantillas parciales enfocadas
