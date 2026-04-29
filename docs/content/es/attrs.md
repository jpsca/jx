---
title: Attrs
description: Manejo de atributos HTML extra
---

El objeto `attrs` es una de las funcionalidades más útiles de Jx. Recolecta cualquier atributo HTML que pases a un componente que no esté declarado en su sentencia `{#def}`.

## El problema que resuelve Attrs

Imagina un componente botón:

```html+jinja
{#def text #}

<button class="btn">{{ text }}</button>
```

Esto funciona, pero ¿qué pasa si necesitas agregar un atributo `id`, `disabled` o `data-*`? ¿Los agregas todos al `{#def}`? Eso es poco práctico.

En su lugar, usa `attrs`:

```html+jinja
{#def text #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

Ahora cualquier atributo extra se recolecta y renderiza automáticamente:

```html+jinja
<Button text="Save" id="save-btn" disabled data-action="save" />
```

**Renderiza como:**

```html
<button class="btn" id="save-btn" data-action="save" disabled>Save</button>
```

## Cómo funciona

Cuando pasas atributos a un componente:

1. **Argumentos declarados** (de `{#def}`) se extraen y están disponibles como variables
2. **Todo lo demás** va al objeto `attrs`
3. Llamas a `attrs.render()` para mostrarlos como atributos HTML

```html+jinja
{#def title #}  {# 'title' es un argumento declarado #}

<div {{ attrs.render() }}>  {# Todo lo demás se vuelve attrs #}
  <h2>{{ title }}</h2>
  {{ content }}
</div>
```

```html+jinja
<Card title="Hello" class="card-primary" id="main-card" data-index="1" />
```

Aquí:
- `title="Hello"` → Disponible como `{{ title }}`
- `class="..."`, `id="..."`, `data-index="..."` → Van a `attrs`

## Uso básico

### Renderiza todos los attrs

El caso de uso más simple:

```html+jinja
<div {{ attrs.render() }}>
  ...
</div>
```

Esto muestra todos los atributos extra como HTML.

### Agrega atributos por defecto

Puedes proporcionar atributos por defecto:

```html+jinja
<button {{ attrs.render(class="btn", type="button") }}>
  {{ content }}
</button>
```

Si el usuario pasa `class` o `type`, se fusionarán/sobrescribirán según corresponda.

### Fusión de clases

El atributo `class` es especial; se fusiona en lugar de reemplazar:

```html+jinja
{#def text #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

```html+jinja
<Button text="Save" class="btn-primary" />
```

**Renderiza como:**

```html
<button class="btn btn-primary">Save</button>
```

¡Ambas clases están incluidas!

## Métodos de Attrs

El objeto `attrs` tiene varios métodos útiles:

### `attrs.render(**kwargs)`

Renderiza todos los atributos como una cadena HTML.

Puedes pasar atributos adicionales para fusionar:

```html+jinja
<div {{ attrs.render(class="card", role="region") }}>
  ...
</div>
```

**Reglas de fusión:**

- `class`: Las clases se agregan (no se reemplazan)
- Otros atributos: Los nuevos valores sobrescriben los antiguos
- `True`: Se renderiza como un atributo booleano (por ejemplo, `disabled`)
- `False`: Elimina el atributo
- Los guiones bajos se convierten en guiones: `data_id` → `data-id`

### `attrs.set(**kwargs)`

Modifica los atributos antes de renderizar:

```html+jinja
{#def title, highlighted=false #}

{% if highlighted %}
  {% do attrs.set(class="card card-highlighted", role="alert") %}
{% endif %}

<div {{ attrs.render(class="card") }}>
  <h3>{{ title }}</h3>
  {{ content }}
</div>
```

**Opciones:**

- `attrs.set(id="new-id")` - Establece un atributo
- `attrs.set(disabled=True)` - Agrega un atributo booleano
- `attrs.set(class="extra-class")` - Agrega a las clases existentes
- `attrs.set(data_foo="bar")` - Los guiones bajos se convierten en guiones
- `attrs.set(hidden=False)` - Elimina un atributo

### `attrs.setdefault(**kwargs)`

Establece un atributo solo si no existe ya:

```html+jinja
{% do attrs.setdefault(role="button", tabindex=0) %}

<div {{ attrs.render(class="btn") }}>
  {{ content }}
</div>
```

Si el usuario pasó `role`, no será sobrescrito.

### `attrs.get(name, default=None)`

Obtiene el valor de un atributo:

```html+jinja
{%- set btn_type = attrs.get("type", "button") %}

<button {{ attrs.render() }} type="{{ btn_type }}">
  {{ content }}
</button>
```

### `attrs.add_class(*classes)`

Agrega una o más clases al final de la lista de clases:

```html+jinja
{% do attrs.add_class("btn", "btn-primary") %}

<button {{ attrs.render() }}>
  {{ content }}
</button>
```

### `attrs.prepend_class(*classes)`

Agrega una o más clases al inicio de la lista de clases:

```html+jinja
{% do attrs.prepend_class("btn") %}

<button {{ attrs.render() }}>
  {{ content }}
</button>
```

Esto es útil cuando el orden de las clases importa (por ejemplo, con frameworks CSS utility-first donde la primera clase debe ser el estilo base).

### `attrs.remove_class(*classes)`

Elimina una o más clases:

```html+jinja
{% do attrs.remove_class("hidden", "invisible") %}

<div {{ attrs.render() }}>
  {{ content }}
</div>
```

### `attrs.classes`

Devuelve todas las clases HTML como una cadena separada por espacios:

```html+jinja
{% if "active" in attrs.classes %}
  <span>Este ítem está activo</span>
{% endif %}
```

### `attrs.as_dict`

Devuelve todos los atributos como un diccionario:

```html+jinja
{% set all_attrs = attrs.as_dict %}

{% for key, value in all_attrs.items() %}
  <p>{{ key }}: {{ value }}</p>
{% endfor %}
```

## Patrones comunes

### Componente botón

```html+jinja title="components/button.jx"
{#def text="Click me", variant="primary" #}

<button {{ attrs.render(
  class="btn btn-" ~ variant,
  type="button"
) }}>
  {{ text }}
</button>
```

```html+jinja title="usage"
<Button text="Save" variant="success" id="save-btn" disabled />
```

### Componente Card

```html+jinja title="components/card.jx"
{#def title="" #}

<div {{ attrs.render(class="card") }}>
  {% if title %}
    <div class="card-header">
      <h3>{{ title }}</h3>
    </div>
  {% endif %}
  <div class="card-body">
    {{ content }}
  </div>
</div>
```

```html+jinja title="usage"
<Card title="Welcome" class="shadow-lg" data-card-id="123">
  <p>Card content here</p>
</Card>
```

### Componente Input

```html+jinja title="components/input.jx"
{#def name, label="", required=false #}

{% do attrs.setdefault(type="text", id=name) %}

<div class="form-group">
  {% if label %}
    <label for="{{ name }}">
      {{ label }}
      {% if required %}<span class="required">*</span>{% endif %}
    </label>
  {% endif %}
  <input name="{{ name }}" {{ attrs.render(class="form-control") }} />
</div>
```

```html+jinja title="usage"
<Input
  name="email"
  label="Email Address"
  type="email"
  required
  placeholder="you@example.com"
  autocomplete="email"
/>
```

### Estilo condicional

```html+jinja title="components/alert.jx"
{#def message, type="info" #}

{% do attrs.add_class("alert", "alert-" ~ type) %}

{% if type == "error" %}
  {% do attrs.set(role="alert") %}
{% endif %}

<div {{ attrs.render() }}>
  {{ message }}
</div>
```

## Pasa attrs a componentes hijos

Para reenviar `attrs` a un componente hijo, pásalo explícitamente:

```html+jinja
{#import "./button.jx" as Button #}
{#def text #}

<div class="button-wrapper">
  <Button text={{ text }} attrs={{ attrs }} />
</div>
```

Ahora todos los atributos extra se reenvían:

```html+jinja
<WrappedButton text="Save" class="primary" disabled />
```

**Importante:** No intentes usar `{{ attrs.render() }}` en una etiqueta de componente. Esto no funcionará:

```html+jinja
{# ❌ INCORRECTO - no funcionará #}
<Button {{ attrs.render() }} />

{# ✅ CORRECTO #}
<Button attrs={{ attrs }} />
```

Las etiquetas de componente se preprocesan antes del renderizado, por lo que debes pasar `attrs` como un argumento.

## Conversión de guion bajo a guion

Los nombres de atributos con guiones bajos se convierten automáticamente a guiones:

```html+jinja
<Button
  data_user_id="123"
  aria_label="Save document"
  hx_get="/api/save"
/>
```

**Renderiza como:**

```html
<button data-user-id="123" aria-label="Save document" hx-get="/api/save">
  ...
</button>
```

Esto es especialmente útil para:

- Atributos `data-*`: `data_id`, `data_action`
- Atributos `aria-*`: `aria_label`, `aria_hidden`
- Atributos de frameworks: `hx_get`, `x_show`, `v_if`

## Casos especiales

### Preserva atributos

A veces quieres controlar qué atributos se renderizan:

```html+jinja
{#def title #}

{# Obtén attrs específicos antes de renderizar #}
{% set custom_id = attrs.get("id", "default-id") %}

<div id="{{ custom_id }}" class="card">
  <h3>{{ title }}</h3>
  <div {{ attrs.render() }}>{# Otros attrs van aquí #}
    {{ content }}
  </div>
</div>
```

### Atributos condicionales

```html+jinja
{#def is_active=false #}

{% if is_active %}
  {% do attrs.add_class("active") %}
  {% do attrs.set(aria_current="true") %}
{% endif %}

<a {{ attrs.render(class="nav-link") }}>
  {{ content }}
</a>
```

### Múltiples elementos

Puedes usar attrs en múltiples elementos, pero usualmente quieres atributos diferentes en cada uno:

```html+jinja
{#def title #}

<div class="card">
  <h3 {{ attrs.render() }}>{# Los attrs van en el título #}
    {{ title }}
  </h3>
  <div class="body">
    {{ content }}
  </div>
</div>
```

O sepáralos:

```html+jinja
{#def title #}

{% set card_class = attrs.get("card_class", "card") %}
{% do attrs.remove_class(card_class) %}

<div class="{{ card_class }}">
  <h3 {{ attrs.render() }}>{# Otros attrs van en el título #}
    {{ title }}
  </h3>
  <div class="body">
    {{ content }}
  </div>
</div>
```

## Buenas prácticas

### 1. Siempre proporciona clases por defecto

```html+jinja
{# ✅ Bien - asegura el estilo base #}
<button {{ attrs.render(class="btn") }}>

{# ❌ Mal - el usuario siempre debe proporcionar class #}
<button {{ attrs.render() }}>
```

### 2. Usa setdefault para atributos semánticos

```html+jinja
{% do attrs.setdefault(role="button", tabindex=0) %}
<div {{ attrs.render() }}>...</div>
```

Esto asegura accesibilidad sin impedir las sobrescrituras del usuario.

### 3. Documenta los attrs esperados

```html+jinja
{#def text #}
{# Attrs comunes: class, id, disabled, data-* #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

### 4. No abuses de attrs.set()

```html+jinja
{# ❌ Demasiada manipulación #}
{% do attrs.set(class="a") %}
{% do attrs.add_class("b") %}
{% do attrs.set(role="button") %}
{% do attrs.setdefault(tabindex=0) %}

{# ✅ Mejor - hazlo todo de una vez #}
{% do attrs.set(class="a b", role="button") %}
{% do attrs.setdefault(tabindex=0) %}
```

## Próximos pasos

- **[Assets](/docs/assets)** - Aprende sobre el manejo de CSS y JavaScript
- **[API: Attrs](/docs/api/attrs)** - Referencia completa de la API para la clase Attrs
