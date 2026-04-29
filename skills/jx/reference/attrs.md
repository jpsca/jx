# attrs reference

`attrs` is the per-component object that holds every HTML attribute the caller passed *that wasn't declared* in `{#def}`. It exists to keep components flexible without forcing every possible attribute into the prop list.

```html+jinja
{#def text #}
<button {{ attrs.render(class="btn") }}>{{ text }}</button>
```

```html+jinja
<Button text="Save" id="save" disabled data-action="save" />
```

→

```html
<button class="btn" id="save" data-action="save" disabled>Save</button>
```

`text` was declared, so it's a regular variable. Everything else flowed into `attrs`.

## Methods

### `attrs.render(**kwargs)`

Render every attribute as an HTML string. Defaults passed via kwargs merge per these rules:

| Behavior | Rule |
|---|---|
| `class` | **Component classes come first**, then caller classes appended. |
| Other attrs | Caller value overrides default. |
| `True` | Renders as a boolean attribute (`disabled`). |
| `False` | Removes the attribute entirely. |
| Underscores | `data_id` → `data-id`, `aria_label` → `aria-label`. |

```html+jinja
<div {{ attrs.render(class="card", role="region") }}>
  ...
</div>
```

`class` is a Python keyword, so in pure-Python contexts you can't pass it as a kwarg. Inside a Jinja template that's not a problem (`class="..."` works), but if you ever build an `Attrs` object in Python code use the `classes=` alias: `Attrs({"classes": "card"})` or `attrs.set(classes="card")` — both internally treated as `class`.

**Best practice**: bundle every attribute into the single `attrs.render(...)` call rather than spreading them across the tag. Pre-compute complex values with `{% set ... %}`:

```html+jinja
{% set base_classes = "Tab ..." %}
{% set state_class = selected_classes if selected else (disabled_classes if disabled else enabled_classes) %}

<{{ tag }}
  {{ attrs.render(
    role="tab",
    aria_selected="true" if selected else "false",
    aria_controls=target,
    id=target ~ "-tab",
    tabindex="0" if selected else "-1",
    aria_disabled="true" if disabled else False,
    disabled=(tag == "button" and disabled),
    class=base_classes ~ " " ~ state_class,
  ) }}
>
  {{ content }}
</{{ tag }}>
```

### `attrs.set(**kwargs)`

Modify before rendering. Useful inside `{% if %}` / `{% for %}` blocks where you can't easily inline expressions in `render()`.

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

`{% do attrs.set(hidden=False) %}` removes an existing attribute.

### `attrs.setdefault(**kwargs)`

Set an attribute only if the caller didn't pass one. Useful for accessibility defaults that shouldn't override caller intent:

```html+jinja
{% do attrs.setdefault(role="button", tabindex=0) %}
<div {{ attrs.render(class="btn") }}>{{ content }}</div>
```

### `attrs.get(name, default=None)`

Read a value (e.g. to use it in a different element than where you call `render`):

```html+jinja
{% set btn_type = attrs.get("type", "button") %}
<button {{ attrs.render() }} type="{{ btn_type }}">{{ content }}</button>
```

### Class manipulation

| Method | Effect |
|---|---|
| `attrs.add_class("a", "b")` | Appends classes after existing ones. |
| `attrs.prepend_class("base")` | Adds classes at the *front* — handy when class order matters (utility CSS). |
| `attrs.remove_class("hidden")` | Removes specific classes. |
| `attrs.classes` | Read-only space-separated string of current classes. |

```html+jinja
{% if "active" in attrs.classes %}<span>active</span>{% endif %}
```

### `attrs.as_dict`

Returns every attribute as a dict — for iteration, debugging, or forwarding to a non-HTML renderer.

```html+jinja
{% for key, value in attrs.as_dict.items() %}
  <p>{{ key }}: {{ value }}</p>
{% endfor %}
```

## Forwarding to a child component

Component tags are preprocessed before rendering, so `attrs.render()` doesn't work on them. Pass `attrs` as an explicit argument instead:

```html+jinja
{#import "./button.jx" as Button #}
{#def text #}

<div class="button-wrapper">
  <Button text={{ text }} attrs={{ attrs }} />
</div>
```

```html+jinja
{# ❌ wrong — this does NOT work #}
<Button {{ attrs.render() }} />

{# ✅ right #}
<Button attrs={{ attrs }} />
```

The child component receives the parent's `attrs` and can call `attrs.render()` on a real HTML element inside it.

## Common patterns

### Variant-aware default class

```html+jinja
{#def text="Click", variant="primary" #}
<button {{ attrs.render(class="btn btn-" ~ variant, type="button") }}>
  {{ text }}
</button>
```

### Accessibility-first input

```html+jinja
{#def name, label="", required=false #}
{% do attrs.setdefault(type="text", id=name) %}

<div class="form-group">
  {% if label %}
    <label for="{{ name }}">
      {{ label }}{% if required %}<span class="required">*</span>{% endif %}
    </label>
  {% endif %}
  <input name="{{ name }}" {{ attrs.render(class="form-control") }} />
</div>
```

### Conditional role/state

```html+jinja
{#def message, type="info" #}
{% do attrs.add_class("alert", "alert-" ~ type) %}
{% if type == "error" %}{% do attrs.set(role="alert") %}{% endif %}

<div {{ attrs.render() }}>{{ message }}</div>
```

## Don'ts

- **Don't apply `attrs` on multiple elements without a clear separation of concerns.** Pick one root element to receive caller attrs; if you need to split, use `attrs.get(...)` to extract specific values explicitly.
- **Don't fragment manipulation.** Prefer one `attrs.render(...)` call over multiple `set()` / `add_class()` / `setdefault()` chains. Keep logic readable.
- **Don't skip default classes.** `attrs.render()` with no kwargs leaves a component unstyled if the caller forgets `class`. Always pass at least the component's base class.
