---
title: Modal Components
description: Creating modal dialogs and overlays
---

Modals are perfect for components - encapsulate the structure, styles, and behavior in one place.

## Basic Modal

```html+jinja title="components/modal.jinja"
{#def id, title="" #}
{#css modal.css #}
{#js modal.js #}

<div class="modal" id="{{ id }}" {{ attrs.render() }}>
  <div class="modal-backdrop" data-modal-close></div>
  <div class="modal-content">
    {% if title %}
      <div class="modal-header">
        <h2>{{ title }}</h2>
        <button type="button" class="modal-close" data-modal-close>&times;</button>
      </div>
    {% endif %}

    <div class="modal-body">
      {{ content }}
    </div>

    {% slot footer %}{% endslot %}
  </div>
</div>
```

```css title="modal.css"
.modal {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 1000;
}

.modal.is-open {
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 8px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}
```

```javascript title="modal.js"
// Simple modal toggle
document.addEventListener('click', (e) => {
  // Open modal
  if (e.target.matches('[data-modal-open]')) {
    const id = e.target.dataset.modalOpen;
    document.getElementById(id)?.classList.add('is-open');
  }

  // Close modal
  if (e.target.matches('[data-modal-close]')) {
    e.target.closest('.modal')?.classList.remove('is-open');
  }
});
```

```html+jinja title="usage"
{#import "modal.jinja" as Modal #}

<button data-modal-open="confirm-modal">Open Modal</button>

<Modal id="confirm-modal" title="Confirm Action">
  <p>Are you sure you want to continue?</p>

  {% fill footer %}
    <div class="modal-footer">
      <button data-modal-close>Cancel</button>
      <button class="btn-primary">Confirm</button>
    </div>
  {% endfill %}
</Modal>
```

## Modal with Slots

```html+jinja title="components/modal.jinja"
{#def id #}
{#css modal.css #}

<div class="modal" id="{{ id }}">
  <div class="modal-backdrop" data-modal-close></div>
  <div class="modal-content" {{ attrs.render() }}>
    <div class="modal-header">
      {% slot header %}
        <h2>Modal</h2>
      {% endslot %}
      <button type="button" class="modal-close" data-modal-close>&times;</button>
    </div>

    <div class="modal-body">
      {{ content }}
    </div>

    <div class="modal-footer">
      {% slot footer %}
        <button data-modal-close>Close</button>
      {% endslot %}
    </div>
  </div>
</div>
```

```html+jinja title="usage"
<Modal id="edit-user" class="modal-lg">
  {% fill header %}
    <h2>Edit User</h2>
    <span class="badge">Admin</span>
  {% endfill %}

  <form>
    <Input name="name" label="Name" />
    <Input name="email" label="Email" />
  </form>

  {% fill footer %}
    <button data-modal-close>Cancel</button>
    <button type="submit" class="btn-primary">Save Changes</button>
  {% endfill %}
</Modal>
```

## Confirmation Modal

A specialized modal for confirmations:

```html+jinja title="components/confirm-modal.jinja"
{#import "./modal.jinja" as Modal #}
{#def id, title="Confirm", message, confirm_text="Confirm", cancel_text="Cancel", variant="primary" #}

<Modal id={{ id }} title={{ title }}>
  <p>{{ message }}</p>

  {% fill footer %}
    <div class="modal-footer">
      <button data-modal-close class="btn btn-secondary">
        {{ cancel_text }}
      </button>
      <button class="btn btn-{{ variant }}" {{ attrs.render() }}>
        {{ confirm_text }}
      </button>
    </div>
  {% endfill %}
</Modal>
```

```html+jinja title="usage"
{#import "confirm-modal.jinja" as ConfirmModal #}

<button data-modal-open="delete-modal">Delete Item</button>

<ConfirmModal
  id="delete-modal"
  title="Delete Item"
  message="This action cannot be undone. Are you sure?"
  confirm_text="Delete"
  variant="danger"
  data-action="delete"
/>
```

## Alert Modal

```html+jinja title="components/alert-modal.jinja"
{#import "./modal.jinja" as Modal #}
{#def id, title, type="info" #}

<Modal id={{ id }} class="alert-modal alert-{{ type }}">
  {% fill header %}
    <div class="alert-icon">
      {% if type == "success" %}✓{% endif %}
      {% if type == "error" %}✕{% endif %}
      {% if type == "warning" %}⚠{% endif %}
      {% if type == "info" %}ℹ{% endif %}
    </div>
    <h2>{{ title }}</h2>
  {% endfill %}

  {{ content }}

  {% fill footer %}
    <button data-modal-close class="btn btn-{{ type }}">OK</button>
  {% endfill %}
</Modal>
```

```html+jinja title="usage"
<AlertModal id="success-modal" title="Success!" type="success">
  <p>Your changes have been saved.</p>
</AlertModal>

<AlertModal id="error-modal" title="Error" type="error">
  <p>Something went wrong. Please try again.</p>
</AlertModal>
```

## Form Modal

```html+jinja title="components/form-modal.jinja"
{#import "./modal.jinja" as Modal #}
{#def id, title, action, method="post" #}

<Modal id={{ id }} title={{ title }}>
  <form action="{{ action }}" method="{{ method }}">
    {{ content }}

    {% fill footer %}
      <div class="modal-footer">
        <button type="button" data-modal-close class="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          Submit
        </button>
      </div>
    {% endfill %}
  </form>
</Modal>
```

```html+jinja title="usage"
{#import "form-modal.jinja" as FormModal #}
{#import "forms/input.jinja" as Input #}

<FormModal id="create-user" title="Create User" action="/users">
  <Input name="name" label="Name" required />
  <Input name="email" label="Email" type="email" required />
</FormModal>
```
