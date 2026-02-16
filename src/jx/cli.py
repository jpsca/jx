"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import argparse
import importlib
import sys

from .tools import check


def load_catalog(catalog_path: str):
    """
    Load a Catalog instance from a Python import path.

    The path format is "module.path:attr" or "module.path:attr.nested",
    e.g. "myapp.setup:catalog" or "docs.docs:docs.catalog".
    """
    if ":" not in catalog_path:
        print(f"Invalid catalog path '{catalog_path}'. Expected format: 'module.path:attribute'")
        sys.exit(1)

    module_path, attr_path = catalog_path.rsplit(":", 1)

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
        help="Import path to the Catalog instance (e.g. 'myapp.setup:catalog')",
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
        help="Import path to the Catalog instance (e.g. 'myapp.setup:catalog')",
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
