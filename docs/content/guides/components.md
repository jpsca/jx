---
title: Components
description: Creating and organizing components in jx
---

Components are the heart of jx. They're simple Jinja template files that can accept arguments, wrap content, and list their own CSS and JavaScript.

## What is a Component?

A component is a reusable template snippet that works like a function. It can take arguments, render content, and be composed with other components to build complex UIs.

Think of components as the building blocks of your interface; buttons, cards, forms, layouts; anything you use more than once or want to keep organized.

## Creating a Component

Components are just Jinja template files with a `.jinja` extension, placed in a folder that's been added to your catalog.

```python
from jx import Catalog

# Folder added when declaring the catalog
catalog = Catalog("components/")
# Folder added later
catalog.add_folder("more_components/")
```

### Basic Example

```html+jinja title="components/button.jinja"
{#def text="Click me" #}

<button {{ attrs.render(class="btn") }}>
  {{ text }}
</button>
```

This simple button component:
- Declares an optional argument `text` with a default value
- Renders as a `<button>` element with a "btn" class
- Uses the `attrs` object to accept extra HTML attributes

## Anatomy of a Component

A complete component can have several parts:

```html+jinja title="components/card.jinja"
{#import "./card-header.jinja" as CardHeader #}
{#css card.css #}
{#js card.js #}
{#def title, image_url="" #}

<div {{ attrs.render(class="card") }}>
  <CardHeader title={{ title }} image_url={{ image_url }} />
  <div class="card-body">
    {{ content }}
  </div>
</div>
```

From top to bottom:

1. **Import statements** - Components this component uses
2. **Asset declarations** - CSS and JS files for this component
3. **Argument definition** - What data this component needs
4. **Template body** - The HTML/Jinja markup to render

All of these parts are optional except the template body.

## Using a Component

To use a component in another component (or page), first import it, then use it like an HTML tag:

```html+jinja title="components/profile.jinja"
{#import "card.jinja" as Card #}
{#import "button.jinja" as Button #}
{#def user #}

<Card title={{ user.name }} image_url={{ user.avatar }}>
  <p>{{ user.bio }}</p>
  <Button text="Follow" class="btn-primary" />
</Card>
```

Components can be used in two ways:

### Block Syntax

For components with content:

```html+jinja
<Card title="Hello">
  <p>This is the content</p>
</Card>
```

### Self-Closing Syntax

For components without content:

```html+jinja
<Button text="Click me" />
```

## Component Files

### Naming

Component files must have a `.jinja` extension. You can name them however you like however, the **import alias** must be *PascalCase* to distinguish components from HTML tags:

```html+jinja
{#import "cards/UserCard.jinja" as UserCard #}
{#import "form_input.jinja" as FormInput #}
{#import "fancy-button.jinja" as Button #}

<UserCard user={{ user }} />
<FormInput name="email" />
<Button>Click me</Button>
```

The import name doesn't have to match the filename:

```html+jinja
{#import "my-super-long-component-name.jinja" as Comp #}
<Comp />
```

### Location

Components must be in a folder that's been added to your catalog:

```python
from jx import Catalog

catalog = Catalog()
catalog.add_folder("components")
catalog.add_folder("layouts")
```

With this setup, your folder structure might look like:

```
project/
  components/
    button.jinja
    card.jinja
    forms/
      input.jinja
      select.jinja
  layouts/
    base.jinja
    dashboard.jinja
```

## Rendering Components

### From Python

Use the catalog to render a component from your views:

```python
def my_view():
    return catalog.render(
        "profile.jinja",
        user=current_user,
    )
```

### From Templates

Import and use components within other components:

```html+jinja
{#import "profile.jinja" as Profile #}

<Profile user={{ user }} />
```

## Nested Folders

Components in subfolders are imported using path notation:

```
components/
  forms/
    text_input.jinja          # snake_case filename
    select.jinja              # lowercase filename
  cards/
    user-card.jinja           # kebab-case filename
  Button.jinja                # PascalCase filename (also valid)
```

```html+jinja
{#import "forms/text_input.jinja" as TextInput #}
{#import "forms/select.jinja" as Select #}
{#import "cards/user-card.jinja" as UserCard #}
{#import "Button.jinja" as Button #}

<UserCard user={{ user }}>
  <TextInput name="email" />
  <Select name="country" />
  <Button>Save</Button>
</UserCard>
```

## Next Steps

Now that you understand components, learn about:

- **[Imports](/guides/imports)** - How to import components (absolute, relative, prefixed)
- **[Arguments](/guides/arguments)** - Passing data to components
- **[Content & Slots](/guides/content-and-slots)** - Wrapping content and using named slots
- **[Attrs](/guides/attrs)** - Handling extra HTML attributes
- **[Assets](/guides/assets)** - Managing CSS and JavaScript
