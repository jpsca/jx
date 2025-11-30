---
title: Arguments
description: Passing data to components
---

Components accept arguments (also called "props" in other frameworks) to customize their behavior and appearance.

## Declaring Arguments

Use the `{#def ... #}` comment at the top of your component to declare what arguments it accepts:

```html+jinja
{#def title, count=0 #}

<div class="card">
  <h2>{{ title }}</h2>
  <p>Count: {{ count }}</p>
</div>
```

This component:
- Requires a `title` argument (no default value)
- Has an optional `count` argument (defaults to `0`)

## Required vs Optional Arguments

### Required Arguments

Arguments without a default value are required:

```html+jinja
{#def name, email #}

<div class="user">
  <p>Name: {{ name }}</p>
  <p>Email: {{ email }}</p>
</div>
```

If you use this component without passing both arguments, you'll get an error:

```html+jinja
{#import "./user.jinja" as User #}

<User name="Alice" />  {# ❌ Error: missing 'email' argument #}
```

### Optional Arguments

Arguments with default values are optional:

```html+jinja
{#def name, role="User", active=true #}

<div class="user">
  <p>{{ name }} ({{ role }})</p>
  {% if active %}
    <span class="badge-active">Active</span>
  {% endif %}
</div>
```

You can use it with or without the optional arguments:

```html+jinja
<User name="Alice" />
<User name="Bob" role="Admin" />
<User name="Charlie" role="Guest" active={{ false }} />
```

## Default Values

Default values can be:

- **Strings**: `name="default"`
- **Numbers**: `count=0`, `price=9.99`
- **Booleans**: `active=true`, `disabled=false`
- **Lists**: `items=[]`
- **Dicts**: `options={}`
- **Expressions**: `total=sum([1,2,3])`, `max_value=max(10, 20)`

Allowed functions in default expressions:
- `len()`, `min()`, `max()`, `sum()`, `pow()`
- `true` / `false` (lowercase, like in Jinja)

```html+jinja
{#def
  items=[],
  max_items=10,
  show_all=false,
  total=sum([1,2,3])
#}
```

## Multiline Declarations

For components with many arguments, spread them across multiple lines:

```html+jinja
{#def
  title,
  subtitle="",
  image_url="",
  author="Anonymous",
  published_date=None,
  tags=[],
  featured=false
#}
```

## Type Hints

You can add Python type hints (they're ignored by jx but help with documentation):

```html+jinja
{#def
  user: dict,
  count: int = 0,
  items: list[str] = [],
  active: bool = true
#}
```

Type hints don't enforce types; they're just for clarity.

## Passing Arguments

### String Arguments

Pass strings using quotes:

```html+jinja
<Button text="Click me" color="blue" />
```

### Expression Arguments

Pass non-string values using `{{ }}`:

```html+jinja
<Card
  user={{ current_user }}
  count={{ 42 }}
  active={{ true }}
  items={{ [1, 2, 3] }}
  config={{ {"key": "value"} }}
/>
```

Inside `{{ }}`, you can use any Jinja expression:

```html+jinja
<Badge
  count={{ user.notifications | length }}
  color={{ "red" if urgent else "blue" }}
  visible={{ count > 0 }}
/>
```

### Boolean Arguments

For `true` values, you can use the HTML-style short syntax:

```html+jinja
{# These are equivalent #}
<Button disabled={{ true }} />
<Button disabled />

{# These are equivalent #}
<Input required={{ true }} autofocus={{ true }} />
<Input required autofocus />
```

For `false` values, you must be explicit:

```html+jinja
<Button disabled={{ false }} />
```

### Multiline Arguments

For complex objects, spread them across lines:

```html+jinja
<UserCard
  user={{
    "name": user.full_name,
    "email": user.email,
    "avatar": user.avatar_url,
    "role": user.role,
  }}
  settings={{
    "show_email": true,
    "show_avatar": true,
  }}
/>
```

## Using Arguments in Components

Access arguments as regular variables:

```html+jinja
{#def title, count=0, items=[] #}

<div class="widget">
  <h2>{{ title }}</h2>

  {% if count > 0 %}
    <span class="count">{{ count }}</span>
  {% endif %}

  <ul>
    {% for item in items %}
      <li>{{ item }}</li>
    {% endfor %}
  </ul>
</div>
```

## Special Arguments

### The `content` Variable

Every component automatically receives a `content` variable containing what's between its tags:

```html+jinja
{#def title #}

<div class="card">
  <h3>{{ title }}</h3>
  <div class="body">
    {{ content }}
  </div>
</div>
```

```html+jinja
<Card title="Hello">
  <p>This becomes the content!</p>
</Card>
```

See [Content & Slots](/guides/content-and-slots) for more details.

### The `attrs` Object

Extra arguments not declared in `{#def}` are collected in the `attrs` object:

```html+jinja
{#def text #}

<button {{ attrs.render() }}>
  {{ text }}
</button>
```

```html+jinja
<Button text="Save" class="btn-primary" id="save-btn" disabled />
```

Renders as:

```html
<button class="btn-primary" id="save-btn" disabled>Save</button>
```

See [Attrs](/guides/attrs) for more details.

## Passing Arguments to Child Components

Pass arguments down to child components:

```html+jinja
{#import "./button.jinja" as Button #}
{#def title, button_text="Submit" #}

<form>
  <h2>{{ title }}</h2>
  <Button text={{ button_text }} type="submit" />
</form>
```

### Forwarding All Extra Attributes

To pass all extra attributes to a child component:

```html+jinja
{#import "./button.jinja" as Button #}
{#def text #}

<div class="button-wrapper">
  <Button text={{ text }} attrs={{ attrs }} />
</div>
```

Now any extra attributes are forwarded:

```html+jinja
<WrappedButton text="Save" class="primary" disabled />
```

## Naming Conventions

### Use Underscores in Arguments

In your `{#def}`, use Python-style snake_case:

```html+jinja
{#def user_name, is_active, created_at #}
```

### Dash-to-Underscore Conversion

When passing arguments, dashes are automatically converted to underscores:

```html+jinja
{# These are equivalent #}
<User user-name="Alice" is-active />
<User user_name="Alice" is_active />
```

Both match the `{#def user_name, is_active #}` declaration.

This is useful for HTML-style attribute names like `aria-label` or `data-value`:

```html+jinja
{#def aria_label #}

<button aria-label="{{ aria_label }}">
  Click me
</button>
```

```html+jinja
<Button aria-label="Close dialog" />
```

## Common Patterns

### Configuration Objects

Pass complex configuration as a dictionary:

```html+jinja
{#def config={} #}

<div class="widget">
  {% if config.get("show_header", true) %}
    <header>...</header>
  {% endif %}

  {% if config.get("show_footer", true) %}
    <footer>...</footer>
  {% endif %}
</div>
```

```html+jinja
<Widget config={{ {"show_header": false, "show_footer": true} }} />
```

### Optional Content Objects

Use `None` as a default for optional objects:

```html+jinja
{#def user=None #}

{% if user %}
  <p>Welcome, {{ user.name }}!</p>
{% else %}
  <p>Welcome, Guest!</p>
{% endif %}
```

### Lists with Defaults

Provide empty lists as defaults:

```html+jinja
{#def items=[], selected=[] #}

<ul>
  {% for item in items %}
    <li class="{{ 'selected' if item in selected else '' }}">
      {{ item }}
    </li>
  {% endfor %}
</ul>
```

### Enum-Style Arguments

Use string arguments with specific values:

```html+jinja
{#def size="medium", variant="primary" #}

<button class="btn btn-{{ size }} btn-{{ variant }}">
  {{ content }}
</button>
```

```html+jinja
<Button size="large" variant="success">Save</Button>
```

## Validation

jx validates arguments at render time:

- **Missing required arguments** → `MissingRequiredArgument` exception
- **Unknown components** → `ImportError` exception (at load time)
- **Invalid syntax** → `TemplateSyntaxError` exception (at load time)

This means errors are caught early, often before the template is even rendered.

## Best Practices

### 1. Keep Arguments Focused

Components should have a clear purpose with relevant arguments:

```html+jinja
{# ✅ Good - focused on user display #}
{#def user, show_avatar=true, show_email=false #}

{# ❌ Bad - too many unrelated things #}
{#def user, theme, analytics_id, debug_mode, api_key #}
```

### 2. Use Descriptive Names

```html+jinja
{# ✅ Good #}
{#def is_loading, should_auto_focus, max_items #}

{# ❌ Bad #}
{#def loading, focus, max #}
```

### 3. Provide Sensible Defaults

Make components easy to use with good defaults:

```html+jinja
{#def
  size="medium",
  variant="primary",
  disabled=false
#}
```

### 4. Document Complex Arguments

Use comments for complex argument types:

```html+jinja
{#def
  user,  # dict with keys: name, email, avatar_url
  permissions=[],  # list of permission strings
  metadata={}  # arbitrary key-value pairs
#}
```

## Next Steps

- **[Content & Slots](/guides/content-and-slots)** - Learn about the `content` variable and named slots
- **[Attrs](/guides/attrs)** - Handle extra HTML attributes
- **[Components](/guides/components)** - Back to component basics
