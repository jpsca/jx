---
title: Imports
description: Understanding jx's import system
---

Jx requires you to **explicitly import** components before using them. This might feel like extra work at first, but it provides huge benefits for maintainability and code clarity.

## Basic Import Syntax

Import components at the top of your template using the `{#import ... #}` syntax:

```html+jinja
{#import "path/to/component.jinja" as ComponentName #}
```

Then use the component:

```html+jinja
<ComponentName prop="value" />
```

## Three Types of Imports

jx supports three different import styles, each useful in different situations.

### 1. Absolute Imports

Import components using paths relative to a catalog folder:

```html+jinja
{#import "components/button.jinja" as Button #}
{#import "layouts/base.jinja" as Base #}
{#import "forms/input.jinja" as Input #}
```

Given this catalog setup:

```python
catalog = Catalog()
catalog.add_folder("components")
catalog.add_folder("layouts")
```

Absolute imports start from the root of a catalog folder.

**When to use:**
- Importing from different catalog folders
- Importing widely-used shared components
- When you want to be explicit about where something comes from

### 2. Relative Imports

Import components relative to the current file:

```html+jinja
{#import "./sibling.jinja" as Sibling #}
{#import "../parent-folder/component.jinja" as Component #}
{#import "./subfolder/child.jinja" as Child #}
```

**Relative import patterns:**

- `./file.jinja` - Same directory
- `../file.jinja` - Parent directory
- `../../file.jinja` - Grandparent directory
- `./sub/file.jinja` - Subdirectory

**When to use:**
- Components that are tightly related
- Building portable component libraries
- Internal imports within a component group

**Example: Portable card components**

```
components/
  card/
    card.jinja              {#import "./header.jinja" as Header #}
    header.jinja            {#import "./title.jinja" as Title #}
    title.jinja
    body.jinja
    footer.jinja
```

Move the entire `card/` folder anywhere, and all internal imports still work!

### 3. Prefixed Imports

Import components from folders added with a prefix:

```python
catalog.add_folder("components")
catalog.add_folder("vendor/ui-library", prefix="ui")
```

```html+jinja
{#import "card.jinja" as Card #}
{#import "@ui/button.jinja" as Button #}
{#import "@ui/modal.jinja" as Modal #}
```

The `@prefix/` notation signals components from a prefixed catalog folder.

**When to use:**
- Third-party component libraries
- Separating your components from vendor components
- Avoiding name collisions

## Import Aliases

The `as Name` part of the import determines how you use the component:

```html+jinja
{#import "common/ui/super-long-component-name.jinja" as Comp #}

<Comp />  {# Much shorter! #}
```

You can import the same component with different names:

```html+jinja
{#import "button.jinja" as Button #}
{#import "button.jinja" as Btn #}

<Button text="Submit" />
<Btn text="Cancel" />
```

Though you usually won't need to do this.

## Import Best Practices

### 1. Keep Imports at the Top

Always place imports before anything else in your template:

```html+jinja
{# ✅ Good #}
{#import "./card.jinja" as Card #}
{#import "./button.jinja" as Button #}
{#def title #}

<Card>
  <Button />
</Card>
```

```html+jinja
{# ❌ Bad #}
{#def title #}
{#import "./card.jinja" as Card #}

<Card>...</Card>
```

### 2. Use Relative Imports for Related Components

When components are closely related, use relative imports:

```html+jinja
{# components/modal/dialog.jinja #}
{#import "./header.jinja" as Header #}
{#import "./footer.jinja" as Footer #}
{#import "./close-button.jinja" as CloseButton #}
```

This makes it clear they're a unit and makes them portable.

### 3. Use Absolute Imports for Shared Components

For widely-used components, absolute imports make dependencies clear:

```html+jinja
{#import "components/layout/base.jinja" as Base #}
{#import "components/common/button.jinja" as Button #}
```

Anyone reading this knows exactly where to find these components.

### 4. Group Related Imports

Organize imports by category:

```html+jinja
{#import "layouts/base.jinja" as Base #}
{#import "layouts/sidebar.jinja" as Sidebar #}

{#import "./card.jinja" as Card #}
{#import "./button.jinja" as Button #}

{#import "forms/input.jinja" as Input #}
{#import "forms/select.jinja" as Select #}
```

## Why Explicit Imports?

You might wonder: why not auto-discover components like some frameworks do?

### Clear Dependencies

Look at the imports and immediately know:
- What components this file uses
- Where each component comes from
- If this file has grown too complex (too many imports)

### Easier Refactoring

Move a component? Your editor shows you exactly which imports need updating. With auto-discovery, you'd have to search the entire codebase.

### Better Error Messages

Missing import? You get an error when the component loads, with the exact line number. With auto-discovery, you only find out when you try to render that specific code path.

### Familiar Pattern

Imports work like Python, JavaScript, Go, Rust, and virtually every modern language. If you know one, you know them all.

### No Namespace Pollution

You control the names. A deeply nested `common/forms/inputs/fancy-text-input.jinja` can be imported as simply `TextInput`:

```html+jinja
{#import "common/forms/inputs/fancy-text-input.jinja" as TextInput #}
```

### Better IDE Support (in theory)

In the future, your editor could:

- Autocomplete import paths
- Jump to component definitions (Cmd/Ctrl+Click)
- Show you where a component is defined
- Highlight unused imports
- Refactor renames across files


## Common Patterns

### Layout Component

```html+jinja
{#import "layouts/base.jinja" as Base #}
{#import "./header.jinja" as Header #}
{#import "./footer.jinja" as Footer #}
{#def title #}

<Base title={{ title }}>
  <Header />
  {{ content }}
  <Footer />
</Base>
```

### Recursive Component

Components can import themselves:

```html+jinja
{#import "./tree-node.jinja" as TreeNode #}
{#def node #}

<div class="tree-node">
  <span>{{ node.name }}</span>
  {% if node.children %}
    <div class="tree-children">
      {% for child in node.children %}
        <TreeNode node={{ child }} />
      {% endfor %}
    </div>
  {% endif %}
</div>
```

## Import Resolution

How jx finds components:

1. **Relative imports** (`./`, `../`) - Resolved relative to the current file
2. **Prefixed imports** (`@prefix/`) - Resolved in the prefixed catalog folder
3. **Absolute imports** - Searched in each catalog folder in order until found

If a component can't be found, you get a clear error:

```
ImportError: Component not found: nonexistent.jinja
```

## Next Steps

- **[Arguments](/guides/arguments)** - Learn how to pass data to components
- **[Content & Slots](/guides/content-and-slots)** - Understand content passing
- **[Organization](/advanced/organization)** - Patterns for organizing large projects
