# Authoring components

When the user asks to **build** a component (button, card, modal, dropdown, form, table, layout, etc.), follow this guidance to produce production-ready, accessible, framework-agnostic markup. For Jx **syntax** (props, imports, slots, attrs), see `components.md` and `attrs.md` — those are the language reference; this file is the design opinion.

## Core principles

1. **Native HTML first.** Prefer built-in elements and APIs before reaching for JavaScript:
   - **`<dialog>` for modal dialogs.** `.showModal()` opens it in the top layer, with a `::backdrop`, making everything else inert. Close buttons use `<form method="dialog">` or `formmethod="dialog"` on the button — closes with zero JS. Escape dismisses by default.
   - **Popover API for all other floating UI** — dropdowns, tooltips, listboxes, combobox panels, floating menus. Renders in the top layer, escapes `overflow: hidden` clipping. Use `popover` (auto) when the browser handles open/close, `popover="manual"` when JS needs control.
   - **`<details>` for accordions.** Use the `name` attribute for exclusive (one-at-a-time) groups.
   - **Native `<form>` validation** — `required`, `pattern`, `type="email"`, etc.

2. **Vanilla JS as ES modules.** When unavoidable (complex keyboard nav, dynamic filtering, clipboard), declare via `{#js ... #}` and write a small ES module. Keep it minimal and progressively enhancing — components should still work without JS where possible.

3. **Jx idioms.** Explicit imports at top, `{#def ...#}` for typed props with sensible defaults, `attrs` for pass-through HTML attributes, `{{ content }}` and `{% slot %}` for composition, `{#css ...#}` / `{#js ...#}` for per-component assets.

4. **Framework-agnostic.** Unless directed to do the opposite, don't use `url_for`, `csrf_token()`, or other framework helpers. Components must work in Flask, Django, FastAPI, or any Python app. If a component needs a URL, accept it as a prop.

5. **Components are fragments, not pages.** Never emit `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>`. Assume rendering inside an existing page that loads Tailwind and runs `assets.render()`. The page shell is the application's responsibility.

## File structure

Output each component as a `.jx` file. JS-needing components get a sibling `.js` declared via `{#js ... #}`.

```
components/
  button.jx
  card.jx
  modal.jx
  modal.js          ← only if JS is needed
  modal.css         ← only if CSS is needed
  forms/
    input.jx
    select.jx
    textarea.jx
  layout/
    page.jx
    sidebar.jx
```

## File naming

- **File**: snake_case (`tab_group.jx`).
- **First class on the root element**: CamelCase matching the component's logical name (`class="TabGroup"`).
- **Other classes**: kebab-case (`class="TabGroup tab-group-control"`).

```html+jinja title="tab_group.jx"
<div {{ attrs.render(class="TabGroup") }}>
  <select class="tab-group-control"></select>
  {{ content }}
</div>
```

This makes class names self-documenting in DevTools without forcing CamelCase on every utility.

## `attrs` discipline

Bundle every attribute into a single `attrs.render(...)` call. Pre-compute complex values in `{% set ... %}`. Don't fragment attribute logic across the tag.

❌ **Don't:**

```html+jinja
<{{ tag }} role="tab"
  data-tabs-target="tab"
  aria-selected="{{ 'true' if selected else 'false' }}"
  id="{{ target }}-tab"
  tabindex="{{ '0' if selected else '-1' }}"
  {% if disabled %}aria-disabled="true"{% endif %}
  {% if tag == "button" and disabled %}disabled{% endif %}
  {{ attrs.render(class="Tab " ~ ("active" if selected else "")) }}
>
  {{ content }}
</{{ tag }}>
```

✅ **Do:**

```html+jinja
{% set base_classes = "Tab ..." %}
{% set state_class = active_classes if selected else (disabled_classes if disabled else enabled_classes) %}

<{{ tag }}
  {{ attrs.render(
    role="tab",
    data_tabs_target="tab",
    aria_selected="true" if selected else "false",
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

## When to use JavaScript

Reach for JS only when HTML/CSS can't do the job.

| Interaction | Solution |
|---|---|
| Modal dialog | `<dialog>` + `.showModal()` — close via `<form method="dialog">` |
| Backdrop dismiss on modal | `closedby="any"` on `<dialog>` |
| Dropdown menu | Popover API (`popover` + `popovertarget`) |
| Tooltip | Popover API (`popover="hint"`) |
| Floating listbox / combobox | Popover API (`popover="manual"`) + JS for filtering & keyboard nav |
| Any floating/overlay UI | Popover API — always over `absolute` / `z-index` |
| Show/hide panel | `<details>` or Popover API |
| Form validation | Native `required`, `pattern`, `type` attrs |
| Cancel button bypassing validation | `formmethod="dialog"` + `formnovalidate` |
| Tabs | `<details name="...">` for accordion-style; JS only for true tabs |
| Clipboard copy | JS (`navigator.clipboard`) |
| Dynamic list filtering | JS |
| Keyboard shortcuts | JS |
| Complex animations | CSS `@starting-style` + transitions (see `transitions.css`) |

When writing JS:
- Declare it as `{#js component.js #}` in the component.
- ES module (Jx defaults `<script type="module">`).
- Prefer event delegation on `document` over per-element handlers.
- One focused behavior per file, kept small.

## Color mode

Before generating components, ask the user which color mode to support. Three options:

- **Light only** — only light-themed utilities (default grays, whites). No `dark:` prefixes.
- **Dark only** — only dark-themed utilities (dark backgrounds, light text). No `dark:` prefixes since everything is already dark.
- **Both (light + dark)** — light is the base, add `dark:` variants for backgrounds, text, borders, and other color-dependent properties.

```html+jinja
class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-700"
```

If the user hasn't specified, **ask once** at the start; remember their choice for all subsequent components in the conversation. Default to **light only** when in doubt — simpler, the user can always add dark later.

When generating **both** modes, every color-bearing utility needs a `dark:` counterpart: backgrounds, text, borders, ring colors, placeholder colors, divide colors, shadow colors, hover/focus state colors. It's easy to miss one — verify by scanning the diff for `bg-`, `text-`, `border-`, `ring-`, `divide-`, `shadow-` without an adjacent `dark:`.

## Checklist before outputting

1. **Props have sensible defaults** — only truly required data (e.g. `name` on an input) lacks a default.
2. **`attrs.render()` is on the root element** with default classes.
3. **Accessibility** — correct ARIA, keyboard navigability, labels on form elements, focus-visible styles.
4. **No framework-specific helpers** — no `url_for`, `csrf_token()`, etc.
5. **Native HTML first** — no JS for interactions the browser handles natively.
6. **Tailwind classes only** — no custom CSS unless necessary (declare via `{#css ...#}` if so).
7. **No page shell** — no `<!DOCTYPE>` / `<html>` / `<head>` / `<body>`.
8. **Color mode** — confirmed user preference and applied consistently.

## Test files

Generate test files only if the user explicitly asks ("give me test data", "create a test page", "I want to test this component").

When asked, output a `test-<component>.jx` for each **top-level** component (the one the user directly asked for, not internal sub-components). For example, if you create `sidebar.jx` and `sidebar-nav.jx` (a helper), generate `test-sidebar.jx` but not `test-sidebar-nav.jx`.

Each test file should:

- Import the component with a relative path.
- Pass realistic test data exercising all features: required props, optional props with non-default values, slots, edge cases (empty content, long text).
- Be self-contained — renderable on its own with `catalog.render("test-sidebar.jx")` without external context.
- Inline test data (dicts, lists) directly in the template.

**Example:** for a `toast.jx` with variants and auto-dismiss:

```html+jinja
{#import "./toast-container.jx" as ToastContainer #}
{#import "./toast.jx" as Toast #}

<ToastContainer position="top-right">
  <Toast variant="success" message="Changes saved successfully." />
  <Toast variant="error" message="Failed to delete item. Please try again." duration={{ 0 }} />
  <Toast variant="warning" message="Your session will expire in 5 minutes." />
  <Toast variant="info" dismissible={{ false }}>
    This is an <strong>info toast</strong> with rich content and no dismiss button.
  </Toast>
</ToastContainer>
```

Exercises: all four variants, `message` prop vs `{{ content }}`, auto-dismiss disabled, non-dismissible, rich HTML content.

## Component-category recipes

For battle-tested implementations of common UI categories (buttons, modals, dropdowns, form inputs, data tables, sidebar layouts), see `patterns.md`. Read it when the user asks for one of those specifically — it has copy-pasteable starting points.
