import pytest

from jx import Component, TemplateSyntaxError

from .data import Button


def test_load():
    co = Button()
    assert co.template == "<button>Click me!</button>"
    assert co.css == ("button.css",)
    assert co.js == ("button.js",)


def test_default_init():
    class Meh(Component):
        template = """<span class="info">meh</span>"""

    co = Meh()
    assert co.template
    assert co.template == Meh.template
    assert co.required == ()
    assert co.optional == {}


def test_empty_init():
    class Meh(Component):
        template = """<span class="info">meh</span>"""

        def render(self):
            return self()

    co = Meh()
    assert co.template
    assert co.template == Meh.template
    assert co.required == ()
    assert co.optional == {}


def test_parse_signature():
    class Button(Component):
        template = """<button id="{{ bid }}">{{ text }}</button>"""

        def render(self, bid, text="Click me!"):
            return self(bid=bid, text=text)

    co = Button()
    assert co.required == ("bid",)
    assert co.optional == {"text": "Click me!"}


def test_render_exact():
    class Button(Component):
        template = """<button id="{{ bid }}">{{ text }}</button>"""

        def render(self, bid, text="Click me!"):
            return self(bid=bid, text=text)

    co = Button()
    html = co.render(bid="btn1", text="Submit")
    assert html == '<button id="btn1">Submit</button>'


def test_missing_required():
    class Button(Component):
        template = """<button id="{{ bid }}">{{ text }}</button>"""

        def render(self, bid, *, text="Click me!"):
            return self(bid=bid, text=text)

    class Parent(Component):
        components = [Button]
        template = """<Button text="Submit" />"""

    co = Parent()
    print(co._template)
    with pytest.raises(TypeError, match=".*'bid'.*"):
        co.render(text="Submit")  # type: ignore


def test_render_derived_data():
    class Button(Component):
        template = """<button class="{{ classes }}">{{ text }}</button>"""

        def render(self, var="primary", text="Click me!"):
            return self(
                var=var,
                text=text,
                classes=f"btn btn-{var}",
            )

    co = Button()
    html = co.render(text="Submit")
    assert html == '<button class="btn btn-primary">Submit</button>'


def test_child_component():
    class Child(Component):
        template = """<span>{{ _content }}</span>"""

    class Parent(Component):
        components = [Child]
        template = """<div><Child>Hello</Child></div>"""

    co = Parent()
    html = co.render()
    assert html == "<div><span>Hello</span></div>"


def test_child_component_renamed():
    class Child(Component):
        template = """<span>{{ _content }}</span>"""

    class Parent(Component):
        components = [Child(name="Say")]
        template = """<div><Say>Hello</Say></div>"""

    co = Parent()
    html = co.render()
    assert html == "<div><span>Hello</span></div>"


def test_unknown_child_component():
    class Child(Component):
        template = """<span>{{ _content }}</span>"""

    class Parent(Component):
        components = []
        template = """<div><Child>Hello</Child></div>"""

    with pytest.raises(TemplateSyntaxError, match="Unknown component `Child`.*"):
        Parent()


def test_child_not_a_component():
    class Child:
        template = """<span>{{ _content }}</span>"""

    class Parent(Component):
        components = [Child]  # type: ignore
        template = """<div><Child>Hello</Child></div>"""

    with pytest.raises(TypeError, match="'Child'.*"):
        Parent()


def test_inherited_attrs():
    class Button(Component):
        template = """<button {{ _attrs.render() }}>{{ _content }}</button>"""

    class Child(Component):
        components = [Button]
        template = """<span><Button :_attrs="_attrs">{{ _content }}</Button></span>"""

    class Parent(Component):
        components = [Child]
        template = """<div><Child class="btn btn-primary">Hello</Child></div>"""

    co = Parent()
    html = co.render()
    assert (
        html == '<div><span><button class="btn btn-primary">Hello</button></span></div>'
    )


def test_content_returned():
    class Child(Component):
        template = """<span>{{ _content }}</span>"""

        def render(self):
            return self(_content=self._content * 2)

    class Parent(Component):
        components = [Child]
        template = """<div><Child>Hello</Child></div>"""

    co = Parent()
    html = co.render()
    assert html == "<div><span>HelloHello</span></div>"


def test_content_reassigned():
    class Child(Component):
        template = """<span>{{ _content }}</span>"""

        def render(self):
            self._content = self._content * 2
            return self()

    class Parent(Component):
        components = [Child]
        template = """<div><Child>Hello</Child></div>"""

    co = Parent()
    html = co.render()
    assert html == "<div><span>HelloHello</span></div>"


def test_attrs_modification():
    class Child(Component):
        template = """<button {{ _attrs.render() }}>{{ _content }}</button>"""

        def render(self, var="primary"):
            self._attrs.add_class(f"btn-{var}")
            return self()

    class Parent(Component):
        components = [Child]
        template = """<div><Child var="secondary">Cancel</Child></div>"""

    co = Parent()
    html = co.render()
    assert html == '<div><button class="btn-secondary">Cancel</button></div>'


def test_random_id():
    class Button(Component):
        template = """<button id="{{ _get_random_id() }}">Click me</button>"""

    co = Button()
    assert co.render() != co.render()  # Ensure different IDs are generated


def test_vue_expr():
    class Child(Component):
        template = """<span>{{ text }}</span>"""

        def render(self, text: str):
            return self(text=text)

    class Parent(Component):
        components = [Child]
        template = """<div><Child :text="text * 2" /></div>"""

        def render(self, text: str):
            return self(text=text)

    co = Parent()
    html = co.render(text="Hello")
    assert html == "<div><span>HelloHello</span></div>"


def test_jinja_expr():
    class Child(Component):
        template = """<span>{{ text }}</span>"""

        def render(self, text: str):
            return self(text=text)

    class Parent(Component):
        components = [Child]
        template = """<div><Child text={{text * 2}} /></div>"""

        def render(self, text: str):
            return self(text=text)

    co = Parent()
    html = co.render(text="Hello")
    assert html == "<div><span>HelloHello</span></div>"


def test_globals():
    class SubChild(Component):
        template = """<span>{{ lorem }}</span>"""

    class Child(Component):
        components = [SubChild]
        template = """<p><SubChild /></p>"""

    class Parent(Component):
        components = [Child]
        template = """<div><Child /></div>"""

    co = Parent(lorem="ipsum")
    html = co.render()
    assert html == "<div><p><span>ipsum</span></p></div>"


def test_globals_with_instances():
    class SubChild(Component):
        template = """<span>{{ lorem }}</span>"""

    class Child(Component):
        components = [SubChild]
        template = """<p><SubChild /></p>"""

    class Parent(Component):
        components = [Child(name="George")]
        template = """<div><George /></div>"""

    co = Parent(lorem="ipsum")
    html = co.render()
    assert html == "<div><p><span>ipsum</span></p></div>"


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
    assert co.collect_css() == [
        "parent.css",
        "/static/common/parent.css",
        "child.css",
    ]
    assert co.collect_js() == [
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

    result = co.render_css()
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

    result = co.render_js()
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

    result = co.render_assets()
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

    result = co.render_css()
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

    result = co.render_js()
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

    result = co.render_js(module=False, defer=True)
    expected = "\n".join(
        [
            '<script src="/assets/parent.js" defer></script>',
            '<script src="/assets/child.js" defer></script>',
            '<script src="https://example.com/child.js" defer></script>',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected

    result = co.render_js(module=False, defer=False)
    expected = "\n".join(
        [
            '<script src="/assets/parent.js"></script>',
            '<script src="/assets/child.js"></script>',
            '<script src="https://example.com/child.js"></script>',
        ]
    )
    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected


def test_render_assets_in_layout():
    class Layout(Component):
        css = ("layout.css",)
        js = ("layout.js", "https://example.com/layout.js")
        template = """{{ _assets.render() }}\n<div>{{ _content }}</div>"""

    class Main(Component):
        css = ("main.css", "/static/common/main.css")
        js = ("main.js",)
        components = [Layout]
        template = """<Layout>Hello</Layout>"""

    co = Main()
    result = co.render()
    expected = "\n".join(
        [
            '<link rel="stylesheet" href="/static/main.css">',
            '<link rel="stylesheet" href="/static/common/main.css">',
            '<link rel="stylesheet" href="/static/layout.css">',
            '<script type="module" src="/static/main.js"></script>',
            '<script type="module" src="/static/layout.js"></script>',
            '<script type="module" src="https://example.com/layout.js"></script>',
            "<div>Hello</div>",
        ]
    )

    print(f"-- Result --\n{result}")
    print(f"-- Expected --\n{expected}")
    assert result == expected
