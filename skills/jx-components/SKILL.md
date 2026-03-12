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

Follow these patterns when building components. They represent the best way to handle each UI category.

---

### Buttons

```html+jinja
{#def
  label="",
  variant="primary",
  size="md",
  href=""
#}

{% set base = "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-current disabled:opacity-50 disabled:pointer-events-none cursor-pointer" %}

{% set variants = {
  "primary": "bg-indigo-600 text-white hover:bg-indigo-700",
  "secondary": "bg-gray-100 text-gray-800 hover:bg-gray-200",
  "danger": "bg-red-600 text-white hover:bg-red-700",
  "ghost": "text-gray-700 hover:bg-gray-100",
  "outline": "border border-gray-300 text-gray-700 hover:bg-gray-50",
} %}

{% set sizes = {
  "sm": "px-3 py-1.5 text-sm gap-1.5",
  "md": "px-4 py-2 text-sm gap-2",
  "lg": "px-5 py-2.5 text-base gap-2.5",
} %}

{% if href %}
  <a href="{{ href }}" {{ attrs.render(
    class=base ~ " " ~ variants[variant] ~ " " ~ sizes[size]
  ) }}>
    {{ label if label else content }}
  </a>
{% else %}
  <button {{ attrs.render(
    class=base ~ " " ~ variants[variant] ~ " " ~ sizes[size],
    type="button"
  ) }}>
    {{ label if label else content }}
  </button>
{% endif %}
```

- Renders as `<a>` when `href` is provided, `<button>` otherwise.
- `attrs.render()` merges caller classes and passes through `disabled`, `data-*`, etc.

---

### Modals — use `<dialog>`

```html+jinja
{#css transitions.css #}
{#def id, title="" #}

<dialog id="{{ id }}" closedby="any"
  {{ attrs.render(
    class="bg-white rounded-xl shadow-xl max-w-lg w-full p-0"
  ) }}
>
  <div class="flex items-center justify-between p-4 border-b border-gray-200">
    {% slot header %}
      {% if title %}
        <h2 class="text-lg font-semibold text-gray-900">{{ title }}</h2>
      {% endif %}
    {% endslot %}
    <form method="dialog">
      <button type="submit"
        class="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 cursor-pointer"
        aria-label="Close"
        autofocus
      >
        <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>
    </form>
  </div>
  <div class="p-4">
    {{ content }}
  </div>
  {% slot footer %}{% endslot %}
</dialog>
```

Zero JavaScript. Key details from the spec:

- **Close button uses `<form method="dialog">`** — submitting a form with this method closes the dialog natively, no JS needed. Alternatively, use `formmethod="dialog"` on individual buttons.
- **`closedby="any"`** enables light dismiss (clicking the backdrop closes the dialog), Escape key, and developer-specified close buttons. Other values: `"closerequest"` (Escape + JS only, no backdrop dismiss) or `"none"` (only developer-specified mechanisms).
- **`autofocus`** on the close button gives it focus when the dialog opens, which is the recommended pattern per the spec.
- **Escape key** dismisses modal dialogs by default (provided `closedby` is not `"none"`).
- **`transitions.css`** handles the fade+scale enter/exit animation and the backdrop fade (see the Animations section).
- The caller opens the dialog with `document.getElementById("my-modal").showModal()`.

When the dialog contains a form with required fields and you need a cancel button that bypasses validation, add `formnovalidate` to the cancel button:

```html+jinja
<button type="submit" formmethod="dialog" formnovalidate>Cancel</button>
<button type="submit">Save</button>
```

---

### Dropdowns — use the Popover API

```html+jinja
{#def id, label="Menu" #}

<div {{ attrs.render(class="relative inline-block") }}>
  <button popovertarget="{{ id }}" class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 cursor-pointer">
    {{ label }}
    <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
    </svg>
  </button>
  <div id="{{ id }}" popover
    class="m-0 absolute top-full left-0 mt-1 min-w-48 bg-white rounded-lg shadow-lg ring-1 ring-gray-200 p-1"
  >
    {{ content }}
  </div>
</div>
```

No JavaScript needed — the browser handles show/hide via the `popover`/`popovertarget` attributes. The popover renders in the top layer, so it won't be clipped by `overflow: hidden` on parent containers.

For components that need JS control over a floating panel (like a combobox with filtering), use `popover="manual"` instead of `popover` (auto). This gives you full control via `.showPopover()` / `.hidePopover()` while still getting top-layer rendering. Position the popover with `position: fixed` and `getBoundingClientRect()` to track the trigger element.

---

### Accordions — use `<details>`

```html+jinja
{#def title, open=false #}

<details {{ "open" if open else "" }} {{ attrs.render(
  class="group border border-gray-200 rounded-lg"
) }}>
  <summary class="flex items-center justify-between p-4 cursor-pointer select-none font-medium text-gray-900 hover:bg-gray-50 rounded-lg list-none [&::-webkit-details-marker]:hidden">
    {{ title }}
    <svg class="size-5 text-gray-500 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
    </svg>
  </summary>
  <div class="px-4 pb-4 text-gray-600">
    {{ content }}
  </div>
</details>
```

For exclusive (one-at-a-time) accordions, use the `name` attribute on `<details>`:

```html+jinja
<Details title="Section 1" name="faq">...</Details>
<Details title="Section 2" name="faq">...</Details>
```

No JavaScript needed.

---

### Form Inputs

```html+jinja
{#def name, label="", type="text", required=false, error="" #}

{% do attrs.setdefault(id=name) %}

<div class="space-y-1.5">
  {% if label %}
    <label for="{{ attrs.get('id', name) }}" class="block text-sm font-medium text-gray-700">
      {{ label }}
      {% if required %}<span class="text-red-500">*</span>{% endif %}
    </label>
  {% endif %}
  <input
    type="{{ type }}"
    name="{{ name }}"
    {% if required %}required{% endif %}
    {{ attrs.render(
      class="block w-full rounded-lg border px-3 py-2 text-sm shadow-sm focus:outline-2 focus:outline-indigo-500 " ~
        ("border-red-300 text-red-900 placeholder:text-red-300" if error else "border-gray-300 text-gray-900 placeholder:text-gray-400")
    ) }}
  />
  {% if error %}
    <p class="text-sm text-red-600">{{ error }}</p>
  {% endif %}
</div>
```

Lean on native HTML validation (`required`, `pattern`, `minlength`, `type="email"`, etc.) before adding JS validation.

---

### Data Tables

```html+jinja
{#def headers=[], rows=[], striped=true, hoverable=true #}

<div {{ attrs.render(class="overflow-x-auto rounded-lg border border-gray-200") }}>
  <table class="min-w-full divide-y divide-gray-200 text-sm">
    {% if headers %}
      <thead class="bg-gray-50">
        <tr>
          {% for header in headers %}
            <th class="px-4 py-3 text-left font-semibold text-gray-700">{{ header }}</th>
          {% endfor %}
        </tr>
      </thead>
    {% endif %}
    <tbody class="divide-y divide-gray-100">
      {% for row in rows %}
        <tr class="{{ 'bg-gray-50/50' if striped and loop.index is odd else '' }} {{ 'hover:bg-gray-50' if hoverable else '' }}">
          {% for cell in row %}
            <td class="px-4 py-3 text-gray-600">{{ cell }}</td>
          {% endfor %}
        </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

For more complex tables where cells need custom markup, use content with `{% slot %}` instead of the `rows` prop.

---

### Sidebar Layout

A responsive sidebar that collapses to a `<dialog>` drawer on mobile. This is a fragment — it produces a flex container, not a full HTML page.

```html+jinja
{#import "./sidebar-nav.jinja" as SidebarNav #}
{#css transitions.css #}
{#def title="", nav_items=[], current="" #}

<div {{ attrs.render(class="lg:flex min-h-screen") }}>

  {# Mobile header with menu trigger #}
  <header class="sticky top-0 z-30 flex items-center justify-between bg-white border-b border-gray-200 px-4 py-3 lg:hidden">
    <span class="text-lg font-semibold text-gray-900">{{ title }}</span>
    <button
      type="button"
      onclick="document.getElementById('mobile-nav').showModal()"
      class="p-2 rounded-lg text-gray-600 hover:bg-gray-100 cursor-pointer"
      aria-label="Open menu"
    >
      <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
      </svg>
    </button>
  </header>

  {# Mobile nav — <dialog> slide-over drawer with slide-from-left animation #}
  <dialog
    id="mobile-nav"
    closedby="any"
    class="slide-from-left fixed inset-0 z-40 m-0 h-full w-72 max-h-full max-w-full bg-white p-0 shadow-xl lg:hidden"
  >
    <div class="flex items-center justify-between p-4 border-b border-gray-200">
      <span class="text-lg font-semibold text-gray-900">{{ title }}</span>
      <form method="dialog">
        <button type="submit"
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 cursor-pointer"
          aria-label="Close menu">
          <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </form>
    </div>
    <nav class="flex-1 overflow-y-auto p-4">
      <SidebarNav items={{ nav_items }} current={{ current }} />
    </nav>
  </dialog>

  {# Desktop sidebar #}
  <aside class="hidden lg:flex lg:flex-col lg:w-64 lg:shrink-0 bg-white border-r border-gray-200">
    <div class="flex items-center h-16 px-6 border-b border-gray-200">
      <span class="text-lg font-semibold text-gray-900">{{ title }}</span>
    </div>
    <nav class="flex-1 overflow-y-auto p-4">
      <SidebarNav items={{ nav_items }} current={{ current }} />
    </nav>
    {% slot sidebar_footer %}{% endslot %}
  </aside>

  {# Main content #}
  <main class="flex-1 min-w-0 p-6 lg:p-8">
    {{ content }}
  </main>
</div>
```

The mobile drawer uses `<dialog>` with `showModal()`. The `closedby="any"` attribute enables light dismiss (backdrop click) and Escape key. The close button uses `<form method="dialog">` — no JS needed. The `slide-from-left` class (from `transitions.css`) gives it a smooth slide-in/out animation. The nav items use `<details>` for collapsible sections (see the Accordions pattern).

Note: Opening a dialog still requires a small `onclick` to call `.showModal()` — there's no declarative way to open a dialog, unlike popovers which have `popovertarget`.

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
