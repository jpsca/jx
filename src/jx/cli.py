"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path

from .tools import check


def _is_file_path(module_path: str) -> bool:
    return "/" in module_path or module_path.endswith(".py")


def _load_module_from_file(file_path: str):
    path = Path(file_path).resolve()
    if not path.exists():
        print(f"File not found: '{file_path}'")
        sys.exit(1)

    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_catalog(catalog_path: str):
    """
    Load a Catalog instance from a Python import path or file path.

    Accepted formats:
        module.path:attr          — e.g. "myapp.setup:catalog"
        module.path:attr.nested   — e.g. "docs.docs:docs.catalog"
        path/to/file.py:attr      — e.g. "docs/docs.py:docs.catalog"
    """
    if ":" not in catalog_path:
        print(f"Invalid catalog path '{catalog_path}'. Expected format: 'module.path:attribute' or 'path/to/file.py:attribute'")
        sys.exit(1)

    module_path, attr_path = catalog_path.rsplit(":", 1)

    if _is_file_path(module_path):
        module = _load_module_from_file(module_path)
    else:
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as err:
            print(f"Could not import module '{module_path}': {err}")
            sys.exit(1)

    obj = module
    for attr_name in attr_path.split("."):
        obj = getattr(obj, attr_name, None)
        if obj is None:
            print(f"Could not resolve '{attr_path}' in module '{module_path}'")
            sys.exit(1)

    return obj


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jx",
        description="Jx component tools",
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Validate components")
    check_parser.add_argument(
        "catalog",
        help="Path to the Catalog instance (e.g. 'myapp.setup:catalog' or 'path/to/file.py:catalog')",
    )
    check_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    collect_parser = subparsers.add_parser("collect_assets", help="Copy package assets to an output folder")
    collect_parser.add_argument(
        "catalog",
        help="Path to the Catalog instance (e.g. 'myapp.setup:catalog' or 'path/to/file.py:catalog')",
    )
    collect_parser.add_argument(
        "output",
        help="Destination folder for collected assets",
    )

    args = parser.parse_args()

    if args.command == "check":
        catalog = load_catalog(args.catalog)
        sys.exit(check(catalog, format=args.format))
    elif args.command == "collect_assets":
        catalog = load_catalog(args.catalog)
        collected = catalog.collect_assets(args.output)
        for prefix, rel in collected:
            print(f"  {prefix}/{rel}" if prefix else f"  {rel}")
        print(f"\n{len(collected)} file{'s' if len(collected) != 1 else ''} collected")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
