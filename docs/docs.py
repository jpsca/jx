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
            # "recipes/modals.md",
            # "recipes/tabs.md",
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
            "working/alpinejs.md",
        ]
    },
    "cli.md",
    "installable.md",
    "from-jinjax.md",
]

docs = Docs(
    __file__,
    pages=pages,
    site={
        "name": "Jx",
        "description": "Python server-side components",
        "base_url": "https://jx.scaletti.dev",
        "lang": "en",
        "version": "1.0",
        "source_code": "https://github.com/jpsca/jx/",
    },
)
docs.catalog.add_folder(Path(__file__).parent / "demos")

if __name__ == "__main__":
    docs.cli()
