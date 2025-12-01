---
title: Form Components
description: Building reusable form inputs and validation
---

Forms benefit greatly from components - reduce repetition and ensure consistent styling and validation across your app.

## Basic Input

```html+jinja title="components/forms/input.jinja"
{#def name, label="", type="text", required=false, error="" #}

<div class="form-group">
  {% if label %}
    <label for="{{ name }}">
      {{ label }}
      {% if required %}<span class="required">*</span>{% endif %}
    </label>
  {% endif %}

  <input
    name="{{ name }}"
    id="{{ name }}"
    type="{{ type }}"
    {{ attrs.render(class="form-control" ~ (" is-invalid" if error else "")) }}
  />

  {% if error %}
    <span class="error-message">{{ error }}</span>
  {% endif %}
</div>
```

```html+jinja title="usage"
{#import "forms/input.jinja" as Input #}

<Input name="email" label="Email" type="email" required />
<Input name="password" label="Password" type="password" required />
<Input name="username" label="Username" error="Username is taken" />
```

## Textarea

```html+jinja title="components/forms/textarea.jinja"
{#def name, label="", required=false, rows=4, error="" #}

<div class="form-group">
  {% if label %}
    <label for="{{ name }}">
      {{ label }}
      {% if required %}<span class="required">*</span>{% endif %}
    </label>
  {% endif %}

  <textarea
    name="{{ name }}"
    id="{{ name }}"
    rows="{{ rows }}"
    {{ attrs.render(class="form-control" ~ (" is-invalid" if error else "")) }}
  >{{ content }}</textarea>

  {% if error %}
    <span class="error-message">{{ error }}</span>
  {% endif %}
</div>
```

```html+jinja title="usage"
<Textarea name="bio" label="Biography" rows={{ 6 }}>
  Default text here
</Textarea>
```

## Select

```html+jinja title="components/forms/select.jinja"
{#def name, label="", options=[], value="", required=false, placeholder="" #}

<div class="form-group">
  {% if label %}
    <label for="{{ name }}">
      {{ label }}
      {% if required %}<span class="required">*</span>{% endif %}
    </label>
  {% endif %}

  <select name="{{ name }}" id="{{ name }}" {{ attrs.render(class="form-control") }}>
    {% if placeholder %}
      <option value="" disabled {{ "selected" if not value else "" }}>
        {{ placeholder }}
      </option>
    {% endif %}

    {% for opt in options %}
      {% if opt is mapping %}
        <option value="{{ opt.value }}" {{ "selected" if opt.value == value else "" }}>
          {{ opt.label }}
        </option>
      {% else %}
        <option value="{{ opt }}" {{ "selected" if opt == value else "" }}>
          {{ opt }}
        </option>
      {% endif %}
    {% endfor %}
  </select>
</div>
```

```html+jinja title="usage"
{#import "forms/select.jinja" as Select #}

{# Simple list #}
<Select
  name="color"
  label="Favorite Color"
  options={{ ["Red", "Green", "Blue"] }}
  placeholder="Choose a color"
/>

{# Value/label pairs #}
<Select
  name="country"
  label="Country"
  options={{[
    {"value": "us", "label": "United States"},
    {"value": "uk", "label": "United Kingdom"},
    {"value": "ca", "label": "Canada"},
  ]}}
  value="uk"
/>
```

## Checkbox

```html+jinja title="components/forms/checkbox.jinja"
{#def name, label, checked=false, value="on" #}

<div class="form-check">
  <input
    type="checkbox"
    name="{{ name }}"
    id="{{ name }}"
    value="{{ value }}"
    {{ "checked" if checked else "" }}
    {{ attrs.render(class="form-check-input") }}
  />
  <label for="{{ name }}" class="form-check-label">
    {{ label }}
  </label>
</div>
```

```html+jinja title="usage"
<Checkbox name="terms" label="I agree to the terms" />
<Checkbox name="newsletter" label="Subscribe to newsletter" checked />
```

## Radio Group

```html+jinja title="components/forms/radio-group.jinja"
{#def name, label="", options=[], value="" #}

<fieldset class="form-group">
  {% if label %}
    <legend>{{ label }}</legend>
  {% endif %}

  {% for opt in options %}
    {% set opt_value = opt.value if opt is mapping else opt %}
    {% set opt_label = opt.label if opt is mapping else opt %}

    <div class="form-check">
      <input
        type="radio"
        name="{{ name }}"
        id="{{ name }}-{{ loop.index }}"
        value="{{ opt_value }}"
        {{ "checked" if opt_value == value else "" }}
        class="form-check-input"
      />
      <label for="{{ name }}-{{ loop.index }}" class="form-check-label">
        {{ opt_label }}
      </label>
    </div>
  {% endfor %}
</fieldset>
```

```html+jinja title="usage"
<RadioGroup
  name="plan"
  label="Select a plan"
  options={{[
    {"value": "free", "label": "Free - $0/mo"},
    {"value": "pro", "label": "Pro - $10/mo"},
    {"value": "enterprise", "label": "Enterprise - $50/mo"},
  ]}}
  value="pro"
/>
```

## Form Wrapper

```html+jinja title="components/forms/form.jinja"
{#def action="", method="post" #}

<form action="{{ action }}" method="{{ method }}" {{ attrs.render() }}>
  {{ content }}
</form>
```

```html+jinja title="usage"
{#import "forms/form.jinja" as Form #}
{#import "forms/input.jinja" as Input #}

<Form action="/register" class="register-form">
  <Input name="email" label="Email" type="email" required />
  <Input name="password" label="Password" type="password" required />
  <button type="submit">Register</button>
</Form>
```

## Complete Form Example

```html+jinja title="components/contact-form.jinja"
{#import "./forms/form.jinja" as Form #}
{#import "./forms/input.jinja" as Input #}
{#import "./forms/textarea.jinja" as Textarea #}
{#import "./forms/select.jinja" as Select #}
{#import "./forms/checkbox.jinja" as Checkbox #}
{#def errors={} #}

<Form action="/contact" class="contact-form">
  <Input
    name="name"
    label="Your Name"
    required
    error={{ errors.get("name", "") }}
  />

  <Input
    name="email"
    label="Email Address"
    type="email"
    required
    error={{ errors.get("email", "") }}
  />

  <Select
    name="subject"
    label="Subject"
    placeholder="What is this about?"
    options={{["General Inquiry", "Support", "Feedback", "Other"]}}
  />

  <Textarea
    name="message"
    label="Message"
    required
    rows={{ 6 }}
    error={{ errors.get("message", "") }}
  />

  <Checkbox name="copy" label="Send me a copy" />

  <button type="submit" class="btn btn-primary">Send Message</button>
</Form>
```

```python title="view"
@app.post("/contact")
def contact():
    errors = validate_contact_form(request.form)
    if errors:
        return catalog.render("contact-form.jinja", errors=errors)
    # Process form...
```

## Form with Server Errors

```html+jinja title="components/forms/field-errors.jinja"
{#def errors=[] #}

{% if errors %}
  <ul class="field-errors">
    {% for error in errors %}
      <li>{{ error }}</li>
    {% endfor %}
  </ul>
{% endif %}
```

```html+jinja title="usage"
{#import "forms/input.jinja" as Input #}
{#import "forms/field-errors.jinja" as FieldErrors #}

<div class="form-group">
  <Input name="email" label="Email" type="email" />
  <FieldErrors errors={{ form_errors.get("email", []) }} />
</div>
```
