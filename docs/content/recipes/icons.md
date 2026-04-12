---
title: SVG Icons
description: Using components for SVG icons
---

Components are perfect for SVG icons - encapsulate the SVG code once, reuse it everywhere with customizable size and color.

## Basic Icon Component

```html+jinja title="components/icons/icon-check.jx"
{#def size=24 #}

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{{ size }}"
  height="{{ size }}"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  {{ attrs.render(class="icon icon-check") }}
>
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>
```

```html+jinja title="usage"
{#import "icons/icon-check.jx" as IconCheck #}

<IconCheck />
<IconCheck size="32" />
<IconCheck class="text-green" />
```

::: tab | Preview
<p class="preview">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-check"
>
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="32"
  height="32"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-check"
>
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-check text-green"
>
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>
</p>
:::

## Generic Icon Wrapper

Create a base component that other icons extend:

```html+jinja title="components/icons/icon.jx"
{#def size=24 #}

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{{ size }}"
  height="{{ size }}"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  {{ attrs.render(class="icon") }}
>
  {{ content }}
</svg>
```

```html+jinja title="components/icons/icon-x.jx"
{#import "./icon.jx" as Icon #}
{#def size=24 #}

{% do attrs.set(size=size) %}

<Icon attrs={{ attrs }}>
  <line x1="18" y1="6" x2="6" y2="18"></line>
  <line x1="6" y1="6" x2="18" y2="18"></line>
</Icon>
```

```html+jinja title="components/icons/icon-menu.jx"
{#import "./icon.jx" as Icon #}
{#def size=24 #}

{% do attrs.set(size=size) %}

<Icon attrs={{ attrs }}>
  <line x1="3" y1="12" x2="21" y2="12"></line>
  <line x1="3" y1="6" x2="21" y2="6"></line>
  <line x1="3" y1="18" x2="21" y2="18"></line>
</Icon>
```

::: tab | Preview
<p class="preview">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon"
>
  <line x1="18" y1="6" x2="6" y2="18"></line>
  <line x1="6" y1="6" x2="18" y2="18"></line>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon"
>
  <line x1="3" y1="12" x2="21" y2="12"></line>
  <line x1="3" y1="6" x2="21" y2="6"></line>
  <line x1="3" y1="18" x2="21" y2="18"></line>
</svg>
</p>
:::

## Dynamic Icon Component

Load icons by name:

```html+jinja title="components/icon.jx"
{#def name, size=24 #}

{% set icons = {
  "check": '<polyline points="20 6 9 17 4 12"></polyline>',
  "x": '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>',
  "menu": '<line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line>',
  "search": '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
  "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>',
} %}

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{{ size }}"
  height="{{ size }}"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  {{ attrs.render(class="icon icon-" ~ name) }}
>
  {{ icons.get(name, "") | safe }}
</svg>
```

```html+jinja title="usage"
{#import "icon.jx" as Icon #}

<Icon name="x" size="16" />
<Icon name="menu" class="text-gray-600" />
<Icon name="search" />
```

::: tab | Preview
<p class="preview">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="16"
  height="16"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-x"
>
<line x1="18" y1="6" x2="6" y2="18"></line>
<line x1="6" y1="6" x2="18" y2="18"></line>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="16"
  height="16"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-menu text-gray-600"
>
<line x1="3" y1="12" x2="21" y2="12"></line>
<line x1="3" y1="6" x2="21" y2="6"></line>
<line x1="3" y1="18" x2="21" y2="18"></line>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-search"
>
<circle cx="11" cy="11" r="8"></circle>
<line x1="21" y1="21" x2="16.65" y2="16.65"></line>
</svg>
</p>
:::

## Icon Button

Combine icons with buttons:

```html+jinja title="components/icon-button.jx"
{#def label="" #}
{#css icon-button.css #}

{% do attrs.setdefault(type="button") %}
{% do attrs.set(aria_label=label if label else None) %}

<button {{ attrs.render(class="btn btn--icon") }}>
  {{ content }}
</button>
```

```html+jinja title="usage"
{#import "icon-button.jx" as IconButton #}
{#import "icons/icon-x.jx" as IconX #}

<IconButton label="Close" @click="close()">
  <IconX size={{ 20 }} />
</IconButton>
```

::: tab | Preview
<p class="preview">
<button class="btn btn--icon" type="button" aria-label="Close">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="20"
  height="20"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-x"
>
<line x1="18" y1="6" x2="6" y2="18"></line>
<line x1="6" y1="6" x2="18" y2="18"></line>
</svg>
</button>
</p>
:::

## Button with Icon and Text

```html+jinja title="components/button.jx"
{#def text="" #}
{#css button.css #}

{% do attrs.setdefault(type="button") %}

<button {{ attrs.render(class="btn") }}>
  {% slot icon %}{% endslot %}
  {% if text %}
    <span>{{ text }}</span>
  {% else %}
    {{ content }}
  {% endif %}
</button>
```

```html+jinja title="usage"
{#import "button.jx" as Button #}
{#import "icons/icon-check.jx" as IconCheck #}

<Button text="Save">
  {% fill icon %}
    <IconCheck size="18" aria_hidden />
  {% endfill %}
</Button>
```


::: tab | Preview
<p class="preview">
<button class="btn" type="button">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="18"
  height="18"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  class="icon icon-x"
>
<polyline points="20 6 9 17 4 12"></polyline>
</svg>
<span>Save</span>
</button>
</p>
:::

## Filled vs Stroke Icons

```html+jinja title="components/icons/icon-heart.jx"
{#def size=24, filled=false #}

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{{ size }}"
  height="{{ size }}"
  viewBox="0 0 24 24"
  fill="{{ 'currentColor' if filled else 'none' }}"
  stroke="currentColor"
  stroke-width="2"
  {{ attrs.render(class="icon icon-heart") }}
>
  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
</svg>
```

```html+jinja title="usage"
<IconHeart />                    {# Outline #}
<IconHeart filled />             {# Filled #}
<IconHeart filled class="text-red-500" />
```

::: tab | Preview
<p class="preview">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  class="icon icon-heart"
>
  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="currentColor"
  stroke="currentColor"
  stroke-width="2"
  class="icon icon-heart"
>
  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
</svg>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="currentColor"
  stroke="currentColor"
  stroke-width="2"
  class="icon icon-heart text-red-500"
>
  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
</svg>
</p>
:::

## Spinner Icon

```html+jinja title="components/icons/icon-spinner.jx"
{#def size=24 #}
{#css spinner.css #}

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{{ size }}"
  height="{{ size }}"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  {{ attrs.render(class="icon icon-spinner") }}
>
  <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
  <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
</svg>
```

```css title="spinner.css"
.icon-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

::: tab | Preview
<p class="preview">
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  class="icon icon-spinner"
>
  <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
  <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
</svg>
</p>
:::

## Icon with Badge

```html+jinja title="components/icon-badge.jx"
{#def count=0 #}
{#css icon-badge.css #}

<span class="icon-badge-wrapper">
  {{ content }}
  {% if count > 0 %}
    <span class="icon-badge">{{ count if count < 100 else "99+" }}</span>
  {% endif %}
</span>
```

```css title="icon-badge.css"
.icon-badge-wrapper {
  position: relative;
  display: inline-flex;
}

.icon-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  background: rgba(255,0,0,0.8);
  color: white;
  font-size: 10px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
}
```

```html+jinja title="usage"
{#import "icon-badge.jx" as IconBadge #}
{#import "icons/icon-bell.jx" as IconBell #}

<IconBadge count={{ notifications_count }}>
  <IconBell />
</IconBadge>
```

::: tab | Preview
<p class="preview">
<span class="icon-badge-wrapper">
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="24" height="24">
  <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
</svg>
<span class="icon-badge">42</span>
</span>
</p>
:::

## Tips

1. **Use `currentColor`** for fill/stroke to inherit text color
2. **Set sensible defaults** for size (24px is common)
3. **Add `aria-hidden="true"`** for decorative icons
4. **Use `aria-label`** on icon-only buttons
5. **Keep SVGs optimized** - remove unnecessary attributes

