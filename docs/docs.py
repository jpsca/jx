"""
# WriteaDoc Documentation

- `python docs.py run` to start a local server with live reload.
- `python docs.py build` to build the documentation for deployment.

"""
from pathlib import Path

from writeadoc import Docs


pages = [
    "quickstart.md",
    "catalog.md",
    "components.md",
    "attrs.md",
    "assets.md",
    {
        "title": "API",
        "pages": [
            "api/catalog.md",
            "api/attrs.md",
        ],
    },
    {
        "title": "Recipes",
        "pages": [
            "recipes/layouts.md",
            "recipes/icons.md",
        ],
    },
    {
        "title": "Working with",
        "pages": [
            ""
            "working/flask.md",
            "working/django.md",
            "working/fastapi.md",
            "working/htmx.md",
        ]
    },
    "installable.md",
    {
        "title": "Tools",
        "pages": [
            "tools/skill.md",
            "tools/check.md",
            "tools/vscode.md",
        ]
    },
    "from-jinjax.md",
]

pages_es = [
    "quickstart.md",
    "catalog.md",
    "components.md",
    "attrs.md",
    "assets.md",
    {
        "title": "API",
        "pages": [
            "api/catalog.md",
            "api/attrs.md",
        ],
    },
    {
        "title": "Recetas",
        "pages": [
            "recipes/layouts.md",
            "recipes/icons.md",
        ],
    },
    {
        "title": "Trabajando con",
        "pages": [
            ""
            "working/flask.md",
            "working/django.md",
            "working/fastapi.md",
            "working/htmx.md",
        ]
    },
    "installable.md",
    {
        "title": "Herramientas",
        "pages": [
            "tools/skill.md",
            "tools/check.md",
            "tools/vscode.md",
        ]
    },
    "from-jinjax.md",
]

docs_es = Docs(
    __file__,
    pages=pages_es,  # Relative to content/es/
    site={
        "name": "Jx",
        "description": "Python server-side components",
        "base_url": "https://jx.scaletti.dev",
        "lang": "es",
        "version": "0.11",
        "source_code": "https://github.com/jpsca/jx/",
    },
)

docs = Docs(
    __file__,
    pages=pages,
    variants={
      "es": docs_es,
    },
    site={
        "name": "Jx",
        "description": "Python server-side components",
        "base_url": "https://jx.scaletti.dev",
        "lang": "en",
        "version": "0.11",
        "source_code": "https://github.com/jpsca/jx/",
    },
)
docs.catalog.add_folder(Path(__file__).parent / "demos")

if __name__ == "__main__":
    docs.cli()
