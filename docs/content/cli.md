---
title: Validator tool
description: Command-line tools for validating Jx components
---

Jx includes a command-line tool for validating your components. This helps catch errors early, and can be especially useful in CI pipelines.

### `jx check`

Validate components in one or more folders:

```sh
$ jx check components/
```

Check multiple folders:

```sh
$ jx check components/ layouts/ pages/
```

## What It Checks

The `check` command validates each `.jinja` file for:

1. **Valid UTF-8** — Files must be valid UTF-8 encoded
2. **Metadata syntax** — `{#def ...#}` and `{#import ...#}` declarations must parse correctly
3. **Import paths** — All imported components must exist in the catalog
4. **Component usage** — Every `<PascalCase>` tag must be imported
5. **Template syntax** — Catches unclosed tags, unmatched braces, and other parse errors

## Output Formats

### Text (default)

```sh
$ jx check components/
```

```sh
✓ button.jinja - OK
✓ card.jinja - OK
✗ page.jinja:12 - Component 'Buton' used but not imported (did you mean 'Button'?)
✗ modal.jinja - Unknown import 'dialog.jinja' (did you mean 'dialogs/dialog.jinja'?)

4 components checked, 2 errors
````

### JSON

```sh
$ jx check --format json components/
```

```json
{
  "checked": 4,
  "errors": [
    {
      "file": "page.jinja",
      "line": 12,
      "message": "Component 'Buton' used but not imported",
      "suggestion": "Button"
    },
    {
      "file": "modal.jinja",
      "line": null,
      "message": "Unknown import 'dialog.jinja'",
      "suggestion": "dialogs/dialog.jinja"
    }
  ]
}
```

JSON output is useful for integrating with editors, linters, or custom tooling.
