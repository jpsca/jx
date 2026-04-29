# Tools reference

## `jx check` validator

Beyond what the `Catalog` validates at render time, the `jx` CLI has a static checker that scans every component up-front. Use it locally and in CI.

```sh
jx check myapp.setup:catalog
jx check docs/docs.py:catalog
```

The argument is `module.path:attribute` or `path/to/file.py:attribute`. Jx imports the module/file and uses the named attribute as the `Catalog` instance.

### What it catches that the catalog doesn't

| Check | Description |
|---|---|
| Cross-component imports | `{#import "buton.jx" as Button #}` resolves to a real file in the catalog (the catalog only verifies imports lazily, at render time). |
| Used-but-not-imported tags | `<Button />` without an import — tells you which component you forgot to declare. |
| Typo suggestions | "did you mean 'button.jx'?" / "did you mean 'Button'?" |
| Whole-tree run | Reports every issue across every component, not just the first. |

### Output formats

**Text** (default):

```
✓ button.jx - OK
✓ card.jx - OK
✗ page.jx:12 - Component 'Buton' used but not imported (did you mean 'Button'?)
✗ modal.jx - Unknown import 'dialog.jx' (did you mean 'dialogs/dialog.jx'?)

4 components checked, 2 errors
```

**JSON** (for editor integrations):

```sh
jx check --format json myapp.setup:catalog
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
    }
  ]
}
```

### Programmatic API

```python
from jx import Catalog
from jx.tools import check, check_all

catalog = Catalog("components/")

errors, checked = check_all(catalog)
for error in errors:
    print(f"{error.file}:{error.line} - {error.message}")

# Or run a full check with formatted output:
exit_code = check(catalog, format="text")
```

`check_all` returns `(errors, checked_count)`. Useful in CI scripts where you want custom reporting; `check` does the formatting and returns an exit code suitable for `sys.exit()`.

### CI usage

```yaml
# .github/workflows/ci.yml (excerpt)
- name: Validate Jx components
  run: |
    uv run jx check myapp.setup:catalog
```

Non-zero exit on any error; pair with `--format json` if you want to post-process the output.

## VSCode extension

Install `jpscaletti.jinja-jx` (Quick Open: `Ctrl+P`, paste `ext install jpscaletti.jinja-jx`).

Repo: https://github.com/jpsca/jx-vscode

### Features

- **Syntax highlighting** for Jx pragmas (`{#import #}`, `{#def #}`, `{#css #}`, `{#js #}`), PascalCase component tags, Jinja expressions/statements/comments, and inherited HTML.
- **Go-to-Definition**: `Ctrl/Cmd+click` on an import path, an alias name, or a component tag (`<Card>` / `</Card>`) jumps to the file. Works with absolute, relative (`./`, `../`), and prefixed (`@ui/...`) imports.
- **Diagnostics**: runs `jx check` on save and on open. Errors show in the **Problems** panel and as red underlines, with "did you mean?" suggestions for typos.
- **Snippets**:

| Prefix | Expands to |
|---|---|
| `jximport` | `{#import "..." as ... #}` |
| `jxdef` | `{#def ... #}` |
| `jxcss` | `{#css ... #}` |
| `jxjs` | `{#js ... #}` |
| `jxslot` | `{% slot name %} ... {% endslot %}` |
| `jxfill` | `{% fill name %} ... {% endfill %}` |
| `jxcomp` | Full component scaffold (import, css, js, def) |

- **Formatting**: `Shift+Alt+F` delegates to VS Code's built-in HTML formatter. Your HTML formatting settings (indent, wrap) are respected.

### Auto-detection

The extension scans for `Catalog()` / `.add_folder()` calls in `.py` files to infer:

- Component folder paths (for go-to-definition).
- Catalog import path (for diagnostics — what to pass to `jx check`).

It re-runs the scan on `.py` create/change/delete. If it can't find a `Catalog()` call, it falls back to `.jx` files inside `views/`, `components/`, `templates/`.

### Configuration

All settings are optional.

| Setting | Default | Description |
|---|---|---|
| `jx.check.enabled` | `true` | Toggle diagnostics. |
| `jx.pythonPath` | `""` | Python interpreter. Auto-detects from the Python extension or `PATH` if empty. |
| `jx.catalogPath` | `""` | `myapp.setup:catalog` — overrides auto-detection. |

## Installable component packages

If you're shipping a Jx component library on PyPI, two pieces matter:

1. **Catalog setup at install site**:

   ```python
   catalog.add_folder(
       package_path / "components",
       prefix="my_lib",
       assets=package_path / "static",
   )
   ```

2. **Asset resolution**: the host application provides an `asset_resolver` callback (Catalog constructor) that turns the URLs declared inside your library into the host's static-file URLs. Then `catalog.collect_assets("static/")` copies your library's `static/` files into the host's static folder.

The `prefix` becomes the import namespace (`{#import "@my_lib/button.jx" as Button #}`) and the asset folder name (`/static/my_lib/button.css`).
