---
title: Attrs
description: Handling extra HTML attributes
---

The `attrs` object is one of jx's most useful features. It collects any HTML attributes you pass to a component that aren't declared in its `{#def}` statement, letting you create flexible, reusable components.

## The Problem Attrs Solves

Imagine a button component:

```html+jinja
{#def text #}

<button class="btn">{{ text }}</button>
```

This works, but what if you need to add an `id`, `disabled`, or `data-*` attribute? Do you add them all to `{#def}`? That's impractical.

Instead, use `attrs`:

```html+jinja
{#def text #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

Now any extra attributes are automatically collected and rendered:

```html+jinja
<Button text="Save" id="save-btn" disabled data-action="save" />
```

**Renders as:**

```html
<button class="btn" id="save-btn" data-action="save" disabled>Save</button>
```

## How It Works

When you pass attributes to a component:

1. **Declared arguments** (from `{#def}`) are extracted and available as variables
2. **Everything else** goes into the `attrs` object
3. You call `attrs.render()` to output them as HTML attributes

```html+jinja
{#def title #}  {# 'title' is a declared argument #}

<div {{ attrs.render() }}>  {# Everything else becomes attrs #}
  <h2>{{ title }}</h2>
  {{ content }}
</div>
```

```html+jinja
<Card title="Hello" class="card-primary" id="main-card" data-index="1" />
```

Here:
- `title="Hello"` → Available as `{{ title }}`
- `class="..."`, `id="..."`, `data-index="..."` → Go into `attrs`

## Basic Usage

### Rendering All Attrs

The simplest use case:

```html+jinja
<div {{ attrs.render() }}>
  ...
</div>
```

This outputs all extra attributes as HTML.

### Adding Default Attributes

You can provide default attributes:

```html+jinja
<button {{ attrs.render(class="btn", type="button") }}>
  {{ content }}
</button>
```

If the user passes `class` or `type`, they'll be merged/overridden appropriately.

### Class Merging

The `class` attribute is special; it merges instead of replacing:

```html+jinja
{#def text #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

```html+jinja
<Button text="Save" class="btn-primary" />
```

**Renders as:**

```html
<button class="btn btn-primary">Save</button>
```

Both classes are included!

## Attrs Methods

The `attrs` object has several useful methods:

### `attrs.render(**kwargs)`

Renders all attributes as an HTML string.

You can pass additional attributes to merge:

```html+jinja
<div {{ attrs.render(class="card", role="region") }}>
  ...
</div>
```

**Merging rules:**
- `class`: Classes are appended (not replaced)
- Other attributes: New values override old values
- `True`: Renders as a boolean attribute (e.g., `disabled`)
- `False`: Removes the attribute
- Underscores become dashes: `data_id` → `data-id`

### `attrs.set(**kwargs)`

Modifies attributes before rendering:

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

**Options:**
- `attrs.set(id="new-id")` - Set an attribute
- `attrs.set(disabled=True)` - Add a boolean attribute
- `attrs.set(class="extra-class")` - Add to existing classes
- `attrs.set(data_foo="bar")` - Underscores become dashes
- `attrs.set(hidden=False)` - Remove an attribute

### `attrs.setdefault(**kwargs)`

Sets an attribute only if it doesn't already exist:

```html+jinja
{% do attrs.setdefault(role="button", tabindex=0) %}

<div {{ attrs.render(class="btn") }}>
  {{ content }}
</div>
```

If the user passed `role`, it won't be overridden.

### `attrs.get(name, default=None)`

Gets the value of an attribute:

```html+jinja
{%- set btn_type = attrs.get("type", "button") %}

<button {{ attrs.render() }} type="{{ btn_type }}">
  {{ content }}
</button>
```

### `attrs.add_class(*classes)`

Adds one or more classes:

```html+jinja
{% do attrs.add_class("btn", "btn-primary") %}

<button {{ attrs.render() }}>
  {{ content }}
</button>
```

### `attrs.remove_class(*classes)`

Removes one or more classes:

```html+jinja
{% do attrs.remove_class("hidden", "invisible") %}

<div {{ attrs.render() }}>
  {{ content }}
</div>
```

### `attrs.as_dict`

Returns all attributes as a dictionary:

```html+jinja
{% set all_attrs = attrs.as_dict %}

{% for key, value in all_attrs.items() %}
  <p>{{ key }}: {{ value }}</p>
{% endfor %}
```

## Common Patterns

### Button Component

```html+jinja title="components/button.jinja"
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

### Card Component

```html+jinja title="components/card.jinja"
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

### Input Component

```html+jinja title="components/input.jinja"
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

### Conditional Styling

```html+jinja title="components/alert.jinja"
{#def message, type="info" #}

{% do attrs.add_class("alert", "alert-" ~ type) %}

{% if type == "error" %}
  {% do attrs.set(role="alert") %}
{% endif %}

<div {{ attrs.render() }}>
  {{ message }}
</div>
```

## Passing Attrs to Child Components

To forward `attrs` to a child component, pass it explicitly:

```html+jinja
{#import "./button.jinja" as Button #}
{#def text #}

<div class="button-wrapper">
  <Button text={{ text }} attrs={{ attrs }} />
</div>
```

Now all extra attributes are forwarded:

```html+jinja
<WrappedButton text="Save" class="primary" disabled />
```

**Important:** Don't try to use `{{ attrs.render() }}` on a component tag. This won't work:

```html+jinja
{# ❌ WRONG - won't work #}
<Button {{ attrs.render() }} />

{# ✅ CORRECT #}
<Button attrs={{ attrs }} />
```

Component tags are preprocessed before rendering, so you must pass `attrs` as an argument.

## Underscore to Dash Conversion

Attribute names with underscores are automatically converted to dashes:

```html+jinja
<Button
  data_user_id="123"
  aria_label="Save document"
  hx_get="/api/save"
/>
```

**Renders as:**

```html
<button data-user-id="123" aria-label="Save document" hx-get="/api/save">
  ...
</button>
```

This is especially useful for:
- `data-*` attributes: `data_id`, `data_action`
- `aria-*` attributes: `aria_label`, `aria_hidden`
- Framework attributes: `hx_get`, `x_show`, `v_if`

## Special Cases

### Preserving Attributes

Sometimes you want to control which attributes are rendered:

```html+jinja
{#def title #}

{# Get specific attrs before rendering #}
{% set custom_id = attrs.get("id", "default-id") %}

<div id="{{ custom_id }}" class="card">
  <h3>{{ title }}</h3>
  <div {{ attrs.render() }}>{# Other attrs go here #}
    {{ content }}
  </div>
</div>
```

### Conditional Attributes

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

### Multiple Elements

You can use attrs on multiple elements, but usually you want different attributes on each:

```html+jinja
{#def title #}

<div class="card">
  <h3 {{ attrs.render() }}>{# Attrs go on the title #}
    {{ title }}
  </h3>
  <div class="body">
    {{ content }}
  </div>
</div>
```

Or split them:

```html+jinja
{#def title #}

{% set card_class = attrs.get("card_class", "card") %}
{% do attrs.remove_class(card_class) %}

<div class="{{ card_class }}">
  <h3 {{ attrs.render() }}>{# Other attrs go on title #}
    {{ title }}
  </h3>
  <div class="body">
    {{ content }}
  </div>
</div>
```

## Best Practices

### 1. Always Provide Default Classes

```html+jinja
{# ✅ Good - ensures base styling #}
<button {{ attrs.render(class="btn") }}>

{# ❌ Bad - user must always provide class #}
<button {{ attrs.render() }}>
```

### 2. Use setdefault for Semantic Attributes

```html+jinja
{% do attrs.setdefault(role="button", tabindex=0) %}
<div {{ attrs.render() }}>...</div>
```

This ensures accessibility without preventing user overrides.

### 3. Document Expected Attrs

```html+jinja
{#def text #}
{# Common attrs: class, id, disabled, data-* #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

### 4. Don't Overuse attrs.set()

```html+jinja
{# ❌ Too much manipulation #}
{% do attrs.set(class="a") %}
{% do attrs.add_class("b") %}
{% do attrs.set(role="button") %}
{% do attrs.setdefault(tabindex=0) %}

{# ✅ Better - do it all at once #}
{% do attrs.set(class="a b", role="button") %}
{% do attrs.setdefault(tabindex=0) %}
```

## Next Steps

- **[Assets](/guides/assets)** - Learn about CSS and JavaScript management
- **[Components](/guides/components)** - Back to component basics
- **[API: Attrs](/api/attrs)** - Full API reference for the Attrs class
