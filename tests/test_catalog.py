"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import jinja2
import pytest

from jx import Catalog, ImportError


def test_add_folder(folder):
    (folder / "a.jinja").write_text("AAAAA")
    (folder / "b.jinja").write_text("BBBBB")

    catalog = Catalog(folder)

    assert "a.jinja" in catalog.components
    assert "b.jinja" in catalog.components

    assert catalog.components["a.jinja"].base_path == folder
    assert catalog.components["a.jinja"].path == folder / "a.jinja"
    assert catalog.components["a.jinja"].mtime > 0
    assert catalog.components["a.jinja"].code is not None

    assert catalog.components["b.jinja"].base_path == folder
    assert catalog.components["b.jinja"].path == folder / "b.jinja"
    assert catalog.components["b.jinja"].mtime > 0
    assert catalog.components["b.jinja"].code is not None


def test_add_folder_no_preload(folder):
    (folder / "a.jinja").write_text("AAAAA")
    (folder / "b.jinja").write_text("BBBBB")

    catalog = Catalog()
    catalog.add_folder(folder, preload=False)

    assert "a.jinja" in catalog.components
    assert "b.jinja" in catalog.components

    assert catalog.components["a.jinja"].base_path == folder
    assert catalog.components["a.jinja"].path == folder / "a.jinja"
    assert catalog.components["a.jinja"].mtime > 0
    assert catalog.components["a.jinja"].code is None

    assert catalog.components["b.jinja"].base_path == folder
    assert catalog.components["b.jinja"].path == folder / "b.jinja"
    assert catalog.components["b.jinja"].mtime > 0
    assert catalog.components["b.jinja"].code is None


def test_add_folder_nested(tmp_path):
    folder = tmp_path / "views"
    nested = folder / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (nested / "d.jinja").write_text("hello")

    catalog = Catalog(folder)

    assert catalog.components.keys() == {"a/b/c/d.jinja"}


def test_add_folder_with_prefix(tmp_path):
    folder1 = tmp_path / "views1"
    folder1.mkdir()
    (folder1 / "a.jinja").write_text("AAAAA")

    folder2 = tmp_path / "views2"
    folder2.mkdir()
    (folder2 / "b.jinja").write_text("BBBBB")

    catalog = Catalog()
    catalog.add_folder(folder1)
    catalog.add_folder(folder2, prefix="bla")

    assert "a.jinja" in catalog.components
    assert "@bla/b.jinja" in catalog.components

    assert catalog.components["a.jinja"].base_path == folder1
    assert catalog.components["a.jinja"].path == folder1 / "a.jinja"
    assert catalog.components["a.jinja"].mtime > 0
    assert catalog.components["a.jinja"].code is not None

    assert catalog.components["@bla/b.jinja"].base_path == folder2
    assert catalog.components["@bla/b.jinja"].path == folder2 / "b.jinja"
    assert catalog.components["@bla/b.jinja"].mtime > 0
    assert catalog.components["@bla/b.jinja"].code is not None


def test_dot_in_prefix(tmp_path):
    folder = tmp_path / "views"
    folder.mkdir()
    (folder / "a.jinja").write_text("AAAAA")

    catalog = Catalog()
    catalog.add_folder(folder, prefix="ui.forms")

    assert "@ui.forms/a.jinja" in catalog.components

    assert catalog.components["@ui.forms/a.jinja"].base_path == folder
    assert catalog.components["@ui.forms/a.jinja"].path == folder / "a.jinja"
    assert catalog.components["@ui.forms/a.jinja"].mtime > 0
    assert catalog.components["@ui.forms/a.jinja"].code is not None


def test_add_same_folder_many_times(folder):
    (folder / "a.jinja").write_text("AAAAA")
    (folder / "b.jinja").write_text("BBBBB")

    catalog = Catalog()
    catalog.add_folder(folder)
    catalog.add_folder(folder)

    assert catalog.components.keys() == {"a.jinja", "b.jinja"}


def test_overwrite_relpath(tmp_path):
    folder1 = tmp_path / "views1"
    folder1.mkdir()
    (folder1 / "a.jinja").write_text("folder1")

    folder2 = tmp_path / "views2"
    folder2.mkdir()
    (folder2 / "a.jinja").write_text("folder2")

    catalog = Catalog()
    catalog.add_folder(folder1)
    catalog.add_folder(folder2)

    assert catalog.components.keys() == {"a.jinja"}
    assert catalog.components["a.jinja"].base_path == folder1


def test_add_same_folder_with_prefix(folder):
    (folder / "a.jinja").write_text("AAAAA")

    catalog = Catalog()
    catalog.add_folder(folder)
    catalog.add_folder(folder, prefix="copy")

    assert catalog.components.keys() == {"a.jinja", "@copy/a.jinja"}
    assert catalog.components["a.jinja"].base_path == folder
    assert catalog.components["@copy/a.jinja"].base_path == folder


def test_unknown_component(folder):

    catalog = Catalog()
    catalog.add_folder(folder)

    with pytest.raises(ImportError, match="Component not found: a.jinja"):
        catalog.render("a.jinja")

    with pytest.raises(ImportError, match="Component not found: b.jinja"):
        catalog.get_component("b.jinja")


def test_reuse_jinja_env():
    jinja_env = jinja2.Environment()
    jinja_env.filters["custom_filter"] = lambda x: f"Filtered: {x}"
    jinja_env.globals["custom_global"] = "Global Value"
    catalog = Catalog(jinja_env=jinja_env)

    assert catalog.jinja_env.filters["custom_filter"]("Test") == "Filtered: Test"
    assert catalog.jinja_env.globals["custom_global"] == "Global Value"


def test_list_components(folder):
    (folder / "button.jinja").write_text("<button>Click</button>")
    (folder / "card.jinja").write_text("<div>Card</div>")

    catalog = Catalog(folder)
    components = catalog.list_components()

    assert isinstance(components, list)
    assert set(components) == {"button.jinja", "card.jinja"}


def test_list_components_empty():
    catalog = Catalog()
    components = catalog.list_components()

    assert components == []


def test_list_components_with_prefix(tmp_path):
    folder1 = tmp_path / "views1"
    folder1.mkdir()
    (folder1 / "a.jinja").write_text("A")

    folder2 = tmp_path / "views2"
    folder2.mkdir()
    (folder2 / "b.jinja").write_text("B")

    catalog = Catalog()
    catalog.add_folder(folder1)
    catalog.add_folder(folder2, prefix="ui")

    components = catalog.list_components()
    assert set(components) == {"a.jinja", "@ui/b.jinja"}


def test_get_signature(folder):
    (folder / "button.jinja").write_text(
        '{#def label, size="md", disabled=False #}\n'
        '{#css "/static/button.css" #}\n'
        '{#js "/static/button.js" #}\n'
        "<button>{{ label }}</button>"
    )

    catalog = Catalog(folder)
    sig = catalog.get_signature("button.jinja")

    assert sig["required"] == {"label": None}
    assert sig["optional"] == {"size": ("md", None), "disabled": (False, None)}
    assert sig["slots"] == ()
    assert sig["css"] == ("/static/button.css",)
    assert sig["js"] == ("/static/button.js",)


def test_get_signature_with_slots(folder):
    (folder / "card.jinja").write_text(
        "{#def title #}\n"
        "<div>\n"
        "  <h2>{{ title }}</h2>\n"
        "  {% slot content %}Default{% endslot %}\n"
        "  {% slot footer %}{% endslot %}\n"
        "</div>"
    )

    catalog = Catalog(folder)
    sig = catalog.get_signature("card.jinja")

    assert sig["required"] == {"title": None}
    assert sig["optional"] == {}
    assert sig["slots"] == ("content", "footer")
    assert sig["css"] == ()
    assert sig["js"] == ()


def test_get_signature_no_metadata(folder):
    (folder / "simple.jinja").write_text("<div>Simple</div>")

    catalog = Catalog(folder)
    sig = catalog.get_signature("simple.jinja")

    assert sig["required"] == {}
    assert sig["optional"] == {}
    assert sig["slots"] == ()
    assert sig["css"] == ()
    assert sig["js"] == ()


def test_get_signature_unknown_component(folder):
    catalog = Catalog(folder)

    with pytest.raises(ImportError, match="Component not found: unknown.jinja"):
        catalog.get_signature("unknown.jinja")
