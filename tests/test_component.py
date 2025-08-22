"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import pytest

from jx import Catalog, MissingRequiredArgument, TemplateSyntaxError


def test_render_simple(folder):
    (folder / "button.jinja").write_text("""
{# def bid, text="Click me!" #}
<button id="{{ bid }}">{{ text }}</button>
""")

    cat = Catalog(folder)
    html = cat.render("button.jinja", bid="btn1", text="Submit")
    assert html.strip() == '<button id="btn1">Submit</button>'


def test_render_content(folder):
    (folder / "child.jinja").write_text("""
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
<div><Child>Hello</Child></div>
""")

    cat = Catalog(folder)
    html = cat.render("parent.jinja")
    assert html.strip() == "<div><span>Hello</span></div>"


def test_render_custom_content(folder):
    (folder / "child.jinja").write_text("""
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
<div><Child content="Hello" /></div>
""")

    cat = Catalog(folder)
    html = cat.render("parent.jinja")
    assert html.strip() == "<div><span>Hello</span></div>"


def test_unknown_child(folder):
    (folder / "child.jinja").write_text("""
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
<div><Child>Hello</Child></div>
""")

    with pytest.raises(TemplateSyntaxError, match="Unknown component `Child`.*"):
        Catalog(folder)


def test_missing_required_prop(folder):
    (folder / "button.jinja").write_text("""
{# def bid, text="Click me!" #}
<button id="{{ bid }}">{{ text }}</button>
""")

    cat = Catalog(folder)

    with pytest.raises(MissingRequiredArgument, match=".*`bid`.*"):
      cat.render("button.jinja")


def test_missing_required_child_prop(folder):
    (folder / "button.jinja").write_text("""
{# def bid, text="Click me!" #}
<button id="{{ bid }}">{{ text }}</button>
""")

    (folder / "parent.jinja").write_text("""
{# import "button.jinja" as Button #}
<Button text="text" />
""")

    cat = Catalog(folder)

    with pytest.raises(MissingRequiredArgument, match=".*`bid`.*"):
      cat.render("parent.jinja")


def test_inherited_attrs(folder):
    (folder / "button.jinja").write_text("""
<button {{ attrs.render() }}>{{ content }}</button>
""")

    (folder / "child.jinja").write_text("""
{# import "button.jinja" as Button #}
<span><Button attrs={{ attrs }}>{{ content }}</Button></span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
<div><Child class="btn btn-primary">Hello</Child></div>
""")

    cat = Catalog(folder)
    html = cat.render("parent.jinja")
    assert html.strip() == '<div><span><button class="btn btn-primary">Hello</button></span></div>'


def test_get_random_id(folder):
    (folder / "button.jinja").write_text("""
<button id="{{ _get_random_id() }}">Click me</button>
""")

    cat = Catalog(folder)
    # Ensure different IDs are generated
    assert cat.render("button.jinja") != cat.render("button.jinja")


def test_catalog_globals(folder):
    (folder / "button.jinja").write_text("""<button>{{ lorem }}</button>""")

    cat = Catalog(folder, lorem="ipsum")
    html = cat.render("button.jinja")
    assert html.strip() == "<button>ipsum</button>"


def test_render_globals(folder):
    (folder / "child.jinja").write_text("""<p>{{ lorem }}</p>""")

    (folder / "layout.jinja").write_text("""<div class="{{ lorem }}">{{ content }}</div>""")

    (folder / "page.jinja").write_text("""
{# import "layout.jinja" as Layout #}
{# import "child.jinja" as Child #}
<Layout><Child /></Layout>
""")

    cat = Catalog(folder, lorem="ipsum")
    assert cat.render("page.jinja") == '<div class="ipsum"><p>ipsum</p></div>'


def test_collect_assets(folder):
    (folder / "child.jinja").write_text("""
{# css "child.css", "/static/common/parent.css" #}
{# js "child.js", "https://example.com/child.js", "https://example.com/common.js" #}
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
{# css "parent.css", "/static/common/parent.css" #}
{# js "parent.js", "https://example.com/common.js" #}
<Child>Hello</Child>
""")

    cat = Catalog(folder)
    component = cat.get_component("parent.jinja")

    # Check CSS collection (deduplicated)
    css_files = component.collect_css()
    print(css_files)
    assert "parent.css" in css_files
    assert "/static/common/parent.css" in css_files
    assert "child.css" in css_files
    assert len(css_files) == 3

    # Check JS collection (deduplicated)
    js_files = component.collect_js()
    print(js_files)
    assert "parent.js" in js_files
    assert "https://example.com/common.js" in js_files
    assert "child.js" in js_files
    assert "https://example.com/child.js" in js_files
    assert len(js_files) == 4


def test_render_css(folder):
    (folder / "child.jinja").write_text("""
{# css "child.css" #}
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
{# css "parent.css", "/static/common/parent.css" #}
<Child>Hello</Child>
""")

    cat = Catalog(folder)
    component = cat.get_component("parent.jinja")

    css_html = component.render_css()
    print(css_html)
    assert css_html == """
<link rel="stylesheet" href="parent.css">
<link rel="stylesheet" href="/static/common/parent.css">
<link rel="stylesheet" href="child.css">
    """.strip()


def test_render_js(folder):
    (folder / "child.jinja").write_text("""
{# js "child.js", "https://example.com/child.js" #}
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
{# js "parent.js" #}
<Child>Hello</Child>
""")

    cat = Catalog(folder)
    component = cat.get_component("parent.jinja")

    js_html = component.render_js()
    print(js_html)
    assert js_html == """
<script type="module" src="parent.js"></script>
<script type="module" src="child.js"></script>
<script type="module" src="https://example.com/child.js"></script>
    """.strip()

    js_html = component.render_js(module=False)
    print(js_html)
    assert js_html == """
<script src="parent.js" defer></script>
<script src="child.js" defer></script>
<script src="https://example.com/child.js" defer></script>
    """.strip()

    js_html = component.render_js(module=False, defer=False)
    print(js_html)
    assert js_html == """
<script src="parent.js"></script>
<script src="child.js"></script>
<script src="https://example.com/child.js"></script>
    """.strip()


def test_render_assets(folder):
    (folder / "child.jinja").write_text("""
{# css "child.css" #}
{# js "child.js", "https://example.com/child.js" #}
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
{# css "parent.css", "/static/common/parent.css" #}
{# js "parent.js" #}
<Child>Hello</Child>
""")

    cat = Catalog(folder)
    component = cat.get_component("parent.jinja")

    html = component.render_assets()
    print(html)
    assert html.strip() == """
<link rel="stylesheet" href="parent.css">
<link rel="stylesheet" href="/static/common/parent.css">
<link rel="stylesheet" href="child.css">
<script type="module" src="parent.js"></script>
<script type="module" src="child.js"></script>
<script type="module" src="https://example.com/child.js"></script>
    """.strip()


def test_render_assets_in_layout(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{{ assets.render() }}
<div>{{ content }}</div>
""")

    (folder / "main.jinja").write_text("""
{# import "layout.jinja" as Layout #}
{# css "main.css", "/static/common/main.css" #}
{# js "main.js" #}
<Layout>Hello</Layout>
""")

    cat = Catalog(folder)
    html = cat.render("main.jinja")
    print(html)
    assert html.strip() == """
<link rel="stylesheet" href="main.css">
<link rel="stylesheet" href="/static/common/main.css">
<link rel="stylesheet" href="layout.css">
<script type="module" src="main.js"></script>
<script type="module" src="layout.js"></script>
<script type="module" src="https://example.com/layout.js"></script>
<div>Hello</div>
    """.strip()


def test_recursive_component(folder):
    (folder / "recu.jinja").write_text("""
{# import "recu.jinja" as Recu #}
{# def items: list[str], level=1 #}
{# css "recu.css" #}
{% if items %}
<h{{ level }}>Level {{ level }}</h{{ level }}>
<p>{{ items[0] }}</p>
<Recu items={{ items[1:] }} level={{ level + 1 }} />
{%- endif %}
""")

    (folder / "main.jinja").write_text("""
{# import "recu.jinja" as Recu #}
{# def items: list[str] #}
{# css "main.css" #}
{{ assets.render() }}
<Recu items={{ items }} />
""")

    cat = Catalog(folder)
    html = cat.render("main.jinja", items=["one", "two", "three"])
    print(html)
    assert html.strip() == """
<link rel="stylesheet" href="main.css">
<link rel="stylesheet" href="recu.css">
<h1>Level 1</h1>
<p>one</p>
<h2>Level 2</h2>
<p>two</p>
<h3>Level 3</h3>
<p>three</p>
""".strip()


def test_indirect_recursion(folder):
    (folder / "a.jinja").write_text("""
{# import "b.jinja" as B #}
{# def level #}
{# css "a.css" #}
{% if level > 0 -%}
{{ level }}
<B level={{ level - 1 }} />
{%- endif %}
""")

    (folder / "b.jinja").write_text("""
{# import "a.jinja" as A #}
{# def level #}
{# css "b.css" #}
{% if level > 0 -%}
{{ level }}
<A level={{ level - 1 }} />
{%- endif %}
""")

    (folder / "main.jinja").write_text("""
{# import "a.jinja" as A #}
{{ assets.render_css() }}
<A level={{ 10 }} />
""")

    cat = Catalog(folder)
    html = cat.render("main.jinja")
    print(html)
    assert html.strip() == """
<link rel="stylesheet" href="a.css">
<link rel="stylesheet" href="b.css">
10
9
8
7
6
5
4
3
2
1
""".strip()


def test_autoreload(folder):
    (folder / "test.jinja").write_text("""
{# css before.css #}
{{ assets.render_css() }}
BEFORE
""")

    cat = Catalog(folder, auto_reload=True)

    html = cat.render("test.jinja")
    assert html.strip() == """
<link rel="stylesheet" href="before.css">
BEFORE
""".strip()

    (folder / "test.jinja").write_text("""
{# css after.css #}
{{ assets.render_css() }}
AFTER
""")

    html = cat.render("test.jinja")
    assert html == """
<link rel="stylesheet" href="after.css">
AFTER
""".strip()


def test_no_autoreload(folder):
    (folder / "test.jinja").write_text("""
{# css before.css #}
{{ assets.render_css() }}
BEFORE
""")
    cat = Catalog(folder, auto_reload=False)

    html = cat.render("test.jinja")
    assert html == """
<link rel="stylesheet" href="before.css">
BEFORE
""".strip()

    (folder / "test.jinja").write_text("""
{# css after.css #}
{{ assets.render_css() }}
AFTER
""")

    html = cat.render("test.jinja")
    assert html == """
<link rel="stylesheet" href="before.css">
BEFORE
""".strip()
