---
title: VSCode extension
description: VisualStudio Code extension for working with Jx components
---

If you are using VisualStudio Code, install the [Jinja-Jx extension](https://github.com/jpsca/jx-vscode){_target="blank"}.


## Syntax Highlighting

The extension provides full syntax highlighting for `.jinja` files, including:

- Jx pragmas: `{#import ... #}`, `{#def ... #}`, `{#css ... #}`, `{#js ... #}`
- PascalCase component tags (e.g., `<MyComponent>`, `<Card />`)
- Jinja2 expressions (`{{ ... }}`), statements (`{% ... %}`), and comments (`{# ... #}`)
- Standard HTML (inherited from VS Code's built-in HTML grammar)

![Jinja-Jx extension](/assets/images/vscode.png)


## Go-to-Definition

<kbd>Ctrl</kbd>+click (or <kbd>Cmd</kbd>+click on macOS) to jump to a component file. This works from three places:

- **The import path** — click on the string in `{#import "card.jinja" as Card #}`
- **The alias name** — click on `Card` in the import declaration
- **A component tag** — click on `<Card>` or `</Card>` anywhere in the template

The extension resolves paths using your catalog folders (auto-detected from Python files), relative paths (`./`, `../`), and prefixed paths (`@ui/modal.jinja`).


## Diagnostics

The extension runs `jx check` automatically and shows errors inline in the editor. Checks run:

- On save (`.jinja` and `.py` files)
- When a `.jinja` file is opened
- On startup

![Jinja-Jx extension](/assets/images/vscode-didyoumeant.png)

Errors appear in the **Problems** panel and as red underlines in the editor, including "did you mean?" suggestions for typos.

This uses the same checker as the [CLI validator](check.md) — see that page for details on what gets checked.


## Snippets

Type a prefix and press <kbd>Tab</kbd> to expand:

Prefix     | Expands to
---------- | -----------------------------
`jximport` | `{#import "..." as ... #}`
`jxdef`    | `{#def ... #}`
`jxcss`    | `{#css ... #}`
`jxjs`     | `{#js ... #}`
`jxslot`   | `{% slot name %} ... {% endslot %}`
`jxfill`   | `{% fill name %} ... {% endfill %}`
`jxcomp`   | Full component scaffold (import, css, js, def)


## Formatting

The extension provides document formatting (<kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>F</kbd>) by delegating to VS Code's built-in HTML formatter. Your HTML formatting settings (indentation, wrapping, etc.) are respected.


## Auto-Detection

The extension automatically scans your workspace for Python files that use `Catalog()` or `.add_folder()` to detect:

- Component folder paths (used by go-to-definition)
- Catalog import paths (used by diagnostics)

If no `Catalog()` call is found, it falls back to looking for `.jinja` files inside well-known folder names (`views`, `components`, `templates`).

The scan re-runs whenever a `.py` file is created, changed, or deleted.


## Installation

Launch VSCode Quick Open (<kbd>Ctrl</kbd>+<kbd>P</kbd>), paste the following command, and press ENTER.

```bash
ext install jpscaletti.jinja-jx
```

Alternatively:

1. Download the the `jinja-jx-VERSION.vsix` file from the [GitHub repo](https://github.com/jpsca/jx-vscode){_target="blank"}
2. Launch VSCode Quick Command (<kbd>Shift</kbd>+<kbd>Ctrl</kbd>+<kbd>P</kbd>)
3. Run "Extensions: Install from VSIX..."


## Configuration

All settings are optional — the extension works out of the box with auto-detection.

Setting            | Default | Description
------------------ | ------- | ----------------------
`jx.check.enabled` | `true`  | Enable or disable diagnostics
`jx.pythonPath`    | `""`    | Path to the Python interpreter. Auto-detects from the Python extension or `PATH` if empty
`jx.catalogPath`   | `""`    | Import path to your Catalog instance (e.g. `myapp.setup:catalog`). Auto-detects if empty
