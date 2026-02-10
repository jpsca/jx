---
title: Quickstart
---

## Install Jx

Run the following command:

::: tab | Using "**pip**"

```bash
pip install jx
```

:::

::: tab | Using "**uv**"

```bash
uv add jx
```

:::

## Create a catalog

```python {title="app.py"}
from jx import Catalog

catalog = Catalog("components/")
```

## Create a component

Create a new folder for your components. Inside this folder create a new file called `card.jinja` with the following content:

```html+jinja {title="components/card.jinja"}
{#def title, url #}

<div class="bg-white shadow rounded border p-4">
  <h2 class="m-0 text-gray-800">{{ title }}</h2>
  <p>{{ content }}</p>
  <a href="{{ url_for(url) }}" class="text-teal-600">Read more</a>
</div>
```

## Use the component

```python {title="views.py"}
from .app import catalog

def dashboard_view():
    return catalog.render("dashboard.jinja")
```

```html+jinja {title="components/dashboard.jinja"}
{#import "card.jinja" as Card #}

<Card title="Trees" url="trees">
  We have the best trees
</Card>

<Card title="Spades" url="spades">
  The best spades in the land
</Card>
```

::: tab | Preview
<div class="demo">
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Trees</h2>
  <p>We have the best trees</p>
  <a href="/trees" class="text-teal-600">Read more</a>
</div>
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Spades</h2>
  <p>The best spades in the land</p>
  <a href="/spades" class="text-teal-600">Read more</a>
</div>
</div>
:::

::: tab | HTML

```html
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Trees</h2>
  <p>We have the best trees</p>
  <a href="/trees" class="text-teal-600">Read more</a>
</div>
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Spades</h2>
  <p>The best spades in the land</p>
  <a href="/spades" class="text-teal-600">Read more</a>
</div>
```

:::


## VisualStudio Code extension

If you are using VisualStudio Code, install the [Jinja-Jx extension](https://github.com/jpsca/jx-vscode).

![Jinja-Jx extension](/assets/images/jinja-jx.png)

This extension offers:

- Syntax highlighting of Jx-specific constructs like `import`, `def`, `css`, `js`, etc. and PascalCase component tags (e.g., `<MyComponent>`)
- Add go-to-definition from import paths and component tags to jump to the component file
- Check for syntax errors and validate import paths on save
