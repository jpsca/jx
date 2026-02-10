# Jx

Jx is a Python component library for Jinja2 templates. It adds custom syntax on top of standard HTML+Jinja2.

## Syntax

- `{#def arg1, arg2="default" #}` — component parameter definitions
- `{#import "path" as ComponentName #}` — component imports
- `{#css file.css #}` / `{#js file.js #}` — asset declarations
- `<PascalCase>` — component tags (pattern: `[A-Z][0-9A-Za-z_.:$-]*`)
- `{% slot name %}` / `{% endslot %}` — slot definitions
- `{% fill name %}` / `{% endfill %}` — slot fills

## Key modules

- `src/jx/parser.py` — Template parser. `JxParser` replaces PascalCase tags with Jinja2 `{% call %}` blocks. `RX_TAG_NAME = r"[A-Z][0-9A-Za-z_.:$-]*"` (line 21).
- `src/jx/meta.py` — Metadata extraction from `{# ... #}` headers. `RX_IMPORT` (line 35) parses import declarations.
- `src/jx/catalog.py` — Component registry. `add_folder()` discovers `*.jinja` files recursively.
- `src/jx/cli.py` — CLI tool. `jx check [--format json|text] <paths>` validates components. `CheckError` dataclass for structured errors. `check_all()` returns `(list[CheckError], checked_count)`.
- `src/jx/component.py` — Component rendering.
- `src/jx/exceptions.py` — 10 exception classes inheriting from `JxException`.

## Commands

- `python -m pytest` — run tests (152 tests)
- `python -m pytest tests/test_cli.py --cov=jx.cli --cov-report=term-missing` — CLI coverage
- `jx check <paths>` — validate components (text output)
- `jx check --format json <paths>` — validate components (JSON output)

## Testing

- Tests are in `tests/`. Components are created inline via `tmp_path` fixtures (no `.jinja` fixture files).
- `conftest.py` provides a `folder` fixture (tmp_path subdirectory).
- CLI tests use `capsys` to capture stdout.
