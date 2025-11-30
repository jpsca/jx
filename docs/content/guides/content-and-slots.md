---
title: Content & Slots
description: Passing content to components and using named slots
---

One of the most powerful features of components is the ability to wrap content. This allows you to create flexible, composable layouts and UI patterns.

## The `content` Variable

Every component automatically has access to a `content` variable that contains everything between the opening and closing tags.

### Basic Example

```html+jinja title="components/card.jinja"
{#def title #}

<div class="card">
  <div class="card-header">
    <h3>{{ title }}</h3>
  </div>
  <div class="card-body">
    {{ content }}
  </div>
</div>
```

```html+jinja title="usage"
{#import "./card.jinja" as Card #}

<Card title="Welcome">
  <p>This is the card content!</p>
  <p>You can put anything here.</p>
</Card>
```

**Renders as:**

```html
<div class="card">
  <div class="card-header">
    <h3>Welcome</h3>
  </div>
  <div class="card-body">
    <p>This is the card content!</p>
    <p>You can put anything here.</p>
  </div>
</div>
```

## Self-Closing Components

Self-closing components have empty content:

```html+jinja
<Card title="Empty" />
```

The `content` variable will be an empty string.

## Fallback Content

You can provide default content when no content is passed:

```html+jinja
{#def title #}

<div class="card">
  <h3>{{ title }}</h3>
  <div class="body">
    {% if content %}
      {{ content }}
    {% else %}
      <p>No content provided.</p>
    {% endif %}
  </div>
</div>
```

Or more concisely:

```html+jinja
{#def title, default_text="No content" #}

<div class="card">
  <h3>{{ title }}</h3>
  <div class="body">
    {{ content or default_text }}
  </div>
</div>
```

## Nesting Components

Content can include other components:

```html+jinja
{#import "./card.jinja" as Card #}
{#import "./button.jinja" as Button #}

<Card title="Actions">
  <p>Choose an action:</p>
  <Button>Save</Button>
  <Button>Cancel</Button>
</Card>
```

## Named Slots

Sometimes you need more than one content area. Named slots let you pass multiple pieces of content to different locations in a component.

### Defining Slots

Use `{% slot name %}` to define named slots in your component:

```html+jinja title="components/modal.jinja"
<div class="modal">
  <div class="modal-header">
    {% slot header %}
      <h3>Default Header</h3>
    {% endslot %}
  </div>

  <div class="modal-body">
    {{ content }}
  </div>

  <div class="modal-footer">
    {% slot footer %}
      <button>Close</button>
    {% endslot %}
  </div>
</div>
```

The text between `{% slot header %}` and `{% endslot %}` is the **default content** shown when the slot isn't filled.

### Filling Slots

Use `{% fill name %}` to provide content for named slots:

```html+jinja title="usage"
{#import "./modal.jinja" as Modal #}

<Modal>
  {% fill header %}
    <h3>Confirm Action</h3>
    <button class="close">×</button>
  {% endfill %}

  <p>Are you sure you want to continue?</p>

  {% fill footer %}
    <button class="btn-primary">Confirm</button>
    <button class="btn-secondary">Cancel</button>
  {% endfill %}
</Modal>
```

**Renders as:**

```html
<div class="modal">
  <div class="modal-header">
    <h3>Confirm Action</h3>
    <button class="close">×</button>
  </div>

  <div class="modal-body">
    <p>Are you sure you want to continue?</p>
  </div>

  <div class="modal-footer">
    <button class="btn-primary">Confirm</button>
    <button class="btn-secondary">Cancel</button>
  </div>
</div>
```

## Slot Features

### Optional Slots

If you don't fill a slot, the default content is used:

```html+jinja
<Modal>
  <p>Just body content, no custom header or footer</p>
</Modal>
```

This uses the default header and footer from the component definition.

### Multiple Slots

You can have as many named slots as you need:

```html+jinja title="components/layout.jinja"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {% slot styles %}
    <link rel="stylesheet" href="/static/default.css">
  {% endslot %}
</head>
<body>
  <header>
    {% slot header %}
      <h1>{{ title }}</h1>
    {% endslot %}
  </header>

  <nav>
    {% slot navigation %}
      <a href="/">Home</a>
    {% endslot %}
  </nav>

  <main>
    {{ content }}
  </main>

  <footer>
    {% slot footer %}
      <p>&copy; 2024</p>
    {% endslot %}
  </footer>

  {% slot scripts %}{% endslot %}
</body>
</html>
```

### Slots Can Contain Components

Slot content can include other components:

```html+jinja
{#import "./layout.jinja" as Layout #}
{#import "./nav-link.jinja" as NavLink #}

<Layout title="My App">
  {% fill navigation %}
    <NavLink href="/">Home</NavLink>
    <NavLink href="/about">About</NavLink>
    <NavLink href="/contact">Contact</NavLink>
  {% endfill %}

  <h2>Welcome to my app!</h2>
</Layout>
```

### Empty Slots

Slots can have no default content:

```html+jinja
{% slot optional %}{% endslot %}
```

If not filled, nothing is rendered there.

## When to Use Slots vs Props

### Use Props When:
- The content is simple (text, numbers)
- There's a clear single value
- You want type safety or validation

```html+jinja
{#def title, count #}
<h2>{{ title }}: {{ count }}</h2>
```

### Use Content When:
- The content is HTML/components
- There's one main content area
- You want flexibility in what gets passed

```html+jinja
{#def title #}
<div class="card">
  <h2>{{ title }}</h2>
  {{ content }}
</div>
```

### Use Named Slots When:
- You need multiple content areas
- Each area has a specific purpose
- You want to provide defaults for each area

```html+jinja
<div class="panel">
  <header>{% slot header %}Default{% endslot %}</header>
  <main>{{ content }}</main>
  <footer>{% slot footer %}Default{% endslot %}</footer>
</div>
```

## Common Patterns

### Layout Component

```html+jinja title="components/page-layout.jinja"
{#def title #}

<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  {% slot head %}{% endslot %}
  {{ assets.render_css() }}
</head>
<body>
  <header>
    {% slot header %}
      <h1>{{ title }}</h1>
    {% endslot %}
  </header>

  <main>
    {{ content }}
  </main>

  <footer>
    {% slot footer %}
      <p>&copy; 2024 My Company</p>
    {% endslot %}
  </footer>

  {{ assets.render_js() }}
</body>
</html>
```

### Card with Optional Header/Footer

```html+jinja title="components/card.jinja"
<div {{ attrs.render(class="card") }}>
  {% slot header %}{% endslot %}

  <div class="card-body">
    {{ content }}
  </div>

  {% slot footer %}{% endslot %}
</div>
```

```html+jinja title="usage"
<Card>
  {% fill header %}<h3>Title</h3>{% endfill %}
  <p>Body content</p>
</Card>
```

### Tabs Component

```html+jinja title="components/tabs.jinja"
<div class="tabs">
  <div class="tab-headers">
    {% slot headers %}
      <button>Tab 1</button>
    {% endslot %}
  </div>

  <div class="tab-content">
    {{ content }}
  </div>
</div>
```

```html+jinja title="usage"
<Tabs>
  {% fill headers %}
    <button data-tab="home">Home</button>
    <button data-tab="profile">Profile</button>
    <button data-tab="settings">Settings</button>
  {% endfill %}

  <div id="home">Home content</div>
  <div id="profile">Profile content</div>
  <div id="settings">Settings content</div>
</Tabs>
```

### Alert with Optional Actions

```html+jinja title="components/alert.jinja"
{#def message, type="info" #}

<div class="alert alert-{{ type }}">
  <div class="alert-message">{{ message }}</div>

  {% slot actions %}{% endslot %}
</div>
```

```html+jinja title="usage"
<Alert message="File deleted successfully" type="success">
  {% fill actions %}
    <button>Undo</button>
  {% endfill %}
</Alert>

<Alert message="Something went wrong" type="error" />
```

## Composability Over Named Slots

For complex layouts, sometimes it's better to use **composition** (nested components) instead of many named slots:

### With Many Slots (can get messy)

```html+jinja
<Modal>
  {% fill icon %}<Icon name="warning" />{% endfill %}
  {% fill title %}Confirm{% endfill %}
  {% fill subtitle %}This action cannot be undone{% endfill %}
  {% fill actions %}
    <Button>OK</Button>
    <Button>Cancel</Button>
  {% endfill %}
  <p>Body content</p>
</Modal>
```

### With Composition (clearer)

```html+jinja
{#import "./modal.jinja" as Modal #}
{#import "./modal-header.jinja" as ModalHeader #}
{#import "./modal-body.jinja" as ModalBody #}
{#import "./modal-footer.jinja" as ModalFooter #}

<Modal>
  <ModalHeader
    icon="warning"
    title="Confirm"
    subtitle="This action cannot be undone"
  />
  <ModalBody>
    <p>Body content</p>
  </ModalBody>
  <ModalFooter>
    <Button>OK</Button>
    <Button>Cancel</Button>
  </ModalFooter>
</Modal>
```

Each sub-component is independent, testable, and can be used in other contexts.

## Best Practices

### 1. Provide Meaningful Defaults

```html+jinja
{# ✅ Good - useful default #}
{% slot footer %}
  <button type="submit">Submit</button>
{% endslot %}

{# ❌ Bad - unhelpful default #}
{% slot footer %}Footer{% endslot %}
```

### 2. Name Slots Clearly

```html+jinja
{# ✅ Good #}
{% slot header %}{% endslot %}
{% slot footer %}{% endslot %}
{% slot actions %}{% endslot %}

{# ❌ Bad #}
{% slot slot1 %}{% endslot %}
{% slot slot2 %}{% endslot %}
```

### 3. Don't Overuse Slots

If you have more than 3-4 slots, consider using composition:

```html+jinja
{# ❌ Too many slots #}
{% slot icon %}{% endslot %}
{% slot title %}{% endslot %}
{% slot subtitle %}{% endslot %}
{% slot badge %}{% endslot %}
{% slot actions %}{% endslot %}
{% slot footer %}{% endslot %}

{# ✅ Better - use sub-components #}
<CardHeader>...</CardHeader>
<CardBody>{{ content }}</CardBody>
<CardFooter>...</CardFooter>
```

### 4. Mix Content and Slots Naturally

The main content area should use `{{ content }}`, not a slot:

```html+jinja
{# ✅ Good #}
<div class="card">
  {% slot header %}{% endslot %}
  <div class="body">{{ content }}</div>
  {% slot footer %}{% endslot %}
</div>

{# ❌ Bad - don't make the main content a slot #}
<div class="card">
  {% slot header %}{% endslot %}
  {% slot body %}{% endslot %}
  {% slot footer %}{% endslot %}
</div>
```

## Next Steps

- **[Attrs](/guides/attrs)** - Learn about extra HTML attributes
- **[Assets](/guides/assets)** - Managing CSS and JavaScript
- **[Organization](/advanced/organization)** - Patterns for complex component structures
