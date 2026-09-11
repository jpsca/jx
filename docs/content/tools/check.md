---
title: Command line
description: Command-line tools for validating and inspecting Jx components
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
      "line": 2,
      "message": "Unknown import 'dialog.jx'",
      "suggestion": "dialogs/dialog.jx"
    }
  ]
}
```

Every error carries the line it happens on, and a syntax error also carries a
0-based `col`, so an editor can underline the exact spot.

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


## Inspecting a Catalog

`jx info` reports how a catalog is set up — where its component folders are,
what prefixes they have, and which file extension it uses:

```sh
$ jx info myapp.setup:catalog
```

```sh
file_ext: .jx
components: 12
folders:
  /srv/myapp/components
  /srv/myapp/ui (prefix: @ui/) [assets: /srv/myapp/ui/static]
```

```sh
$ jx info --format json myapp.setup:catalog
```

```json
{
  "file_ext": ".jx",
  "folders": [
    {"path": "/srv/myapp/components", "prefix": "", "assets": null},
    {"path": "/srv/myapp/ui", "prefix": "ui", "assets": "/srv/myapp/ui/static"}
  ],
  "components": ["@ui/modal.jx", "button.jx", "page.jx"]
}
```

This exists so a tool does not have to read your Python source to work out
where components live. However the folders were registered — a literal string,
a `Path`, `settings.BASE_DIR / "components"`, `add_package` — the catalog that
actually loaded them is the one answering.


## Inspecting a Component

`jx parse` reports a single component's structure: the imports in its header
and the component tags it uses, each with the offsets they occupy in the file.

```sh
$ jx parse components/page.jx --format text
```

```sh
import button.jx as Button
4: <Button>
```

No catalog is involved, so this works on any file, including one that belongs
to no project. Pass `--stdin` to parse an editor buffer that has not been
saved, using the path only as a name:

```sh
$ jx parse components/page.jx --stdin < buffer.txt
```

The default format is JSON:

```json
{
  "name": "components/page.jx",
  "imports": [
    {
      "name": "Button", "path": "button.jx", "start": 0,
      "path_start": 10, "path_end": 19,
      "name_start": 24, "name_end": 30
    }
  ],
  "tags": [{"name": "Button", "start": 78, "end": 99, "line": 4}],
  "errors": []
}
```

Two things are worth noting:

- The tags come from the parser, so a `<Button />` written inside a comment or
  a `{% raw %}` block is not reported — it is not a tag.
- A file whose body does not parse still reports the imports in its header,
  along with the error. A broken file is exactly when a tool still wants to
  know what it was importing.

The exit code is `1` when the file has an error, in either format.
