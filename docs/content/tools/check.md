---
title: Validator
description: Command-line tools for validating Jx components
---

Jx includes a command-line tool for validating your components. This helps catch errors early, and can be especially useful in CI pipelines.

Point the checker at your catalog instance using its Python import path. The format is `module.path:attribute` — the module is imported and the attribute is used as the `Catalog` instance.

```sh
$ jx check myapp.setup:catalog
```

You can also use `path/to/file.py:attribute` — the file is imported and the attribute is used as the `Catalog` instance.

```sh
$ jx check docs/docs.py:catalog
```


## What It Checks

The `check` command goes beyond the validation the catalog does when loading components:

1. **Cross-component validation** — verifies that import paths (e.g. `{#import "buton.jx" ...}`) actually resolve to components in the catalog. The catalog only verifies imports exist at render time.
2. **Unimported tag detection** — finds PascalCase tags like `<Button />` that aren't imported but exist in the catalog ("used but not imported").
3. **Suggestions** — "did you mean 'button.jx'?" / "did you mean 'Button'?" for typos.
4. **Collects all errors** — check reports every issue across every component.
5. **Structured JSON output** — for IDE integration (the VS Code extension uses this).


## Output Formats

### Text (default)

```sh
$ jx check myapp.setup:catalog
```

```sh
✓ button.jx - OK
✓ card.jx - OK
✗ page.jx:12 - Component 'Buton' used but not imported (did you mean 'Button'?)
✗ modal.jx - Unknown import 'dialog.jx' (did you mean 'dialogs/dialog.jx'?)

4 components checked, 2 errors
```

### JSON

```sh
$ jx check --format json myapp.setup:catalog
```

```json
{
  "checked": 4,
  "errors": [
    {
      "file": "page.jx",
      "abs_path": "/path/to/components/page.jx",
      "line": 12,
      "message": "Component 'Buton' used but not imported",
      "suggestion": "Button"
    },
    {
      "file": "modal.jx",
      "abs_path": "/path/to/components/modal.jx",
      "line": null,
      "message": "Unknown import 'dialog.jx'",
      "suggestion": "dialogs/dialog.jx"
    }
  ]
}
```

JSON output is useful for integrating with editors, linters, or custom tooling.

## Programmatic Use

You can also use the checker from Python code:

```python
from jx import Catalog
from jx.tools import check, check_all

catalog = Catalog("components/")

# Get structured errors
errors, checked = check_all(catalog)
for error in errors:
    print(f"{error.file}:{error.line} - {error.message}")

# Or run the full check with formatted output (returns exit code)
exit_code = check(catalog, format="text")
```
