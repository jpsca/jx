---
name: jx-components
description: Create web UI components using Jx (Jinja2 component library), TailwindCSS v4, and modern vanilla JavaScript. Use this skill whenever the user asks to build, create, or generate Jinja components, Jx components, UI components for a Python web app, reusable template components, or anything involving `.jinja` component files. Also trigger when the user mentions Jx, JinjaX, TailwindCSS with Jinja, or asks for buttons, cards, modals, forms, tables, layouts, navigation, dropdowns, accordions, or any other UI element as a Jinja/Jx component. Even if the user just says "make me a card component" or "I need a dropdown" in the context of a Python web project, use this skill.
---

# Jx Components Skill

Create production-ready, reusable UI components using **Jx** (a Jinja2 component library), styled with **TailwindCSS v4**, and enhanced with **modern vanilla JavaScript** only when native HTML can't handle the interaction.

## Core Principles

1. **Native HTML first.** Always prefer built-in HTML elements and APIs before reaching for JavaScript:
   - **`<dialog>` for modal dialogs.** Use `showModal()` to open — it renders in the top layer, adds a `::backdrop`, and makes everything else inert. Close buttons should use `<form method="dialog">` or `formmethod="dialog"` on the button, which closes the dialog with zero JS. The Escape key dismisses modal dialogs by default.
   - **Popover API for all other floating/overlay UI** — dropdowns, tooltips, listboxes, combobox panels, floating menus. The Popover API also renders in the top layer, escaping `overflow: hidden` clipping. Prefer it over `position: absolute` / `z-index`. Use `popover` (auto) when the browser should handle open/close, and `popover="manual"` when JS needs control (e.g., a combobox that opens on input focus and filters as you type).
   - **`<details>` for accordions and collapsible sections.** Use the `name` attribute for exclusive (one-at-a-time) groups.
   - **Native `<form>` validation** — `required`, `pattern`, `type="email"`, etc.

2. **Tailwind v4 for styling.** Use Tailwind's utility classes directly in component markup. Tailwind v4 uses a CSS-first configuration model (no `tailwind.config.js`). Prefer modern utilities and don't rely on deprecated v3 patterns.

3. **Vanilla JS as ES modules.** When JavaScript is unavoidable (e.g., complex keyboard navigation, dynamic filtering, clipboard actions), write it as a small ES module declared via `{#js ... #}`. Keep scripts minimal, focused, and progressively enhancing — the component should still be usable without JS where possible.

4. **Jx idioms.** Follow Jx conventions: explicit imports at the top, `{#def ...#}` for typed props with sensible defaults, `attrs` for pass-through HTML attributes, `{{ content }}` and `{% slot %}` for composition, and `{#css ...#}` / `{#js ...#}` for per-component assets.

5. **Framework-agnostic.** Don't use `url_for`, `csrf_token()`, or other framework-specific helpers. Components should work with Flask, Django, FastAPI, or any Python app using Jx. If a component needs a URL, accept it as a prop.

6. **Components are fragments, not pages.** Never output `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>` tags. Assume the component will be rendered inside an existing HTML page that already loads Tailwind and renders any declared `{#css}` / `{#js}` assets. The page shell is the application's responsibility — components just produce the markup that goes inside it.

## Component File Structure

Output each component as a `.jinja` file. For components that need JS, output a companion `.js` file declared via `{#js ...#}`.

```
components/
  button.jinja
  card.jinja
  modal.jinja
  modal.js          ← only if JS is needed
  forms/
    input.jinja
    select.jinja
    textarea.jinja
  layout/
    page.jinja
    sidebar.jinja
```

## Jx Syntax Reference

### Imports, Props, Assets

```html+jinja
{#import "./icon.jinja" as Icon #}
{#css button.css #}
{#js button.js #}
{#def label, variant="primary", size="md", disabled=false #}
```

- Props with no default are **required**.
- Props with a default are **optional**.
- Type annotations are supported: `{#def count: int = 0 #}`.

### Using `attrs`

The `attrs` object collects any HTML attributes passed to a component that aren't declared in `{#def}`. Always render attrs on the component's root element so callers can pass `id`, `class`, `data-*`, `aria-*`, etc.

```html+jinja
<button {{ attrs.render(class="btn", type="button") }}>
  {{ label }}
</button>
```

Key behaviors:
- `class` **merges** (caller classes are appended to defaults).
- Other attributes **override**.
- `disabled` (boolean shorthand) becomes `disabled={{ true }}`.
- Underscores convert to dashes: `data_id` → `data-id`.

IMPORTANT: If possible, include every attribute inside the `attrs.render()` call

DO NOT DO THIS:

```html+jinja
<{{ tag }} role="tab"
  data-tabs-target="tab"
  data-action="click->tabs#selectTab keydown->tabs#keydown"
  aria-selected="{{ 'true' if selected else 'false' }}"
  aria-controls="{{ target }}"
  id="{{ target }}-tab"
  tabindex="{{ '0' if selected else '-1' }}"
  {% if disabled %}aria-disabled="true"{% endif %}
  {% if tag == "button" and disabled %}disabled{% endif %}
  {{ attrs.render(
    class="Tab base-classes" ~ (
      "classes-when-selected" if selected else (
        "classes-when-disabled" if disabled else
        "classes-when-enabled"
      ))
  ) }}
>
  {{ content }}
</{{ tag }}>
```

DO THIS INSTEAD:

```html+jinja
{% set base_classes = "Tab ..." %}
{% set selected_classes = "..." %}
{% set disabled_classes = "..." %}
{% set enabled_classes = "..." %}

<{{ tag }}
  {{ attrs.render(
    role="tab",
    data_tabs_target="tab",
    data_action="click->tabs#selectTab keydown->tabs#keydown",
    aria_selected="{{ 'true' if selected else 'false' }}",
    aria_controls="{{ target }}",
    id="{{ target }}-tab",
    tabindex="{{ '0' if selected else '-1' }}",
    aria_disabled="true" if disabled else False,
    disabled=(tag == "button" and disabled),
    class=base_classes ~ (selected_classes if selected else (disabled_classes if disabled else enabled_classes)),
  ) }}
>
  {{ content }}
</{{ tag }}>
```

If one attribute cannot be calculated in a short one-liner, calculate it beforehand inside a `{% set attribute = ... %}` expression.

### Content and Slots

```html+jinja
{# Single content area #}
<div class="card-body">{{ content }}</div>

{# Named slots with fallbacks #}
{% slot header %}<h3>Default</h3>{% endslot %}

{# Caller fills a slot #}
{% fill header %}<h3>Custom Header</h3>{% endfill %}
```

### Asset Declarations

```html+jinja
{#css card.css #}
{#js card.js #}
```

Assets are collected recursively from the component tree and deduplicated. The layout component renders them via `{{ assets.render_css() }}` and `{{ assets.render_js() }}`.

## Component Patterns

Follow the patterns at ./patterns.md when building components. They represent the best way to handle each UI category.

## File names

Use snake_case for the file names, but add the CamelCased name of the component as the first class.
Any other class should be kebab-cased.

Example:

```html+jinja title="tab_group.jinja"
<div {{ attrs.render(class="TabGroup") }}>
  <select class="tab-group-control"
  {{ content }}
</div>
```


## Animations — `transitions.css`

Tailwind v4 doesn't have utilities for `@starting-style` or `transition-behavior: allow-discrete`, which are needed for smooth enter/exit animations on `<dialog>` and popover elements. Instead of writing per-component CSS, use a shared `transitions.css` file. Jx's asset deduplication ensures it only loads once no matter how many components declare it.

Declare it in any component that needs animations:

```html+jinja
{#css transitions.css #}
```

The file provides three animation patterns:

**Default dialog (fade + scale)** — automatically applies to all `<dialog>` elements. Fades and scales in on open, reverses on close. Backdrop fades to a semi-transparent overlay.

**`slide-from-left`** — add this class to a `<dialog>` for a drawer that slides in from the left edge (used for mobile navigation drawers).

**`slide-from-right`** — same, but from the right edge (useful for detail panels, cart drawers, etc.).

### `transitions.css` contents

The full CSS is bundled at `assets/transitions.css` in this skill's folder. When generating a component that uses animations, read that file and output it alongside the `.jinja` files (unless the user already has it).

The CSS uses `@starting-style` and `allow-discrete` for proper enter/exit transitions — these are well-supported in modern browsers. No JavaScript is involved.

## When to Use JavaScript

Only reach for JS when HTML/CSS can't do the job. Here's a guide:

| Interaction | Solution |
|---|---|
| Modal dialog | `<dialog>` + `.showModal()` — close via `<form method="dialog">` or `formmethod="dialog"` |
| Backdrop dismiss on modal | `closedby="any"` attribute on `<dialog>` |
| Dropdown menu | Popover API (`popover` + `popovertarget`) |
| Tooltip | Popover API with `popover="hint"` |
| Floating listbox / combobox | Popover API (`popover="manual"`) + JS for filtering & keyboard nav |
| Any floating/overlay UI | Popover API — always prefer over `absolute` / `z-index` |
| Show/hide panel | `<details>` or Popover API |
| Form validation | Native `required`, `pattern`, `type` attrs |
| Cancel button bypassing validation | `formmethod="dialog"` + `formnovalidate` on the button |
| Tabs | Native `<details name="...">` for accordion-style, or JS for true tabs |
| Clipboard copy | JS (`navigator.clipboard`) |
| Dynamic list filtering | JS |
| Keyboard shortcuts | JS |
| Complex animations | CSS `@starting-style` + transitions (see Animations section) |

When writing JS:
- Declare it as `{#js component.js #}` in the component.
- Write it as an ES module (`type="module"` is the Jx default).
- Use event delegation on `document` rather than per-element handlers where possible.
- Keep it small — a single focused behavior per file.

## Color Mode

Before generating components, ask the user which color mode to support:

- **Light only** — use only light-themed utility classes (default grays, whites, etc.). No `dark:` prefixes.
- **Dark only** — use only dark-themed utility classes (dark backgrounds, light text). No `dark:` prefixes needed since everything is already dark.
- **Both (light + dark)** — use light as the base and add `dark:` variants for backgrounds, text, borders, and other color-dependent properties. Example: `class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-700"`.

If the user hasn't specified, ask once at the start. Remember their choice for all subsequent components in the conversation. When in doubt, default to **light only** — it's simpler and the user can always ask for dark mode later.

When generating **both** modes, apply `dark:` variants to every color-bearing utility. Don't forget: backgrounds, text, borders, ring colors, placeholder colors, divide colors, shadow colors, and hover/focus state colors all need dark counterparts.

## Checklist Before Outputting a Component

1. **Props have sensible defaults** — only truly required data (like `name` on an input) should lack a default.
2. **`attrs.render()` is on the root element** (or the most semantically meaningful element) with default classes.
3. **Accessibility** — correct ARIA attributes, keyboard navigability, labels on form elements, focus-visible styles.
4. **No framework-specific helpers** — no `url_for`, `csrf_token()`, etc. Accept URLs and tokens as props if needed.
5. **Native HTML first** — no JS for interactions the browser handles natively.
6. **Tailwind classes only** — no custom CSS unless absolutely necessary (declared via `{#css ...#}` if so).
7. **No page shell** — no `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>`. Components are fragments rendered inside an existing page.
8. **Color mode** — confirm the user's preference (light/dark/both) and apply it consistently. If "both", verify every color utility has a `dark:` counterpart.

## Test Files

Only generate test files if the user explicitly asks for them (e.g., "give me test data", "create a test page", "I want to test this component").

When asked, output a `test-<component>.jinja` file for each **top-level** component — meaning the component the user directly asked for, not its internal sub-components. For example, if you create `sidebar.jinja` and `sidebar-nav.jinja` (a helper it imports), generate `test-sidebar.jinja` but not `test-sidebar-nav.jinja`.

Each test file should:

- Import the component with a relative path.
- Pass realistic, representative test data that exercises all the component's features: required props, optional props with non-default values, slots, edge cases like empty content or long text.
- Be self-contained — renderable on its own with `catalog.render("test-sidebar.jinja")` without any external data.
- Include inline test data (dicts, lists) directly in the template rather than relying on Python-side context.

**Example:** for a `toast.jinja` with variants and auto-dismiss:

```html+jinja
{#import "./toast-container.jinja" as ToastContainer #}
{#import "./toast.jinja" as Toast #}

<ToastContainer position="top-right">
  <Toast variant="success" message="Changes saved successfully." />
  <Toast variant="error" message="Failed to delete item. Please try again." duration={{ 0 }} />
  <Toast variant="warning" message="Your session will expire in 5 minutes." />
  <Toast variant="info" dismissible={{ false }}>
    This is an <strong>info toast</strong> with rich content and no dismiss button.
  </Toast>
</ToastContainer>
```

This exercises: all four variants, the `message` prop vs `{{ content }}`, auto-dismiss disabled (`duration=0`), non-dismissible, and rich HTML content.
