"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import pytest

from jx import (
    Catalog,
    InvalidPropType,
    MaxRecursionDepthError,
    MissingRequiredArgument,
    TemplateSyntaxError,
)


def test_render_simple(folder):
    (folder / "button.jinja").write_text("""
{# def bid, text="Click me!" #}
<button id="{{ bid }}">{{ text }}</button>
""")

    cat = Catalog(folder)
    html = cat.render("button.jinja", bid="btn1", text="Submit")
    assert html.strip() == '<button id="btn1">Submit</button>'


def test_render_simple_from_string():
    source = """
{# def bid, text="Click me!" #}
<button id="{{ bid }}">{{ text }}</button>
"""

    cat = Catalog()
    html = cat.render_string(source, bid="btn1", text="Submit")
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


def test_render_content_from_string(folder):
    (folder / "child.jinja").write_text("""
<span>{{ content }}</span>
""")
    source = """
{# import "child.jinja" as Child #}
<div><Child>Hello</Child></div>
"""
    cat = Catalog(folder)
    html = cat.render_string(source)
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

    cat = Catalog(folder)
    with pytest.raises(TemplateSyntaxError, match="Unknown component `Child`.*"):
        cat.render("parent.jinja")


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


def test_render_globals_from_string(folder):
    (folder / "child.jinja").write_text("""<p>{{ lorem }}</p>""")

    (folder / "layout.jinja").write_text("""<div class="{{ lorem }}">{{ content }}</div>""")

    source = """
{# import "layout.jinja" as Layout #}
{# import "child.jinja" as Child #}
<Layout><Child /></Layout>
"""

    cat = Catalog(folder, lorem="ipsum")
    assert cat.render_string(source) == '<div class="ipsum"><p>ipsum</p></div>'


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


def test_render_assets_module_defer_combinations(folder):
    (folder / "child.jinja").write_text("""
{# css "child.css" #}
{# js "child.js" #}
<span>{{ content }}</span>
""")

    (folder / "parent.jinja").write_text("""
{# import "child.jinja" as Child #}
{# css "parent.css" #}
{# js "parent.js" #}
<Child>Hello</Child>
""")

    cat = Catalog(folder)
    co = cat.get_component("parent.jinja")

    # Default: module=True, defer=True → type="module" scripts (defer is irrelevant)
    html1 = co.render_assets()
    html2 = co.render_assets(module=True, defer=True)
    html3 = co.render_assets(module=True, defer=False)
    assert html1 == (
        '<link rel="stylesheet" href="parent.css">\n'
        '<link rel="stylesheet" href="child.css">\n'
        '<script type="module" src="parent.js"></script>\n'
        '<script type="module" src="child.js"></script>'
    )
    assert html1 == html2 == html3

    # module=False, defer=True (the default for defer) → deferred scripts
    html1 = co.render_assets(module=False)
    html2 = co.render_assets(module=False, defer=True)
    assert html1 == (
        '<link rel="stylesheet" href="parent.css">\n'
        '<link rel="stylesheet" href="child.css">\n'
        '<script src="parent.js" defer></script>\n'
        '<script src="child.js" defer></script>'
    )
    assert html1 == html2

    # module=False, defer=False → plain scripts
    html = co.render_assets(module=False, defer=False)
    assert html == (
        '<link rel="stylesheet" href="parent.css">\n'
        '<link rel="stylesheet" href="child.css">\n'
        '<script src="parent.js"></script>\n'
        '<script src="child.js"></script>'
    )


def test_global_assets_render(folder):
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


def test_global_assets_render_string(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{{ assets.render() }}
<div>{{ content }}</div>
""")

    source ="""
{# import "layout.jinja" as Layout #}
{# css "main.css", "/static/common/main.css" #}
{# js "main.js" #}
<Layout>Hello</Layout>
"""

    cat = Catalog(folder)
    html = cat.render_string(source)
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


def test_global_assets_render_js(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{{ assets.render_js() }}
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
<script type="module" src="main.js"></script>
<script type="module" src="layout.js"></script>
<script type="module" src="https://example.com/layout.js"></script>
<div>Hello</div>
    """.strip()


def test_global_assets_render_js_string(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{{ assets.render_js() }}
<div>{{ content }}</div>
""")

    source = """
{# import "layout.jinja" as Layout #}
{# css "main.css", "/static/common/main.css" #}
{# js "main.js" #}
<Layout>Hello</Layout>
"""

    cat = Catalog(folder)
    html = cat.render_string(source)
    print(html)
    assert html.strip() == """
<script type="module" src="main.js"></script>
<script type="module" src="layout.js"></script>
<script type="module" src="https://example.com/layout.js"></script>
<div>Hello</div>
    """.strip()


def test_global_assets_render_css(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{{ assets.render_css() }}
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
<div>Hello</div>
    """.strip()


def test_global_assets_render_css_string(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{{ assets.render_css() }}
<div>{{ content }}</div>
""")

    source = """
{# import "layout.jinja" as Layout #}
{# css "main.css", "/static/common/main.css" #}
{# js "main.js" #}
<Layout>Hello</Layout>
"""

    cat = Catalog(folder)
    html = cat.render_string(source)
    print(html)
    assert html.strip() == """
<link rel="stylesheet" href="main.css">
<link rel="stylesheet" href="/static/common/main.css">
<link rel="stylesheet" href="layout.css">
<div>Hello</div>
    """.strip()


def test_global_assets_collect(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{% for url in assets.collect_css() -%}
<link href="{{ url }}" rel="stylesheet">
{% endfor -%}
{% for url in assets.collect_js() -%}
<script src="{{ url }}" type="module"></script>
{% endfor -%}
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
<link href="main.css" rel="stylesheet">
<link href="/static/common/main.css" rel="stylesheet">
<link href="layout.css" rel="stylesheet">
<script src="main.js" type="module"></script>
<script src="layout.js" type="module"></script>
<script src="https://example.com/layout.js" type="module"></script>
<div>Hello</div>
    """.strip()


def test_global_assets_collect_string(folder):
    (folder / "layout.jinja").write_text("""
{# css "layout.css" #}
{# js "layout.js", "https://example.com/layout.js" #}
{% for url in assets.collect_css() -%}
<link href="{{ url }}" rel="stylesheet">
{% endfor -%}
{% for url in assets.collect_js() -%}
<script src="{{ url }}" type="module"></script>
{% endfor -%}
<div>{{ content }}</div>
""")

    source = """
{# import "layout.jinja" as Layout #}
{# css "main.css", "/static/common/main.css" #}
{# js "main.js" #}
<Layout>Hello</Layout>
"""

    cat = Catalog(folder)
    html = cat.render_string(source)
    print(html)
    assert html.strip() == """
<link href="main.css" rel="stylesheet">
<link href="/static/common/main.css" rel="stylesheet">
<link href="layout.css" rel="stylesheet">
<script src="main.js" type="module"></script>
<script src="layout.js" type="module"></script>
<script src="https://example.com/layout.js" type="module"></script>
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


def test_alpine_sintax(folder):
    (folder / "greeting.jinja").write_text("""
{#def message #}
<button @click.prevent="alert('{{ message }}')">Say Hi</button>""")
    cat = Catalog(folder, auto_reload=False)

    html = cat.render("greeting.jinja", message="Hello world!")
    print(html)
    assert html == """<button @click.prevent="alert('Hello world!')">Say Hi</button>"""


def test_alpine_sintax_in_component(folder):
    (folder / "button.jinja").write_text(
        """<button {{ attrs.render() }}>{{ content }}</button>"""
    )

    (folder / "greeting.jinja").write_text("""
{# import "button.jinja" as Button #}
<Button @click.prevent="alert('Hello world!')">Say Hi</Button>
""")
    cat = Catalog(folder, auto_reload=False)

    html = cat.render("greeting.jinja")
    print(html)
    assert html == """<button @click.prevent="alert('Hello world!')">Say Hi</button>"""


def test_recursion_depth_limit(folder):
    """Test that deeply nested components raise MaxRecursionDepthError."""
    # Create a component that infinitely recurses without termination
    (folder / "infinite.jinja").write_text("""
{# import "infinite.jinja" as Infinite #}
{# def level=1 #}
<div>Level {{ level }}</div>
<Infinite level={{ level + 1 }} />
""")

    cat = Catalog(folder)
    with pytest.raises(MaxRecursionDepthError) as exc_info:
        cat.render("infinite.jinja")
    assert "Maximum component nesting depth exceeded" in str(exc_info.value)
    assert "100" in str(exc_info.value)


def test_prop_type_validation(folder):
    """Test that props with type annotations are validated."""
    (folder / "typed.jinja").write_text("""
{# def title: str, count: int = 0 #}
<div>{{ title }} ({{ count }})</div>
""")

    cat = Catalog(folder)

    # Valid types
    html = cat.render("typed.jinja", title="Hello", count=5)
    assert html.strip() == "<div>Hello (5)</div>"

    # Invalid required prop type
    with pytest.raises(InvalidPropType) as exc_info:
        cat.render("typed.jinja", title=123)
    assert "title" in str(exc_info.value)
    assert "expected str" in str(exc_info.value)
    assert "got int" in str(exc_info.value)

    # Invalid optional prop type
    with pytest.raises(InvalidPropType) as exc_info:
        cat.render("typed.jinja", title="Hello", count="five")
    assert "count" in str(exc_info.value)
    assert "expected int" in str(exc_info.value)
    assert "got str" in str(exc_info.value)


def test_prop_type_validation_without_annotation(folder):
    """Test that props without type annotations skip validation."""
    (folder / "untyped.jinja").write_text("""
{# def title, count=0 #}
<div>{{ title }} ({{ count }})</div>
""")

    cat = Catalog(folder)

    # Any type should work when no annotation
    html = cat.render("untyped.jinja", title=123, count="five")
    assert html.strip() == "<div>123 (five)</div>"


def test_prop_type_validation_list(folder):
    """Test type validation with list type."""
    (folder / "list_typed.jinja").write_text("""
{# def items: list #}
<ul>{% for item in items %}<li>{{ item }}</li>{% endfor %}</ul>
""")

    cat = Catalog(folder)

    # Valid list
    html = cat.render("list_typed.jinja", items=["a", "b"])
    assert html.strip() == "<ul><li>a</li><li>b</li></ul>"

    # Invalid type (string instead of list)
    with pytest.raises(InvalidPropType) as exc_info:
        cat.render("list_typed.jinja", items="not a list")
    assert "items" in str(exc_info.value)
    assert "expected list" in str(exc_info.value)


# ---- Asset Resolver Tests ----


def test_asset_resolver_basic(tmp_path):
    """Resolver transforms URLs for prefixed components with an assets dir."""
    components = tmp_path / "pkg_components"
    components.mkdir()
    (components / "button.jinja").write_text("{#css button.css #}\n<button />")

    assets = tmp_path / "pkg_assets"
    assets.mkdir()

    def resolver(url, prefix):
        return f"/pkg/{prefix}/{url}"

    cat = Catalog(asset_resolver=resolver)
    cat.add_folder(components, prefix="ui", assets=assets)

    co = cat.get_component("@ui/button.jinja")
    css = co.collect_css()
    assert css == ["/pkg/ui/button.css"]


def test_asset_resolver_skips_no_assets_dir(tmp_path):
    """Resolver is NOT called for a prefix that has no assets dir."""
    components = tmp_path / "local"
    components.mkdir()
    (components / "card.jinja").write_text("{#css card.css #}\n<div />")

    calls = []

    def resolver(url, prefix):
        calls.append((url, prefix))
        return f"/pkg/{prefix}/{url}"

    cat = Catalog(asset_resolver=resolver)
    cat.add_folder(components, prefix="local")  # no assets= param

    co = cat.get_component("@local/card.jinja")
    css = co.collect_css()
    assert css == ["card.css"]  # pass-through, not resolved
    assert calls == []  # resolver was never called


def test_asset_resolver_skips_unprefixed(tmp_path):
    """Resolver is NOT called for unprefixed components without assets dir."""
    components = tmp_path / "local"
    components.mkdir()
    (components / "card.jinja").write_text("{#css card.css #}\n<div />")

    calls = []

    def resolver(url, prefix):
        calls.append((url, prefix))
        return f"/resolved/{url}"

    cat = Catalog(asset_resolver=resolver)
    cat.add_folder(components)

    co = cat.get_component("card.jinja")
    css = co.collect_css()
    assert css == ["card.css"]
    assert calls == []


def test_asset_resolver_with_children(tmp_path):
    """Child components from different prefixes resolve correctly."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "button.jinja").write_text("{#css button.css #}\n<button />")

    pkg_assets = tmp_path / "pkg_assets"
    pkg_assets.mkdir()

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "page.jinja").write_text(
        '{#import "@ui/button.jinja" as Button #}\n'
        '{#css page.css #}\n'
        '<Button />'
    )

    def resolver(url, prefix):
        return f"/pkg/{prefix}/{url}"

    cat = Catalog(asset_resolver=resolver)
    cat.add_folder(local_dir)
    cat.add_folder(pkg_dir, prefix="ui", assets=pkg_assets)

    co = cat.get_component("page.jinja")
    css = co.collect_css()
    # page.css is local (no assets dir), passes through
    # button.css is from @ui (has assets dir), gets resolved
    assert css == ["page.css", "/pkg/ui/button.css"]


def test_asset_resolver_js(tmp_path):
    """Resolver also works for JS assets."""
    components = tmp_path / "pkg"
    components.mkdir()
    (components / "widget.jinja").write_text(
        "{#js widget.js #}\n<div>widget</div>"
    )

    assets = tmp_path / "assets"
    assets.mkdir()

    def resolver(url, prefix):
        return f"/pkg/{prefix}/{url}"

    cat = Catalog(asset_resolver=resolver)
    cat.add_folder(components, prefix="ui", assets=assets)

    co = cat.get_component("@ui/widget.jinja")
    js = co.collect_js()
    assert js == ["/pkg/ui/widget.js"]


def test_asset_resolver_render_integration(tmp_path):
    """Full render pipeline applies resolver in assets.render_css()."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "button.jinja").write_text(
        "{#css button.css #}\n<button>{{ content }}</button>"
    )

    pkg_assets = tmp_path / "assets"
    pkg_assets.mkdir()

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "page.jinja").write_text(
        '{#import "@ui/button.jinja" as Button #}\n'
        '{#css page.css #}\n'
        '{{ assets.render_css() }}\n'
        '<Button>click</Button>'
    )

    def resolver(url, prefix):
        return f"/pkg/{prefix}/{url}"

    cat = Catalog(asset_resolver=resolver)
    cat.add_folder(local_dir)
    cat.add_folder(pkg_dir, prefix="ui", assets=pkg_assets)

    html = cat.render("page.jinja")
    assert '<link rel="stylesheet" href="page.css">' in html
    assert '<link rel="stylesheet" href="/pkg/ui/button.css">' in html


def test_no_resolver_backward_compatible(tmp_path):
    """Without asset_resolver, everything works exactly as before."""
    components = tmp_path / "views"
    components.mkdir()
    (components / "btn.jinja").write_text("{#css btn.css #}\n<button />")

    cat = Catalog(components)
    co = cat.get_component("btn.jinja")
    assert co.collect_css() == ["btn.css"]
