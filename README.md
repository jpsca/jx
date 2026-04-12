<div align="center">
  <h1><img alt="Jx" src="https://raw.githubusercontent.com/jpsca/jx/main/docs/assets/images/logo-jx.png" height="100" align="top"></h1>
</div>
<p align="center">
  <img alt="python: 3.12, 3.13, 3.14" src="https://raw.githubusercontent.com/jpsca/jx/main/docs/python.svg">
  <img alt="license: MIT" src="https://raw.githubusercontent.com/jpsca/jx/main/docs/license.svg">
</p>

### Python server-side components

From chaos to clarity: The power of components in your server-side-rendered Python web app.

<!-- Documentation: https://jx.scaletti.dev/ -->

## How It Works

Jx is a Python library for creating reusable template components with Jinja2. It works by pre-parsing the template source and replacing TitleCased HTML tags with Jinja calls that render the component.

### Component Definition

Components are defined as regular Jinja2 templates (.jx files) with special metadata comments:

- `{# def parameter1 parameter2=default_value #}` - Defines required and optional parameters
- `{# import "path/to/component.jx" as ComponentName #}` - Imports other components
- `{# css "/path/to/style.css" #}` - Includes CSS files
- `{# js "/path/to/script.js" #}` - Includes JavaScript files

Example component:

```jinja
{# def message #}
{# import "button.jx" as Button #}

<div class="greeting">{{ message }}</div>
<Button text="OK" />
```

### Usage Example

```python
from jx import Catalog

# Create a catalog and add a components folder
catalog = Catalog("templates/components")

# Render a component with parameters
html = catalog.render("card.jx", title="Hello", content="This is a card")
```

## VisualStudio Code extension

If you are using VisualStudio Code, install the [Jinja-Jx extension](https://github.com/jpsca/jx-vscode).

![Jinja-Jx extension](https://raw.githubusercontent.com/jpsca/jx-vscode/main/demo.png)

This extension offers:

- Syntax highlighting of Jx-specific constructs like `import`, `def`, `css`, `js`, etc. and PascalCase component tags (e.g., `<MyComponent>`)
- Add go-to-definition from import paths and component tags to jump to the component file
- Check for syntax errors and validate import paths on save
