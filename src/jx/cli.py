"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import argparse
import re
import sys
from difflib import get_close_matches
from pathlib import Path

from .catalog import Catalog
from .exceptions import JxException
from .meta import extract_metadata
from .parser import RX_TAG_NAME


def find_component_tags(source: str) -> list[tuple[str, int]]:
    """
    Find all component tags in the source and their line numbers.

    Returns:
        List of (tag_name, line_number) tuples.
    """
    tags = []
    lines = source.split("\n")
    for line_num, line in enumerate(lines, start=1):
        for match in RX_TAG_NAME.finditer(line):
            tags.append((match.group("tag"), line_num))
    return tags


def check_component(
    catalog: Catalog,
    relpath: str,
    all_components: set[str],
) -> list[str]:
    """
    Check a single component for issues.

    Returns:
        List of error messages (empty if no errors).
    """
    errors = []
    cdata = catalog.components[relpath]

    try:
        source = cdata.path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{relpath} - Not valid UTF-8"]

    try:
        meta = extract_metadata(source, base_path=cdata.base_path, fullpath=cdata.path)
    except JxException as err:
        return [f"{relpath} - {err}"]

    # Check that all imports exist
    for _import_name, import_path in meta.imports.items():
        if import_path not in all_components:
            suggestion = suggest_component(import_path, all_components)
            msg = f"{relpath} - Unknown import '{import_path}'"
            if suggestion:
                msg += f" (did you mean '{suggestion}'?)"
            errors.append(msg)

    # Build set of available component names for this file
    available = set(meta.imports.keys())

    # Check all component tags used in the source
    for tag, line_num in find_component_tags(source):
        if tag not in available:
            # Check if it exists in the catalog without being imported
            matching = [c for c in all_components if component_matches_tag(c, tag)]
            if matching:
                errors.append(
                    f"{relpath}:{line_num} - Component '{tag}' used but not imported"
                )
            else:
                suggestion = suggest_tag(tag, available, all_components)
                msg = f"{relpath}:{line_num} - Unknown component '{tag}'"
                if suggestion:
                    msg += f" (did you mean '{suggestion}'?)"
                errors.append(msg)

    return errors


def component_matches_tag(relpath: str, tag: str) -> bool:
    """Check if a component relpath could match a tag name."""
    # "button.jinja" -> "Button", "close-btn.jinja" -> "CloseBtn"
    name = Path(relpath).stem
    normalized = "".join(part.capitalize() for part in re.split(r"[-_]", name))
    return normalized == tag


def suggest_component(path: str, all_components: set[str]) -> str | None:
    """Suggest a similar component path."""
    matches = get_close_matches(path, all_components, n=1, cutoff=0.6)
    return matches[0] if matches else None


def suggest_tag(tag: str, imported: set[str], all_components: set[str]) -> str | None:
    """Suggest a similar tag name."""
    # First try imported names
    matches = get_close_matches(tag, imported, n=1, cutoff=0.6)
    if matches:
        return matches[0]

    # Then try deriving tag names from all components
    all_tags = set()
    for relpath in all_components:
        name = Path(relpath).stem
        normalized = "".join(part.capitalize() for part in re.split(r"[-_]", name))
        all_tags.add(normalized)

    matches = get_close_matches(tag, all_tags, n=1, cutoff=0.6)
    return matches[0] if matches else None


def check(paths: list[Path]) -> int:
    """
    Check components in the given paths.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    catalog = Catalog()

    for path in paths:
        if path.is_dir():
            catalog.add_folder(path, preload=False)
        elif path.is_file():
            # Single file - add its parent folder
            catalog.add_folder(path.parent, preload=False)

    all_components = set(catalog.components.keys())

    if not all_components:
        print("No components found")
        return 1

    total_errors = 0
    checked = 0

    for relpath in sorted(all_components):
        errors = check_component(catalog, relpath, all_components)
        checked += 1

        if errors:
            for error in errors:
                print(f"\u2717 {error}")
            total_errors += len(errors)
        else:
            print(f"\u2713 {relpath} - OK")

    print()
    print(f"{checked} component{'s' if checked != 1 else ''} checked, {total_errors} error{'s' if total_errors != 1 else ''}")

    return 1 if total_errors > 0 else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jx",
        description="Jx component validation tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Validate components")
    check_parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Paths to component folders or files",
    )

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(check(args.paths))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
