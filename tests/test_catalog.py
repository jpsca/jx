"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import jinja2
import pytest

from jx import Catalog, ComponentNotFoundError, FileEncodingError


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

    with pytest.raises(ComponentNotFoundError, match="Component not found: a.jinja"):
        catalog.render("a.jinja")

    with pytest.raises(ComponentNotFoundError, match="Component not found: b.jinja"):
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

    with pytest.raises(ComponentNotFoundError, match="Component not found: unknown.jinja"):
        catalog.get_signature("unknown.jinja")


def test_file_encoding_error(folder):
    # Write invalid UTF-8 bytes (Latin-1 encoded text)
    (folder / "bad.jinja").write_bytes(b"<div>\xe9\xe8\xe0</div>")

    catalog = Catalog()
    catalog.add_folder(folder, preload=False)

    with pytest.raises(FileEncodingError, match="Cannot read .*/bad.jinja: not valid UTF-8"):
        catalog.render("bad.jinja")


# ---- Asset folder / package tests ----


def test_add_folder_with_assets(tmp_path):
    components = tmp_path / "components"
    components.mkdir()
    (components / "a.jinja").write_text("A")

    assets = tmp_path / "assets"
    assets.mkdir()

    catalog = Catalog()
    catalog.add_folder(components, prefix="ui", assets=assets)

    assert catalog.get_assets_folder("ui") == assets.resolve()
    assert "@ui/a.jinja" in catalog.components


def test_get_assets_folder_none(tmp_path):
    components = tmp_path / "components"
    components.mkdir()
    (components / "a.jinja").write_text("A")

    catalog = Catalog()
    catalog.add_folder(components, prefix="ui")

    assert catalog.get_assets_folder("ui") is None
    assert catalog.get_assets_folder("nonexistent") is None


def test_add_package(tmp_path):
    """add_package reads JX_COMPONENTS and JX_ASSETS from a module."""
    import types

    components = tmp_path / "pkg_components"
    components.mkdir()
    (components / "btn.jinja").write_text("<button />")

    assets = tmp_path / "pkg_assets"
    assets.mkdir()

    # Create a fake module with JX_COMPONENTS and JX_ASSETS
    fake_mod = types.ModuleType("fake_ui_kit")
    fake_mod.JX_COMPONENTS = components
    fake_mod.JX_ASSETS = assets

    import sys
    sys.modules["fake_ui_kit"] = fake_mod
    try:
        catalog = Catalog()
        catalog.add_package("fake_ui_kit", prefix="ui")

        assert "@ui/btn.jinja" in catalog.components
        assert catalog.get_assets_folder("ui") == assets.resolve()
    finally:
        del sys.modules["fake_ui_kit"]


def test_add_package_no_jx_components(tmp_path):
    """add_package raises ValueError if JX_COMPONENTS is missing."""
    import types

    fake_mod = types.ModuleType("fake_empty")
    import sys
    sys.modules["fake_empty"] = fake_mod
    try:
        catalog = Catalog()
        with pytest.raises(ValueError, match="JX_COMPONENTS"):
            catalog.add_package("fake_empty", prefix="x")
    finally:
        del sys.modules["fake_empty"]


def test_add_package_no_assets(tmp_path):
    """add_package works when JX_ASSETS is not set (assets=None)."""
    import types

    components = tmp_path / "pkg_components"
    components.mkdir()
    (components / "a.jinja").write_text("A")

    fake_mod = types.ModuleType("fake_no_assets")
    fake_mod.JX_COMPONENTS = components

    import sys
    sys.modules["fake_no_assets"] = fake_mod
    try:
        catalog = Catalog()
        catalog.add_package("fake_no_assets", prefix="na")

        assert "@na/a.jinja" in catalog.components
        assert catalog.get_assets_folder("na") is None
    finally:
        del sys.modules["fake_no_assets"]


def test_collect_assets(tmp_path):
    """collect_assets copies files from assets dirs to output."""
    components = tmp_path / "components"
    components.mkdir()
    (components / "a.jinja").write_text("A")

    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "button.css").write_text(".btn {}")
    sub = assets / "sub"
    sub.mkdir()
    (sub / "card.css").write_text(".card {}")

    output = tmp_path / "output"

    catalog = Catalog()
    catalog.add_folder(components, prefix="ui", assets=assets)
    collected = catalog.collect_assets(output)

    assert len(collected) == 2
    prefixes = [c[0] for c in collected]
    assert all(p == "ui" for p in prefixes)

    assert (output / "ui" / "button.css").read_text() == ".btn {}"
    assert (output / "ui" / "sub" / "card.css").read_text() == ".card {}"


def test_collect_assets_multiple_prefixes(tmp_path):
    """collect_assets handles multiple prefixes."""
    comp1 = tmp_path / "comp1"
    comp1.mkdir()
    (comp1 / "a.jinja").write_text("A")

    assets1 = tmp_path / "assets1"
    assets1.mkdir()
    (assets1 / "a.css").write_text("a")

    comp2 = tmp_path / "comp2"
    comp2.mkdir()
    (comp2 / "b.jinja").write_text("B")

    assets2 = tmp_path / "assets2"
    assets2.mkdir()
    (assets2 / "b.css").write_text("b")

    output = tmp_path / "output"

    catalog = Catalog()
    catalog.add_folder(comp1, prefix="one", assets=assets1)
    catalog.add_folder(comp2, prefix="two", assets=assets2)
    catalog.collect_assets(output)

    assert (output / "one" / "a.css").read_text() == "a"
    assert (output / "two" / "b.css").read_text() == "b"


def test_assets_without_prefix_raises(tmp_path):
    components = tmp_path / "components"
    components.mkdir()
    (components / "a.jinja").write_text("A")

    assets = tmp_path / "assets"
    assets.mkdir()

    catalog = Catalog()
    with pytest.raises(ValueError, match="Cannot register assets folder without a prefix"):
        catalog.add_folder(components, assets=assets)


def test_render(folder):
    (folder / "hello.jinja").write_text("{#def name #}\n<p>Hello {{ name }}</p>")

    catalog = Catalog(folder)
    html = catalog.render("hello.jinja", name="World")

    assert "<p>Hello World</p>" in html


def test_render_string():
    catalog = Catalog()
    html = catalog.render_string("{#def x #}\n<b>{{ x }}</b>", x="hi")

    assert "<b>hi</b>" in html


def test_auto_reload_false_cache(folder):
    (folder / "a.jinja").write_text("<p>cached</p>")

    catalog = Catalog(folder, auto_reload=False)
    # First call compiles; second call returns cached code
    cdata1 = catalog.get_component_data("a.jinja")
    cdata2 = catalog.get_component_data("a.jinja")

    assert cdata1 is cdata2
    assert cdata1.code is not None


def test_asset_resolver_invoked(tmp_path):
    components = tmp_path / "components"
    components.mkdir()
    (components / "btn.jinja").write_text(
        '{#css "btn.css" #}\n<button>click</button>\n{{ assets.render_css() }}'
    )

    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "btn.css").write_text(".btn{}")

    catalog = Catalog(
        asset_resolver=lambda url, prefix: f"/pkg/{prefix}/{url}",
    )
    catalog.add_folder(components, prefix="ui", assets=assets)
    html = catalog.render("@ui/btn.jinja")

    assert "/pkg/ui/btn.css" in html


def test_asset_resolver_skipped_without_assets_folder(tmp_path):
    """Resolver is not called for prefixes without a registered assets folder."""
    components = tmp_path / "components"
    components.mkdir()
    (components / "btn.jinja").write_text(
        '{#css "btn.css" #}\n<button />\n{{ assets.render_css() }}'
    )

    catalog = Catalog(
        asset_resolver=lambda url, prefix: f"/pkg/{prefix}/{url}",
    )
    # No assets= argument, so resolver should NOT transform the URL
    catalog.add_folder(components, prefix="ui")
    html = catalog.render("@ui/btn.jinja")

    assert "btn.css" in html
    assert "/pkg/" not in html


def test_auto_reload_recompiles_on_change(folder):
    comp = folder / "a.jinja"
    comp.write_text("<p>v1</p>")

    catalog = Catalog(folder, auto_reload=True)
    html1 = catalog.render("a.jinja")
    assert "v1" in html1

    # Modify the file (ensure mtime changes)
    import time
    time.sleep(0.05)
    comp.write_text("<p>v2</p>")

    html2 = catalog.render("a.jinja")
    assert "v2" in html2
