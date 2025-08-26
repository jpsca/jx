"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import ast
import re
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import DuplicateDefDeclaration, InvalidArgument, InvalidImport
from .parser import re_tag_name


# This regexp matches the meta declarations (`{#def .. #}``, `{#css .. #}``,
# and `{#js .. #}`) and regular Jinja comments AT THE BEGINNING of the components source.
# You can also have comments inside the declarations.
RX_META_HEADER = re.compile(r"^(\s*{#.*?#})+", re.DOTALL)

# This regexep matches comments (everything after a `#`)
# Used to remove them from inside meta declarations
RX_INTER_COMMENTS = re.compile(r"\s*#[^\n]*")

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
    required: tuple[str, ...] = ()
    optional: dict[str, t.Any] = field(default_factory=dict) # { attr: default_value }
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
            Absolute base path for all the template files
        fullpath:
            The absolute full path of the current template.

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
            expr = RX_INTER_COMMENTS.sub("", expr).replace("\n", " ")
            import_path, import_name = parse_import_expr(expr)
            if import_path.startswith("."):
                import_path = (fullpath.parent / import_path).resolve().relative_to(base_path).as_posix()
            meta.imports[import_name] = import_path
            continue

        expr = read_metadata_item(item, RX_CSS_START)
        if expr:
            expr = RX_INTER_COMMENTS.sub("", expr).replace("\n", " ")
            meta.css = (*meta.css, *parse_files_expr(expr))
            continue

        expr = read_metadata_item(item, RX_JS_START)
        if expr:
            expr = RX_INTER_COMMENTS.sub("", expr).replace("\n", " ")
            meta.js = (*meta.js, *parse_files_expr(expr))
            continue

    return meta


def read_metadata_item(source: str, rx_start: re.Pattern) -> str:
    start = rx_start.match(source)
    if not start:
        return ""
    return source[start.end():].strip()


def parse_args_expr(expr: str) -> tuple[tuple[str, ...], dict[str, t.Any]]:
    expr = expr.strip(" *,/")
    required = []
    optional = {}

    try:
        p = ast.parse(f"def component(*,\n{expr}\n): pass")
    except SyntaxError as err:
        raise InvalidArgument(err) from err

    args = p.body[0].args  # type: ignore
    arg_names = [arg.arg for arg in args.kwonlyargs]
    for name, value in zip(arg_names, args.kw_defaults):  # noqa: B905
        if value is None:
            required.append(name)
            continue
        expr = ast.unparse(value)
        optional[name] = eval_expression(expr)

    return tuple(required), optional


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
        if not url:
            continue
        if url.startswith(("/", "http://", "https://")):
            files.append(url)
        else:
            files.append(url)
    return files


def parse_import_expr(expr: str) -> tuple[str, str]:
    match = RX_IMPORT.match(expr)
    if not match:
        raise InvalidImport(expr)
    return match.group(1), match.group(2)
