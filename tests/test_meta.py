"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
from pathlib import Path

import pytest

from jx.meta import (
    DuplicateDefDeclaration,
    InvalidArgument,
    InvalidImport,
    extract_metadata,
)


def test_empty_source():
    """Test that empty source returns empty metadata."""
    source = ""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")
    assert meta.required == ()
    assert meta.optional == {}
    assert meta.imports == {}
    assert meta.css == ()
    assert meta.js == ()


def test_source_without_metadata():
    """Test that source without metadata comments returns empty metadata."""
    source = """<div>Hello world</div>"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.required == ()
    assert meta.optional == {}
    assert meta.imports == {}
    assert meta.css == ()
    assert meta.js == ()


def test_def_metadata():
    """Test extraction of required and optional arguments."""
    source = """
{# def
    name,
    age=18,
    is_active=true
#}
<div>Hello {{ name }}</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.required == ("name",)
    assert meta.optional == {"age": 18, "is_active": True}


def test_def_with_allowed_expressions():
    """Test extraction of arguments with allowed expressions."""
    source = """
{# def
    max_items=max(10, 20),
    min_value=min(5, 10),
    total=sum([1, 2, 3]),
    length=len("hello"),
    power=pow(2, 3)
#}
<div>Config</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.optional == {
        "max_items": 20,
        "min_value": 5,
        "total": 6,
        "length": 5,
        "power": 8
    }


def test_invalid_argument():
    """Test that invalid arguments raise an exception."""
    source = """
{# def name=invalid_function() #}
<div>Hello {{ name }}</div>
"""
    with pytest.raises(InvalidArgument):
        base = Path("dummy")
        extract_metadata(source, base, base / "test.jinja")


def test_unparsable_argument():
    """Test that unparseable arguments raise an exception."""
    source = """
{# def name=$3 #}
<div>Hello {{ name }}</div>
"""
    with pytest.raises(InvalidArgument):
        base = Path("dummy")
        extract_metadata(source, base, base / "test.jinja")


def test_invalid_expression():
    """Test that invalid expressions raise an exception."""
    source = """
{# def name=5/0 #}
<div>Hello {{ name }}</div>
"""
    with pytest.raises(ZeroDivisionError):
        base = Path("dummy")
        extract_metadata(source, base, base / "test.jinja")


def test_import_metadata():
    """Test extraction of imports."""
    source = """
{# import "components/button.jinja" as Button #}
{# import "components/header.jinja" as Header #}
<div>{{ Button() }}</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.imports == {
        "Button": "components/button.jinja",
        "Header": "components/header.jinja"
    }


def test_relative_import_metadata():
    """Test extraction of relative imports."""
    base = Path("/app/views")
    source = """
{# import "./button.jinja" as Button #}
<div>{{ Button() }}</div>
    """
    meta = extract_metadata(source, base, base / "foo/bar.jinja")

    assert meta.imports == {
        "Button": "foo/button.jinja",
    }


def test_complex_relative_import_metadata():
    """Test extraction of complex relative imports."""
    base = Path.cwd() / "views"
    source = """
{# import "../forms/button.jinja" as Button #}
<div>{{ Button() }}</div>
    """
    meta = extract_metadata(source, base, base / "foo/bar/header.jinja")

    assert meta.imports == {
        "Button": "foo/forms/button.jinja",
    }

def test_invalid_relative_import():
    """Test that invalid relative imports raise an exception."""
    base = Path("/app/views")
    source = """
{# import ../button.jinja as Button #}
<div>{{ Button() }}</div>
"""
    with pytest.raises(InvalidImport):
        extract_metadata(source, base, base / "test.jinja")


def test_css_metadata():
    """Test extraction of CSS references."""
    source = """
{# css "/static/styles.css", "https://cdn.example.com/style.css" #}
<div>Styled content</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.css == (
        "/static/styles.css",
        "https://cdn.example.com/style.css"
    )


def test_js_metadata():
    """Test extraction of JS references."""
    source = """
{# js "/static/script.js", "https://cdn.example.com/script.js" #}
<div>Interactive content</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.js == (
        "/static/script.js",
        "https://cdn.example.com/script.js"
    )


def test_css_commas():
    """Test extraction of CSS references even with extra commas."""
    source = """
{# css "/static/styles.css",, "https://cdn.example.com/style.css", #}
<div>Styled content</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.css == (
        "/static/styles.css",
        "https://cdn.example.com/style.css",
    )


def test_js_commas():
    """Test extraction of JS references even with extra commas."""
    source = """
{# js "/static/script.js",, "https://cdn.example.com/script.js", #}
<div>Interactive content</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.js == (
        "/static/script.js",
        "https://cdn.example.com/script.js",
    )


def test_comments_in_metadata():
    """Test that comments in metadata are ignored."""
    source = """
{# def
  name, # This is a required field
  age=18 # Default age
#}
<div>Hello {{ name }}</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.required == ("name",)
    assert meta.optional == {"age": 18}


def test_multiple_metadata_blocks():
    """Test extracting multiple metadata blocks."""
    source = """
{# def name, age=21 #}
{# import "button.jinja" as Button #}
{# css "/style.css" #}
{# js "/script.js" #}
<div>Hello {{ name }}</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")

    assert meta.required == ("name",)
    assert meta.optional == {"age": 21}
    assert meta.imports == {"Button": "button.jinja"}
    assert meta.css == ("/style.css", )
    assert meta.js == ("/script.js", )


def test_duplicate_def_declaration():
    """Test that duplicate def declarations raise an exception."""
    source = """
{# def name #}
{# def age #}
<div>Hello {{ name }}</div>
"""
    with pytest.raises(DuplicateDefDeclaration):
        base = Path("dummy")
        extract_metadata(source, base, base / "test.jinja")


def test_empty_meta_declarations():
    """Test that empty meta declarations are handled correctly."""
    source = """
{# def #}
<div>Hello world</div>
"""
    base = Path("dummy")
    meta = extract_metadata(source, base, base / "test.jinja")
    assert meta.required == ()
    assert meta.optional == {}
    assert meta.imports == {}
