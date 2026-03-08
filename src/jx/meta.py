"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import ast
import builtins
import re
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import (
    DuplicateDefDeclaration,
    InvalidArgument,
    InvalidImport,
    PathTraversalError,
)
from .parser import re_tag_name


# This regexp matches the meta declarations (`{#def .. #}`, `{#css .. #}`,
# and `{#js .. #}`) and regular Jinja comments AT THE BEGINNING of the components source.
# You can also have comments inside the declarations.
RX_META_HEADER = re.compile(r"^(\s*{#.*?#})+", re.DOTALL)

# Matches quoted strings (to skip them) or inline comments (to strip).
# This preserves `#` inside quoted values like URLs with fragments.
RX_INTER_COMMENTS = re.compile(r""""[^"]*"|'[^']*'|\s*#[^\n]*""")


def _strip_comments(m: re.Match) -> str:
    s = m.group(0)
    if s[0] in "\"'":
        return s
    return ""


RX_DEF_START = re.compile(r"{#-?\s*def\s+")
RX_IMPORT_START = re.compile(r"{#-?\s*import\s+")
RX_CSS_START = re.compile(r"{#-?\s*css\s+")
RX_JS_START = re.compile(r"{#-?\s*js\s+")
RX_COMMA = re.compile(r"\s*,\s*")
RX_IMPORT = re.compile(fr'"([^"]+)"\s+as\s+({re_tag_name})')

ALLOWED_NAMES_IN_EXPRESSION_VALUES = {
    "len": len,
    "max": max,
    "min": min,
    "pow": pow,
    "sum": sum,
    # Jinja allows using lowercase booleans, so we do it too for consistency
    "false": False,
    "true": True,
}


@dataclass(slots=True)
class Meta:
    required: dict[str, type | None] = field(default_factory=dict)  # { attr: type or None }
    optional: dict[str, tuple[t.Any, type | None]] = field(default_factory=dict)  # { attr: (default, type or None) }
    imports: dict[str, str] = field(default_factory=dict)  # { component_name: relpath }
    css: tuple[str, ...] = ()
    js: tuple[str, ...] = ()


def extract_metadata(source: str, base_path: Path, fullpath: Path) -> Meta:
    """
    Extract metadata from the Jx template source.

    Arguments:
        source:
            The template source code.
        base_path:
            Absolute base path for all the template files, for relative imports.
        fullpath:
            The absolute full path of the current template, for relative imports.

    Returns:
        A `Meta` object containing the extracted metadata.

    """
    meta = Meta()

    match = RX_META_HEADER.match(source)
    if not match:
        return meta

    header = match.group(0)
    # Reversed because I will use `header.pop()`
    header = header.split("#}")[:-1][::-1]
    def_found = False

    while header:
        item = header.pop().strip(" -\n")

        expr = read_metadata_item(item, RX_DEF_START)
        if expr:
            if def_found:
                raise DuplicateDefDeclaration(str(fullpath))
            meta.required, meta.optional = parse_args_expr(expr)
            def_found = True
            continue

        expr = read_metadata_item(item, RX_IMPORT_START)
        if expr:
            expr = RX_INTER_COMMENTS.sub(_strip_comments, expr).replace("\n", " ")
            import_path, import_name = parse_import_expr(expr)
            if import_path.startswith("."):
                resolved = (fullpath.parent / import_path).resolve()
                validate_import_path(import_path, resolved, base_path)
                import_path = resolved.relative_to(base_path).as_posix()
            meta.imports[import_name] = import_path
            continue

        expr = read_metadata_item(item, RX_CSS_START)
        if expr:
            expr = RX_INTER_COMMENTS.sub(_strip_comments, expr).replace("\n", " ")
            meta.css = (*meta.css, *parse_files_expr(expr))
            continue

        expr = read_metadata_item(item, RX_JS_START)
        if expr:
            expr = RX_INTER_COMMENTS.sub(_strip_comments, expr).replace("\n", " ")
            meta.js = (*meta.js, *parse_files_expr(expr))
            continue

    return meta


def read_metadata_item(source: str, rx_start: re.Pattern) -> str:
    start = rx_start.match(source)
    if not start:
        return ""
    return source[start.end():].strip()


def annotation_to_type(annotation: ast.expr | None) -> type | None:
    """
    Convert an AST annotation node to a Python type.
    Returns None if the annotation is not a supported builtin type.

    ::: note
    For generic types like `list[str]` or `dict[str, int]`, only the base
    type (`list`, `dict`) is extracted. The generic parameters are discarded.
    This is sufficient for basic `isinstance()` validation but won't validate
    element types.

    To preserve full generic type info in the future, we could use
    `eval(ast.unparse(annotation), {"__builtins__": {}}, vars(builtins))`
    which returns the actual generic type object, which can be used with more
    advanced type checking libraries like `typeguard` or manual element validation.
    :::
    """
    if annotation is None:
        return None

    # For generics like `list[str]`, extract the base type
    if isinstance(annotation, ast.Subscript):
        annotation = annotation.value

    if isinstance(annotation, ast.Name):
        result = getattr(builtins, annotation.id, None)
        return result if isinstance(result, type) else None

    return None


def parse_args_expr(expr: str) -> tuple[dict[str, type | None], dict[str, tuple[t.Any, type | None]]]:
    expr = expr.strip(" *,/")
    required: dict[str, type | None] = {}
    optional: dict[str, tuple[t.Any, type | None]] = {}

    try:
        p = ast.parse(f"def component(*,\n{expr}\n): pass")
    except SyntaxError as err:
        raise InvalidArgument(err) from err

    args = p.body[0].args  # type: ignore
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):  # noqa: B905
        arg_type = annotation_to_type(arg.annotation)
        if default is None:
            required[arg.arg] = arg_type
            continue
        default_expr = ast.unparse(default)
        optional[arg.arg] = (eval_expression(default_expr), arg_type)

    return required, optional


def eval_expression(input_string: str) -> t.Any:
    code = compile(input_string, "<string>", "eval")
    for name in code.co_names:
        if name not in ALLOWED_NAMES_IN_EXPRESSION_VALUES:
            raise InvalidArgument(f"Use of {name} not allowed")
    return eval(code, {"__builtins__": {}}, ALLOWED_NAMES_IN_EXPRESSION_VALUES)


def parse_files_expr(expr: str) -> list[str]:
    files = []
    for url in RX_COMMA.split(expr):
        url = url.strip("\"'").rstrip("/")
        if url:
            files.append(url)
    return files


def parse_import_expr(expr: str) -> tuple[str, str]:
    match = RX_IMPORT.match(expr)
    if not match:
        raise InvalidImport(expr)
    return match.group(1), match.group(2)


def validate_import_path(path: str, resolved: Path, base_path: Path) -> None:
    """
    Validate that the resolved import path does not escape the component root.

    Arguments:
        path:
            The original import path string (for error messages).
        resolved:
            The resolved absolute path of the import.
        base_path:
            The base path that all imports must stay within.

    Raises:
        PathTraversalError: If the resolved path escapes the base path.

    """
    if not resolved.is_relative_to(base_path):
        raise PathTraversalError(path)
