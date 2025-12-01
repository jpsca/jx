---
title: SVG Icons
description: Using components for SVG icons
---

Components are perfect for SVG icons - encapsulate the SVG code once, reuse it everywhere with customizable size and color.

## Basic Icon Component

```html+jinja title="components/icons/icon-check.jinja"
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
{#import "icons/icon-check.jinja" as IconCheck #}

<IconCheck />
<IconCheck size={{ 32 }} />
<IconCheck size={{ 16 }} class="text-green" />
```

## Generic Icon Wrapper

Create a base component that other icons extend:

```html+jinja title="components/icons/icon.jinja"
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

```html+jinja title="components/icons/icon-x.jinja"
{#import "./icon.jinja" as Icon #}
{#def size=24 #}

<Icon size={{ size }} {{ attrs.render() }}>
  <line x1="18" y1="6" x2="6" y2="18"></line>
  <line x1="6" y1="6" x2="18" y2="18"></line>
</Icon>
```

```html+jinja title="components/icons/icon-menu.jinja"
{#import "./icon.jinja" as Icon #}
{#def size=24 #}

<Icon size={{ size }} {{ attrs.render() }}>
  <line x1="3" y1="12" x2="21" y2="12"></line>
  <line x1="3" y1="6" x2="21" y2="6"></line>
  <line x1="3" y1="18" x2="21" y2="18"></line>
</Icon>
```

## Dynamic Icon Component

Load icons by name:

```html+jinja title="components/icon.jinja"
{#def name, size=24 #}

{% set icons = {
  "check": '<polyline points="20 6 9 17 4 12"></polyline>',
  "x": '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>',
  "menu": '<line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line>',
  "search": '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
  "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>',
  "settings": '<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>',
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
{#import "icon.jinja" as Icon #}

<Icon name="check" />
<Icon name="x" size={{ 16 }} />
<Icon name="menu" class="text-gray-600" />
```

## Icon Button

Combine icons with buttons:

```html+jinja title="components/icon-button.jinja"
{#def label="" #}
{#css icon-button.css #}

<button
  {{ attrs.render(class="icon-button") }}
  {% if label %}aria-label="{{ label }}"{% endif %}
>
  {{ content }}
</button>
```

```html+jinja title="usage"
{#import "icon-button.jinja" as IconButton #}
{#import "icons/icon-x.jinja" as IconX #}

<IconButton label="Close" @click="close()">
  <IconX size={{ 20 }} />
</IconButton>
```

## Button with Icon and Text

```html+jinja title="components/button.jinja"
{#def text="" #}
{#css button.css #}

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
{#import "button.jinja" as Button #}
{#import "icons/icon-check.jinja" as IconCheck #}

<Button text="Save">
  {% fill icon %}
    <IconCheck size={{ 18 }} />
  {% endfill %}
</Button>
```

## Filled vs Stroke Icons

```html+jinja title="components/icons/icon-heart.jinja"
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

## Spinner Icon

```html+jinja title="components/icons/icon-spinner.jinja"
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

## Icon with Badge

```html+jinja title="components/icon-badge.jinja"
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
  top: -8px;
  right: -8px;
  background: red;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
}
```

```html+jinja title="usage"
{#import "icon-badge.jinja" as IconBadge #}
{#import "icons/icon-bell.jinja" as IconBell #}

<IconBadge count={{ notifications_count }}>
  <IconBell />
</IconBadge>
```

## Organizing Icons

Recommended folder structure:

```
components/
  icons/
    icon.jinja           # Base wrapper (optional)
    icon-check.jinja
    icon-x.jinja
    icon-menu.jinja
    icon-search.jinja
    icon-user.jinja
    icon-settings.jinja
    icon-heart.jinja
    icon-spinner.jinja
    ...
```

## Icon Sprite Alternative

For many icons, consider an SVG sprite:

```html+jinja title="components/sprite-icon.jinja"
{#def name, size=24 #}

<svg
  width="{{ size }}"
  height="{{ size }}"
  {{ attrs.render(class="icon icon-" ~ name) }}
>
  <use href="/static/icons.svg#{{ name }}"></use>
</svg>
```

```html+jinja title="usage"
{#import "sprite-icon.jinja" as Icon #}

<Icon name="check" />
<Icon name="x" size={{ 16 }} />
```

This loads icons from a single sprite file, reducing HTTP requests.

## Tips

1. **Use `currentColor`** for fill/stroke to inherit text color
2. **Set sensible defaults** for size (24px is common)
3. **Add `aria-hidden="true"`** for decorative icons
4. **Use `aria-label`** on icon-only buttons
5. **Keep SVGs optimized** - remove unnecessary attributes
6. **Consider a sprite** for apps with many icons
