"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import json
import re
from dataclasses import asdict, dataclass
from difflib import get_close_matches
from pathlib import Path

from .catalog import Catalog
from .exceptions import JxException
from .meta import extract_metadata
from .parser import RX_COMMENT, RX_RAW, RX_TAG_NAME, JxParser


@dataclass
class CheckError:
    file: str
    line: int | None
    message: str
    suggestion: str | None = None
    abs_path: str | None = None


def find_component_tags(source: str) -> list[tuple[str, int]]:
    """
    Find all component tags in the source and their line numbers.
    Strips Jinja comments and raw blocks first to avoid false positives.

    Returns:
        List of (tag_name, line_number) tuples.
    """
    # Replace comments/raw blocks with same-length whitespace to preserve line numbers
    def _blank(m: re.Match) -> str:
        text = m.group(0)
        return "".join("\n" if c == "\n" else " " for c in text)

    cleaned = RX_RAW.sub(_blank, source)
    cleaned = RX_COMMENT.sub(_blank, cleaned)

    tags = []
    for match in RX_TAG_NAME.finditer(cleaned):
        line_num = cleaned[:match.start()].count("\n") + 1
        tags.append((match.group("tag"), line_num))
    return tags


def check_component(
    catalog: Catalog,
    relpath: str,
    all_components: set[str],
) -> list[CheckError]:
    """
    Check a single component for issues.

    Returns:
        List of CheckError objects (empty if no errors).
    """
    errors: list[CheckError] = []
    cdata = catalog.components[relpath]
    abs_path = str(cdata.path)

    try:
        source = cdata.path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [CheckError(file=relpath, line=None, message="Not valid UTF-8", abs_path=abs_path)]

    try:
        meta = extract_metadata(source, base_path=cdata.base_path, fullpath=cdata.path)
    except JxException as err:
        return [CheckError(file=relpath, line=None, message=str(err), abs_path=abs_path)]

    # Check that all imports exist
    for _import_name, import_path in meta.imports.items():
        if import_path not in all_components:
            suggestion = suggest_component(import_path, all_components)
            errors.append(CheckError(
                file=relpath,
                line=None,
                message=f"Unknown import '{import_path}'",
                suggestion=suggestion,
                abs_path=abs_path,
            ))

    # Build set of available component names for this file
    available = set(meta.imports.keys())

    # Check all component tags used in the source
    for tag, line_num in find_component_tags(source):
        if tag not in available:
            # Check if it exists in the catalog without being imported
            matching = [c for c in all_components if component_matches_tag(c, tag)]
            if matching:
                errors.append(CheckError(
                    file=relpath,
                    line=line_num,
                    message=f"Component '{tag}' used but not imported",
                    abs_path=abs_path,
                ))
            else:
                suggestion = suggest_tag(tag, available, all_components)
                errors.append(CheckError(
                    file=relpath,
                    line=line_num,
                    message=f"Unknown component '{tag}'",
                    suggestion=suggestion,
                    abs_path=abs_path,
                ))

    # Parse the template to catch syntax errors (unclosed tags, unmatched braces, etc.)
    try:
        components = list(meta.imports.keys())
        parser = JxParser(name=relpath, source=source, components=components)
        parser.parse(validate_tags=False)
    except JxException as err:
        errors.append(CheckError(file=relpath, line=None, message=str(err), abs_path=abs_path))

    return errors


def relpath_to_tag(relpath: str) -> str:
    """Convert a component relpath to a PascalCase tag name.

    "button.jx" -> "Button", "close-btn.jx" -> "CloseBtn"
    """
    name = Path(relpath).stem
    return "".join(part.capitalize() for part in re.split(r"[-_]", name))


def component_matches_tag(relpath: str, tag: str) -> bool:
    """Check if a component relpath could match a tag name."""
    return relpath_to_tag(relpath) == tag


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
    all_tags = {relpath_to_tag(relpath) for relpath in all_components}
    matches = get_close_matches(tag, all_tags, n=1, cutoff=0.6)
    return matches[0] if matches else None


def check_all(catalog: Catalog) -> tuple[list[CheckError], int]:
    """
    Check all components in the catalog.

    Returns:
        Tuple of (list of errors, number of components checked).
    """
    all_components = set(catalog.components.keys())
    all_errors: list[CheckError] = []
    checked = 0

    for relpath in sorted(all_components):
        errors = check_component(catalog, relpath, all_components)
        checked += 1
        all_errors.extend(errors)

    return all_errors, checked


def format_error(error: CheckError) -> str:
    """Format a CheckError as a human-readable string."""
    if error.line is not None:
        msg = f"{error.file}:{error.line} - {error.message}"
    else:
        msg = f"{error.file} - {error.message}"
    if error.suggestion:
        msg += f" (did you mean '{error.suggestion}'?)"
    return msg


def check(catalog: Catalog, *, format: str = "text") -> int:
    """
    Check all components in the catalog.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    errors, checked = check_all(catalog)

    if format == "json":
        print(json.dumps({
            "checked": checked,
            "errors": [asdict(e) for e in errors],
        }))
        return 1 if errors else 0

    # Text format
    if not checked:
        print("No components found")
        return 1

    errors_by_file: dict[str, list[CheckError]] = {}
    for error in errors:
        errors_by_file.setdefault(error.file, []).append(error)

    for relpath in sorted(catalog.components.keys()):
        file_errors = errors_by_file.get(relpath)
        if file_errors:
            for error in file_errors:
                print(f"\u2717 {format_error(error)}")
        else:
            print(f"\u2713 {relpath} - OK")

    total_errors = len(errors)
    print()
    print(f"{checked} component{'s' if checked != 1 else ''} checked, {total_errors} error{'s' if total_errors != 1 else ''}")

    return 1 if total_errors > 0 else 0
