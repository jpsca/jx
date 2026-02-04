---
title: Components
description: Building components with Jx
---

A component is a reusable template snippet that works like a function. It can take arguments, render content, and be composed with other components to build complex UIs.

Think of components as the building blocks of your interface; buttons, cards, forms, layouts; anything you use more than once or want to keep organized.

## Creating a Component

Components are Jinja template files with a `.jinja` extension:

```html+jinja title="components/button.jinja"
{#def text #}

<button class="btn">{{ text }}</button>
```

### Anatomy of a Component

A complete component can have these parts:

```html+jinja title="components/card.jinja"
{#import "./header.jinja" as Header #}
{#css card.css #}
{#js card.js #}
{#def title, subtitle="" #}

<div class="card">
  <Header title={{ title }} subtitle={{ subtitle }} />
  <div class="card-body">
    {{ content }}
  </div>
</div>
```

From top to bottom:

1. **Imports** - Other components this one uses
2. **Assets** - CSS and JS files
3. **Arguments** - Data the component accepts
4. **Template** - The HTML to render

All parts are optional except the template.

## Using Components

Import a component, then use it like an HTML tag:

```html+jinja
{#import "button.jinja" as Button #}
{#import "card.jinja" as Card #}

<Card title="Welcome">
  <p>Hello world!</p>
  <Button text="Click me" />
</Card>
```

**Block syntax** for components with content:

```html+jinja
<Card title="Hello">
  <p>Content goes here</p>
</Card>
```

**Self-closing syntax** for components without content:

```html+jinja
<Button text="Click me" />
```

---

## Imports

Jx requires explicit imports before using components.

### Basic Syntax

```html+jinja
{#import "path/to/component.jinja" as Name #}
```

### File Naming

Component files and folders can use any naming convention: `button.jinja`, `user-card.jinja`, `form_input.jinja`, etc. The **import alias**, however, must be `PascalCase` to distinguish components from HTML:

```html+jinja
{#import "user-card.jinja" as UserCard #}
{#import "form_input.jinja" as FormInput #}

<UserCard />   {# Component #}
<div />        {# HTML #}
```

### Absolute Imports

Paths relative to a catalog folder:

```html+jinja
{#import "components/button.jinja" as Button #}
{#import "layouts/base.jinja" as Base #}
```

Use for shared components used across your project.

### Relative Imports

Paths relative to the current file:

```html+jinja
{#import "./sibling.jinja" as Sibling #}
{#import "../parent/component.jinja" as Component #}
{#import "./subfolder/child.jinja" as Child #}
```

Use for tightly related components. Move an entire folder and internal imports still work.

**Example structure:**

```
components/
  modal/
    modal.jinja       {#import "./header.jinja" as Header #}
    header.jinja      {#import "./close-btn.jinja" as CloseBtn #}
    close-btn.jinja
```

### Prefixed Imports

For components from prefixed catalog folders:

```python
catalog.add_folder("vendor/ui-lib", prefix="ui")
```

```html+jinja
{#import "@ui/button.jinja" as Button #}
{#import "@ui/modal.jinja" as Modal #}
```

Use for third-party component libraries.

---

## Arguments

Components accept arguments to customize their behavior.

### Declaring Arguments

Use `{#def ... #}` at the top of your component:

```html+jinja
{#def title, count=0 #}

<h2>{{ title }}: {{ count }}</h2>
```

- `title` - Required (no default)
- `count` - Optional (defaults to `0`)


#### Type Annotations

Arguments can also have type annotations:                                                                                   

```html+jinja                                                                                           
{#def
    title: str,
    count: int = 0,
    items: list[str] = [],
    data: dict[str, int] = {}
#}
```

For primitive types (`int`, `str`, `bool`, `list`, `dict`, etc.), Jx validates at runtime that passed arguments match the declared types.

**However, this is limited to simple types**. For example, for arguments with types like `list[str]`, Jx only checks that the argument is a list, not that its elements are
strings. The same is true for `dict[str, int]`, `tuple[int, ...]`, etc. It also cannot check any union types like `int | str`.


### Default Values

Defaults can be any Python value: strings, numbers, booleans, lists, dicts, etc.

```html+jinja
{#def
  name,
  count=0,
  active=true,
  items=[],
  config={}
#}
```

### Passing Arguments

**Strings** use quotes:

```html+jinja
<Button text="Click me" />
```

**Expressions** use `{{ }}`:

```html+jinja
<Card
  user={{ current_user }}
  count={{ items | length }}
  active={{ true }}
  items={{ [1, 2, 3] }}
/>
```

**Booleans** can use HTML-style shorthand for `true`:

```html+jinja
<Input required />          {# Same as required={{ true }} #}
<Input disabled={{ false }} />
```

### Dash to Underscore

Dashes in attribute names convert to underscores:

```html+jinja
{#def aria_label, data_id #}

<Button aria-label="Close" data-id="123" />
```

Both `aria-label` and `aria_label` match `aria_label` in the def.

---

## Content & Slots

Components can wrap content passed between their tags.

### The `content` Variable

Everything between a component's tags is available as `content`:

```html+jinja title="components/card.jinja"
{#def title #}

<div class="card">
  <h3>{{ title }}</h3>
  <div class="body">{{ content }}</div>
</div>
```

```html+jinja title="usage"
<Card title="Hello">
  <p>This becomes the content!</p>
</Card>
```

### Fallback Content

Provide defaults when no content is passed:

```html+jinja
<div class="body">
  {{ content or "No content provided" }}
</div>
```

### Named Slots

For multiple content areas, use named slots.

**Define slots** in the component with `{% slot %}`:

```html+jinja title="components/modal.jinja"
<div class="modal">
  <div class="modal-header">
    {% slot header %}
      <h3>Default Header</h3>
    {% endslot %}
  </div>
  <div class="modal-body">
    {{ content }}
  </div>
  <div class="modal-footer">
    {% slot footer %}
      <button>Close</button>
    {% endslot %}
  </div>
</div>
```

**Fill slots** when using the component with `{% fill %}`:

```html+jinja title="usage"
<Modal>
  {% fill header %}
    <h3>Confirm</h3>
  {% endfill %}

  <p>Are you sure?</p>

  {% fill footer %}
    <button>Yes</button>
    <button>No</button>
  {% endfill %}
</Modal>
```

Unfilled slots use their default content.

### When to Use Slots vs Props

#### Use Props When:

- The content is a single value
- You want validation

```html+jinja
{#def title, count #}
<h2>{{ title }}: {{ count }}</h2>
```

#### Use Content When:

- The content is HTML
- There's one main content area
- You want flexibility in what gets passed

```html+jinja
{#def title #}
<div class="card">
  <h2>{{ title }}</h2>
  {{ content }}
</div>
```

#### Use Named Slots When:

- You need multiple content areas
- Each area has a specific purpose
- You might want to provide defaults for each area

```html+jinja
<div class="panel">
  <header>{% slot header %}Default{% endslot %}</header>
  <main>{{ content }}</main>
  <footer>{% slot footer %}Default{% endslot %}</footer>
</div>
```

## Validation

You can easily validate your components using the CLI tool `jx` installs. Just run:

```bash
❯❯ jx check PATH_TO_FOLDER 
```

Example:

```bash
❯❯ jx check docs/views/

✓ autodoc.md.jinja - OK
✓ banner_archived.jinja - OK
✓ color_scheme.jinja - OK
✓ footer.jinja - OK
✓ header.jinja - OK
✓ humans.txt.jinja - OK
✓ index.jinja - OK
✓ language_selector.jinja - OK
✓ layout.jinja - OK
✓ llm.jinja - OK
✓ metadata.jinja - OK
✓ page.jinja - OK
✓ page_nav.jinja - OK
✓ page_pager.jinja - OK
✓ page_toc.jinja - OK
✓ robots.txt.jinja - OK
✓ search.jinja - OK
✓ sidebar.jinja - OK
✓ sitemap.xml.jinja - OK
✓ toc.jinja - OK
✓ version_selector.jinja - OK

21 components checked, 0 errors
```
