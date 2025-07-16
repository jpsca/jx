import sys

from jx import Component


def test_collect_assets():
    class Child(Component):
        css = (
            "child.css",
            "/static/common/parent.css",
        )
        js = (
            "child.js",
            "https://example.com/child.js",
            "https://example.com/common.js",
        )
        template = """<span>{{ _content }}</span>"""

    class Parent(Component):
        css = (
            "parent.css",
            "/static/common/parent.css",
        )
        js = (
            "parent.js",
            "https://example.com/common.js",
        )
        components = [Child]
        template = """<Child>Hello</Child>"""

    co = Parent()
    assert co.collect_css(fingerprint=False) == [
        "parent.css",
        "/static/common/parent.css",
        "child.css",
    ]
    assert co.collect_js(fingerprint=False) == [
        "parent.js",
        "https://example.com/common.js",
        "child.js",
        "https://example.com/child.js",
    ]


def test_render_assets():
    class Child(Component):
        css = ("child.css",)
        js = ("child.js", "https://example.com/child.js")
        template = """<span>{{ _content }}</span>"""

    class Parent(Component):
        css = ("parent.css", "/static/common/parent.css")
        js = ("parent.js",)
        components = [Child]
        template = """<Child>Hello</Child>"""

    co = Parent()

    result = co.render_css(fingerprint=False)
    expected = "\n".join(
        [
            '<link rel="stylesheet" href="/static/parent.css">',
            '<link rel="stylesheet" href="/static/common/parent.css">',
            '<link rel="stylesheet" href="/static/child.css">',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected

    result = co.render_js(fingerprint=False)
    expected = "\n".join(
        [
            '<script type="module" src="/static/parent.js"></script>',
            '<script type="module" src="/static/child.js"></script>',
            '<script type="module" src="https://example.com/child.js"></script>',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected

    result = co.render_assets(fingerprint=False)
    expected = "\n".join(
        [
            '<link rel="stylesheet" href="/static/parent.css">',
            '<link rel="stylesheet" href="/static/common/parent.css">',
            '<link rel="stylesheet" href="/static/child.css">',
            '<script type="module" src="/static/parent.js"></script>',
            '<script type="module" src="/static/child.js"></script>',
            '<script type="module" src="https://example.com/child.js"></script>',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected


def test_render_assets_custom_base():
    class BaseComponent(Component):
        base_url = "/assets/"

    class Child(BaseComponent):
        css = ("child.css",)
        js = ("child.js", "https://example.com/child.js")
        template = """<span>{{ _content }}</span>"""

    class Parent(BaseComponent):
        css = ("parent.css", "/static/common/parent.css")
        js = ("parent.js",)
        components = [Child]
        template = """<Child>Hello</Child>"""

    co = Parent()

    result = co.render_css(fingerprint=False)
    expected = "\n".join(
        [
            '<link rel="stylesheet" href="/assets/parent.css">',
            '<link rel="stylesheet" href="/static/common/parent.css">',
            '<link rel="stylesheet" href="/assets/child.css">',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected

    result = co.render_js(fingerprint=False)
    expected = "\n".join(
        [
            '<script type="module" src="/assets/parent.js"></script>',
            '<script type="module" src="/assets/child.js"></script>',
            '<script type="module" src="https://example.com/child.js"></script>',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected


def test_fingerprint(tmp_path):
    path = tmp_path / "one"
    path.mkdir(exist_ok=True)

    css = path / "test_button_one.css"
    css.write_text("button { color: red; }")

    js = path / "test_button_one.js"
    js.write_text("console.log('Hello from test_button_one.js');")

    (path / "test_button_one.py").write_text("""
from jx import Component

class TestButtonOne(Component):
    template = "<button>Click me</button>"
    css = ("test_button_one.css",)
    js = ("test_button_one.js",)

""")

    sys.path.insert(0, str(path))
    from test_button_one import TestButtonOne  # type: ignore

    co = TestButtonOne()

    assets = co.render_assets(fingerprint=True)

    css_files = co.collect_css(fingerprint=True)
    assert css_files[0].startswith("test_button_one-")
    assert css_files[0].endswith(".css")

    js_files = co.collect_js(fingerprint=True)
    assert js_files[0].startswith("test_button_one-")
    assert js_files[0].endswith(".js")

    # Same content, same fingerprint
    assert co.render_assets(fingerprint=True) == assets
    assert co.collect_css(fingerprint=True) == css_files
    assert co.collect_js(fingerprint=True) == js_files

    # Change content to generate a new fingerprint
    css.write_text("button { color: green; }")
    js.write_text("console.log('Bye');")
    assert co.collect_css(fingerprint=True) != css_files
    assert co.collect_js(fingerprint=True) != js_files


def test_url_relative_to(tmp_path):
    path = tmp_path / "two" / "forms"
    path.mkdir(exist_ok=True, parents=True)

    css = path / "test_button_two.css"
    css.touch()

    js = path / "test_button_two.js"
    js.touch()

    (path / "test_button_two.py").write_text("""
from jx import Component

class TestButtonTwo(Component):
    template = "<button>Click me</button>"
    css = ("test_button_two.css",)
    js = ("test_button_two.js",)

""")

    sys.path.insert(0, str(path))
    from test_button_two import TestButtonTwo  # type: ignore

    co = TestButtonTwo()
    assert co.collect_css(fingerprint=False) == [
        "test_button_two.css"
    ]
    assert co.collect_js(fingerprint=False) == [
        "test_button_two.js"
    ]

    co.url_relative_to = tmp_path / "two"
    assert co.collect_css(fingerprint=False) == [
        "forms/test_button_two.css"
    ]
    assert co.collect_js(fingerprint=False) == [
        "forms/test_button_two.js"
    ]
