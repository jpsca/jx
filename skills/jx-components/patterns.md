# Patterns

Follow these patterns when building components.

## Buttons

```html
{#def
  label="",
  variant="primary",
  size="md",
  href=""
#}

{% set base = "Button inline-flex items-center justify-center font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-current disabled:opacity-50 disabled:pointer-events-none cursor-pointer" %}

{% set variants = {
  "primary": "bg-indigo-600 text-white hover:bg-indigo-700",
  "secondary": "bg-gray-100 text-gray-800 hover:bg-gray-200",
  "danger": "bg-red-600 text-white hover:bg-red-700",
  "ghost": "text-gray-700 hover:bg-gray-100",
  "outline": "border border-gray-300 text-gray-700 hover:bg-gray-50",
} %}

{% if href %}
  <a href="{{ href }}" {{ attrs.render(
    class=base ~ " " ~ variants[variant]
  ) }}>
    {{ label if label else content }}
  </a>
{% else %}
  <button {{ attrs.render(
    class=base ~ " " ~ variants[variant],
    type="button"
  ) }}>
    {{ label if label else content }}
  </button>
{% endif %}
```

- Renders as `<a>` when `href` is provided, `<button>` otherwise.
- `attrs.render()` merges caller classes and passes through `disabled`, `data-*`, etc.

---

## Modals — use `<dialog>`

```html
{#css transitions.css #}
{#def id, title="" #}

<dialog id="{{ id }}" closedby="any"
  {{ attrs.render(
    class="Dialog bg-white rounded-xl shadow-xl max-w-lg w-full p-0"
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

```html
<button type="submit" formmethod="dialog" formnovalidate>Cancel</button>
<button type="submit">Save</button>
```

---

## Dropdowns — use the Popover API

```html
{#def id, label="Menu" #}

<div {{ attrs.render(class="Dropdown relative inline-block") }}>
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

## Form Inputs

```html
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
    {{ attrs.render(
      type=type,
      name=name,
      required=required,
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

## Data Tables

```html
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

## Sidebar Layout

A responsive sidebar that collapses to a `<dialog>` drawer on mobile. This is a fragment — it produces a flex container, not a full HTML page.

```html
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

--
