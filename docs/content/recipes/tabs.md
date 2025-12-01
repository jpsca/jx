---
title: Tabs
description: Building tabbed interfaces
---

Tabs are a common UI pattern that benefit from component encapsulation.

## Basic Tabs

```html+jinja title="components/tabs/tabs.jinja"
{#def active="" #}
{#css tabs.css #}
{#js tabs.js #}

<div class="tabs" data-tabs {{ attrs.render() }}>
  {{ content }}
</div>
```

```html+jinja title="components/tabs/tab-list.jinja"
<div class="tab-list" role="tablist">
  {{ content }}
</div>
```

```html+jinja title="components/tabs/tab.jinja"
{#def id, active=false #}

<button
  role="tab"
  data-tab="{{ id }}"
  aria-selected="{{ 'true' if active else 'false' }}"
  {{ attrs.render(class="tab" ~ (" active" if active else "")) }}
>
  {{ content }}
</button>
```

```html+jinja title="components/tabs/tab-panels.jinja"
<div class="tab-panels">
  {{ content }}
</div>
```

```html+jinja title="components/tabs/tab-panel.jinja"
{#def id, active=false #}

<div
  role="tabpanel"
  id="panel-{{ id }}"
  data-panel="{{ id }}"
  {{ attrs.render(class="tab-panel" ~ (" active" if active else "")) }}
  {% if not active %}hidden{% endif %}
>
  {{ content }}
</div>
```

```javascript title="tabs.js"
document.addEventListener('click', (e) => {
  const tab = e.target.closest('[data-tab]');
  if (!tab) return;

  const tabs = tab.closest('[data-tabs]');
  const tabId = tab.dataset.tab;

  // Update tab buttons
  tabs.querySelectorAll('[data-tab]').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabId);
    t.setAttribute('aria-selected', t.dataset.tab === tabId);
  });

  // Update panels
  tabs.querySelectorAll('[data-panel]').forEach(p => {
    const isActive = p.dataset.panel === tabId;
    p.classList.toggle('active', isActive);
    p.hidden = !isActive;
  });
});
```

```html+jinja title="usage"
{#import "tabs/tabs.jinja" as Tabs #}
{#import "tabs/tab-list.jinja" as TabList #}
{#import "tabs/tab.jinja" as Tab #}
{#import "tabs/tab-panels.jinja" as TabPanels #}
{#import "tabs/tab-panel.jinja" as TabPanel #}

<Tabs>
  <TabList>
    <Tab id="overview" active>Overview</Tab>
    <Tab id="features">Features</Tab>
    <Tab id="pricing">Pricing</Tab>
  </TabList>

  <TabPanels>
    <TabPanel id="overview" active>
      <h2>Overview</h2>
      <p>This is the overview content.</p>
    </TabPanel>

    <TabPanel id="features">
      <h2>Features</h2>
      <p>Feature list goes here.</p>
    </TabPanel>

    <TabPanel id="pricing">
      <h2>Pricing</h2>
      <p>Pricing information.</p>
    </TabPanel>
  </TabPanels>
</Tabs>
```

## Vertical Tabs

```html+jinja title="components/tabs/vertical-tabs.jinja"
{#css vertical-tabs.css #}
{#js tabs.js #}

<div class="tabs tabs-vertical" data-tabs {{ attrs.render() }}>
  {{ content }}
</div>
```

```css title="vertical-tabs.css"
.tabs-vertical {
  display: flex;
}

.tabs-vertical .tab-list {
  flex-direction: column;
  border-right: 1px solid #ddd;
  border-bottom: none;
}

.tabs-vertical .tab-panels {
  flex: 1;
  padding-left: 1rem;
}
```

## Simple Tabs Component

A higher-level component that takes data:

```html+jinja title="components/simple-tabs.jinja"
{#def tabs, active="" #}
{#css tabs.css #}
{#js tabs.js #}

{% set first_id = tabs[0].id if tabs else "" %}
{% set active_id = active or first_id %}

<div class="tabs" data-tabs>
  <div class="tab-list" role="tablist">
    {% for tab in tabs %}
      <button
        role="tab"
        data-tab="{{ tab.id }}"
        class="tab {{ 'active' if tab.id == active_id else '' }}"
        aria-selected="{{ 'true' if tab.id == active_id else 'false' }}"
      >
        {{ tab.label }}
      </button>
    {% endfor %}
  </div>

  <div class="tab-panels">
    {% for tab in tabs %}
      <div
        role="tabpanel"
        data-panel="{{ tab.id }}"
        class="tab-panel {{ 'active' if tab.id == active_id else '' }}"
        {{ "" if tab.id == active_id else "hidden" }}
      >
        {{ tab.content }}
      </div>
    {% endfor %}
  </div>
</div>
```

```html+jinja title="usage"
{#import "simple-tabs.jinja" as SimpleTabs #}

<SimpleTabs tabs={{[
  {"id": "tab1", "label": "First", "content": "<p>First tab content</p>"},
  {"id": "tab2", "label": "Second", "content": "<p>Second tab content</p>"},
  {"id": "tab3", "label": "Third", "content": "<p>Third tab content</p>"},
]}} />
```
