# Components reference

A component is a `.jx` file that works like a typed function: it takes named props, optionally renders content/slots, and produces HTML.

## Anatomy

```html+jinja
{#import "./header.jx" as Header #}    {# 1. imports #}
{#css card.css #}                       {# 2. asset declarations #}
{#js card.js #}
{#def title, subtitle="" #}             {# 3. props #}

<div {{ attrs.render(class="card") }}> {# 4. template #}
  <Header title={{ title }} subtitle={{ subtitle }} />
  <div class="card-body">{{ content }}</div>
</div>
```

All four sections are optional except the template. Order matters: imports/assets/def must come before the template.

## Imports

Jx requires explicit imports — no auto-discovery, no globals.

```html+jinja
{#import "path/to/component.jx" as Name #}
```

The alias must be **PascalCase**. That's how Jx tells `<Card />` (component) from `<div />` (HTML).

**File names** can be anything: `button.jx`, `user-card.jx`, `form_input.jx`. Convention is snake_case for the file, PascalCase for the alias.

### Three import styles

| Style | Example | Resolves against |
|---|---|---|
| Absolute | `{#import "button.jx" as Button #}` | A registered catalog folder |
| Relative | `{#import "./sibling.jx" as Sibling #}` | The current file's directory |
| Prefixed | `{#import "@ui/button.jx" as Button #}` | A prefixed folder (`add_folder(..., prefix="ui")`) |

Use **relative imports** for tightly coupled groups — moving the folder doesn't break the imports.

```
components/
  modal/
    modal.jx       {#import "./header.jx" as Header #}
    header.jx      {#import "./close-btn.jx" as CloseBtn #}
    close-btn.jx
```

## Props (`{#def ... #}`)

```html+jinja
{#def title, count=0, items: list = [], data: dict = {} #}
```

- **No default → required.** Catalog raises if missing.
- **Default → optional.** Any Python literal works (strings, numbers, lists, dicts, etc.).
- **Type annotations are runtime-checked for primitives** (`int`, `str`, `bool`, `list`, `dict`, `tuple`). Containers are checked at the outer level only — `list[str]` checks "is a list", not "all elements are str". Union types and complex generics are not checked.

### Passing props at call sites

```html+jinja
<Button text="Save" />              {# string literal #}
<Card user={{ current_user }} />    {# any expression #}
<Card count={{ items | length }} />
<Card active={{ true }} />
<Input required />                  {# boolean shorthand for required={{ true }} #}
<Input disabled={{ false }} />      {# explicit false #}
```

### Dash-to-underscore

Dashes in the call site become underscores in the def:

```html+jinja
{#def aria_label, data_id #}

<Button aria-label="Close" data-id="123" />
```

Both `aria-label` and `aria_label` map to `aria_label` inside the component.

## Content & slots

Anything between a component's open/close tags is available as `content`.

```html+jinja title="card.jx"
{#def title #}
<div class="card">
  <h3>{{ title }}</h3>
  <div class="body">{{ content }}</div>
</div>
```

```html+jinja title="usage"
<Card title="Hello">
  <p>This becomes the content.</p>
</Card>
```

### Fallback content

```html+jinja
<div class="body">{{ content or "No content provided" }}</div>
```

### Named slots

For multiple content regions, declare slots in the component, fill them at the call site.

```html+jinja title="modal.jx"
<div class="modal">
  <div class="modal-header">
    {% slot header %}<h3>Default Header</h3>{% endslot %}
  </div>
  <div class="modal-body">{{ content }}</div>
  <div class="modal-footer">
    {% slot footer %}<button>Close</button>{% endslot %}
  </div>
</div>
```

```html+jinja title="usage"
<Modal>
  {% fill header %}<h3>Confirm</h3>{% endfill %}
  <p>Are you sure?</p>
  {% fill footer %}
    <button>Yes</button>
    <button>No</button>
  {% endfill %}
</Modal>
```

Unfilled slots use their default content. Slots and `content` can be mixed — `content` is just the implicit, unnamed area.

### Choosing between props, `content`, and slots

| Use | When |
|---|---|
| **Prop** | The value is a string/number/bool, you want type validation, or one piece of structured data (e.g. `user={...}`). |
| **`content`** | Single chunk of HTML, varies in shape, the most common "body" of the component. |
| **Slot** | Multiple distinct regions (header/body/footer), each with its own purpose and possibly defaults. |

## Tag syntax

```html+jinja
<Card title="Hello">                {# block syntax — has content #}
  <p>Body</p>
</Card>

<Button text="Click me" />          {# self-closing — no content #}
```

Either block or self-closing form is allowed; pick whichever matches the component's intent.

## File naming convention

A common idiom (used in the `jx-components` skill):

- **File**: snake_case (`tab_group.jx`).
- **First class on the root element**: CamelCase matching the component's logical name (`class="TabGroup"`).
- **Other classes**: kebab-case (`class="TabGroup tab-group-control"`).

This makes class names self-documenting in DevTools without forcing CamelCase across the whole stylesheet.
