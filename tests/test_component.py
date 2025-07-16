import pytest

from jx import Component, MissingRequiredArgument, TemplateSyntaxError

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

        def init(self):
            pass

    co = Meh()
    assert co.template
    assert co.template == Meh.template
    assert co.required == ()
    assert co.optional == {}


def test_parse_signature():
    class Button(Component):
        template = """<button id="{{ bid }}">{{ text }}</button>"""

        def init(self, bid, text="Click me!"):
            return {"bid": bid, "text": text}

    co = Button()
    assert co.required == ("bid",)
    assert co.optional == {"text": "Click me!"}


def test_render_exact():
    class Button(Component):
        template = """<button id="{{ bid }}">{{ text }}</button>"""

        def init(self, bid, text="Click me!"):
            return {"bid": bid, "text": text}

    co = Button()
    assert co.template
    assert co.template == Button.template
    html = co.render(bid="btn1", text="Submit")
    assert html == '<button id="btn1">Submit</button>'


def test_missing_required():
    class Button(Component):
        template = """<button id="{{ bid }}">{{ text }}</button>"""

        def init(self, bid, text="Click me!"):
            return {"bid": bid, "text": text}

    co = Button()
    assert co.template
    assert co.template == Button.template
    with pytest.raises(MissingRequiredArgument, match="`Button` component requires a `bid` argument"):
        co.render(text="Submit")


def test_render_derived_data():
    class Button(Component):
        template = """<button class="{{ class }}">{{ text }}</button>"""

        def init(self, var="primary", text="Click me!"):
            return {
                "text": text,
                "class": f"btn btn-{var}",
            }

    co = Button()
    html = co.render(text="Submit")
    assert html == '<button class="btn btn-primary">Submit</button>'


def test_render_extra():
    class Button(Component):
        template = """<button {{ _attrs.render() }}>{{ text }}</button>"""

        def init(self, text="Click me!"):
            return {"text": text}

    co = Button()
    args = {"class": "btn btn-primary", "disabled": True, "text": "Submit"}
    html = co.render(**args)
    assert html == '<button class="btn btn-primary" disabled>Submit</button>'


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

    with pytest.raises(TypeError, match="`Child`.*"):
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
    assert html == '<div><span><button class="btn btn-primary">Hello</button></span></div>'


def test_content_returned():
    class Child(Component):
        template = """<span>{{ _content }}</span>"""

        def init(self):
            return {"_content": self._content() * 2}

    class Parent(Component):
        components = [Child]
        template = """<div><Child>Hello</Child></div>"""

    co = Parent()
    html = co.render()
    assert html == "<div><span>HelloHello</span></div>"


def test_attrs_modification():
    class Child(Component):
        template = """<button {{ _attrs.render() }}>{{ _content }}</button>"""

        def init(self, var="primary"):
            self._attrs.add_class(f"btn-{var}")
            return {}

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

        def init(self, text: str):
            return {"text": text}

    class Parent(Component):
        components = [Child]
        template = """<div><Child :text="text * 2" /></div>"""

        def init(self, text: str):
            return {"text": text}

    co = Parent()
    html = co.render(text="Hello")
    assert html == "<div><span>HelloHello</span></div>"


def test_jinja_expr():
    class Child(Component):
        template = """<span>{{ text }}</span>"""

        def init(self, text: str):
            return {"text": text}

    class Parent(Component):
        components = [Child]
        template = """<div><Child text={{text * 2}} /></div>"""

        def init(self, text: str):
            return {"text": text}

    co = Parent()
    html = co.render(text="Hello")
    assert html == "<div><span>HelloHello</span></div>"
