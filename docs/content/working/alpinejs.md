---
title: Working with Alpine.js
description: Using Jx components with Alpine.js for reactive interactions
---

[Alpine.js](https://alpinejs.dev) is a lightweight JavaScript framework that adds reactivity directly in your HTML. It's perfect for adding interactivity to Jx components without a build step.

::: warning
This page is a work in progress and may contain errors.
:::

## Setup

Include Alpine in your layout:

```html+jinja title="components/layout.jx"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
  {{ assets.render_css() }}
</head>
<body>
  {{ content }}
  {{ assets.render_js() }}
</body>
</html>
```

## Passing Alpine Attributes

Jx converts underscores to dashes, so Alpine directives work naturally:

```html+jinja
<button
  @click="open = true"
  x_show="!loading"
  x_bind:disabled="loading"
>
  Click me
</button>
```

Renders as:

```html
<button
  @click="open = true"
  x-show="!loading"
  x-bind:disabled="loading"
>
  Click me
</button>
```

## Dropdown Component

```html+jinja title="components/dropdown.jx"
{#def label #}
{#css dropdown.css #}

<div class="dropdown" x-data="{ open: false }" @click.outside="open = false">
  <button
    @click="open = !open"
    :aria-expanded="open"
    {{ attrs.render(class="dropdown-toggle") }}
  >
    {{ label }}
    <span :class="{ 'rotate-180': open }">▼</span>
  </button>

  <div
    class="dropdown-menu"
    x-show="open"
    x-transition
    x-cloak
  >
    {{ content }}
  </div>
</div>
```

```html+jinja title="usage"
{#import "dropdown.jx" as Dropdown #}

<Dropdown label="Options">
  <a href="/profile">Profile</a>
  <a href="/settings">Settings</a>
  <hr>
  <a href="/logout">Logout</a>
</Dropdown>
```

## Modal with Alpine

```html+jinja title="components/alpine-modal.jx"
{#def name, title="" #}
{#css modal.css #}

<div
  x-data="{ open: false }"
  x-on:open-modal-{{ name }}.window="open = true"
  x-on:keydown.escape.window="open = false"
  {{ attrs.render() }}
>
  {# Trigger slot #}
  <div @click="open = true">
    {% slot trigger %}
      <button>Open Modal</button>
    {% endslot %}
  </div>

  {# Modal #}
  <template x-teleport="body">
    <div
      class="modal-overlay"
      x-show="open"
      x-transition.opacity
      x-cloak
    >
      <div
        class="modal-content"
        @click.outside="open = false"
        x-show="open"
        x-transition
      >
        {% if title %}
          <div class="modal-header">
            <h2>{{ title }}</h2>
            <button @click="open = false">&times;</button>
          </div>
        {% endif %}

        <div class="modal-body">
          {{ content }}
        </div>

        {% slot footer %}{% endslot %}
      </div>
    </div>
  </template>
</div>
```

```html+jinja title="usage"
{#import "alpine-modal.jx" as Modal #}

<Modal name="confirm" title="Confirm Action">
  {% fill trigger %}
    <button class="btn btn-danger">Delete Item</button>
  {% endfill %}

  <p>Are you sure you want to delete this item?</p>

  {% fill footer %}
    <div class="modal-footer">
      <button @click="open = false">Cancel</button>
      <button class="btn btn-danger">Delete</button>
    </div>
  {% endfill %}
</Modal>

{# Or trigger from elsewhere #}
<button @click="$dispatch('open-modal-confirm')">Delete</button>
```

## Tabs with Alpine

```html+jinja title="components/alpine-tabs.jx"
{#def default="" #}
{#css tabs.css #}

<div x-data="{ activeTab: '{{ default }}' }" {{ attrs.render(class="tabs") }}>
  {{ content }}
</div>
```

```html+jinja title="components/alpine-tab.jx"
{#def name #}

<button
  @click="activeTab = '{{ name }}'"
  :class="{ 'active': activeTab === '{{ name }}' }"
  {{ attrs.render(class="tab") }}
>
  {{ content }}
</button>
```

```html+jinja title="components/alpine-tab-panel.jx"
{#def name #}

<div
  x-show="activeTab === '{{ name }}'"
  x-transition
  {{ attrs.render(class="tab-panel") }}
>
  {{ content }}
</div>
```

```html+jinja title="usage"
{#import "alpine-tabs.jx" as Tabs #}
{#import "alpine-tab.jx" as Tab #}
{#import "alpine-tab-panel.jx" as TabPanel #}

<Tabs default="overview">
  <div class="tab-list">
    <Tab name="overview">Overview</Tab>
    <Tab name="features">Features</Tab>
    <Tab name="pricing">Pricing</Tab>
  </div>

  <TabPanel name="overview">
    <h2>Overview</h2>
    <p>Overview content here.</p>
  </TabPanel>

  <TabPanel name="features">
    <h2>Features</h2>
    <p>Features content here.</p>
  </TabPanel>

  <TabPanel name="pricing">
    <h2>Pricing</h2>
    <p>Pricing content here.</p>
  </TabPanel>
</Tabs>
```

## Accordion with Alpine

```html+jinja title="components/alpine-accordion.jx"
{#def multiple=false #}
{#css accordion.css #}

<div
  x-data="{ active: {{ '[]' if multiple else 'null' }} }"
  {{ attrs.render(class="accordion") }}
>
  {{ content }}
</div>
```

```html+jinja title="components/alpine-accordion-item.jx"
{#def id, title #}

<div class="accordion-item">
  <button
    class="accordion-header"
    @click="active = active === '{{ id }}' ? null : '{{ id }}'"
    :aria-expanded="active === '{{ id }}'"
  >
    {{ title }}
    <span x-text="active === '{{ id }}' ? '−' : '+'"></span>
  </button>

  <div
    class="accordion-content"
    x-show="active === '{{ id }}'"
    x-collapse
  >
    <div class="accordion-body">
      {{ content }}
    </div>
  </div>
</div>
```

```html+jinja title="usage"
{#import "alpine-accordion.jx" as Accordion #}
{#import "alpine-accordion-item.jx" as AccordionItem #}

<Accordion>
  <AccordionItem id="q1" title="What is Alpine.js?">
    <p>Alpine.js is a lightweight JavaScript framework.</p>
  </AccordionItem>

  <AccordionItem id="q2" title="Why use it with Jx?">
    <p>It adds reactivity without a build step.</p>
  </AccordionItem>
</Accordion>
```

## Toggle Component

```html+jinja title="components/toggle.jx"
{#def name, label, checked=false #}
{#css toggle.css #}

<label class="toggle" x-data="{ on: {{ 'true' if checked else 'false' }} }">
  <input
    type="checkbox"
    name="{{ name }}"
    x-model="on"
    class="sr-only"
  />
  <span
    class="toggle-track"
    :class="{ 'active': on }"
  >
    <span class="toggle-thumb" :class="{ 'active': on }"></span>
  </span>
  <span class="toggle-label">{{ label }}</span>
</label>
```

## Counter Component

```html+jinja title="components/counter.jx"
{#def name, value=0, min=0, max=100 #}

<div class="counter" x-data="{ count: {{ value }} }">
  <button
    @click="count = Math.max({{ min }}, count - 1)"
    :disabled="count <= {{ min }}"
  >
    −
  </button>

  <input
    type="number"
    name="{{ name }}"
    x-model="count"
    min="{{ min }}"
    max="{{ max }}"
    {{ attrs.render() }}
  />

  <button
    @click="count = Math.min({{ max }}, count + 1)"
    :disabled="count >= {{ max }}"
  >
    +
  </button>
</div>
```

## Notification Toast

```html+jinja title="components/toast.jx"
{#def message, type="info", duration=3000 #}
{#css toast.css #}

<div
  x-data="{ show: true }"
  x-init="setTimeout(() => show = false, {{ duration }})"
  x-show="show"
  x-transition
  class="toast toast-{{ type }}"
>
  <span>{{ message }}</span>
  <button @click="show = false">&times;</button>
</div>
```

## Form with Validation

```html+jinja title="components/validated-form.jx"
{#def action, method="post" #}

<form
  action="{{ action }}"
  method="{{ method }}"
  x-data="{
    errors: {},
    validate() {
      this.errors = {};
      // Add validation logic
      return Object.keys(this.errors).length === 0;
    }
  }"
  @submit="if (!validate()) $event.preventDefault()"
  {{ attrs.render() }}
>
  {{ content }}
</form>
```

## Password Visibility Toggle

```html+jinja title="components/password-input.jx"
{#def name, label="" #}

<div class="form-group" x-data="{ show: false }">
  {% if label %}
    <label for="{{ name }}">{{ label }}</label>
  {% endif %}

  <div class="input-group">
    <input
      :type="show ? 'text' : 'password'"
      name="{{ name }}"
      id="{{ name }}"
      {{ attrs.render(class="form-control") }}
    />
    <button type="button" @click="show = !show" class="input-addon">
      <span x-text="show ? 'Hide' : 'Show'"></span>
    </button>
  </div>
</div>
```

## Tips

1. **Use `x-cloak`** to prevent flash of unstyled content
2. **Prefer `x-data` on the component root** for encapsulation
3. **Use `$dispatch`** for cross-component communication
4. **Leverage `x-transition`** for smooth animations
5. **Keep state local** when possible; use Alpine stores for global state

```css title="Add to your CSS"
[x-cloak] {
  display: none !important;
}
```
