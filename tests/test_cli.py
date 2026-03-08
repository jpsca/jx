"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import sys
from unittest.mock import patch

import pytest

from jx import Catalog
from jx.cli import _is_file_path, load_catalog, main


def test_load_catalog_invalid_format(capsys):
    """Test load_catalog with invalid format (no colon)."""
    with pytest.raises(SystemExit) as exc_info:
        load_catalog("no_colon_here")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Invalid catalog path" in captured.out


def test_load_catalog_missing_module(capsys):
    """Test load_catalog with a module that doesn't exist."""
    with pytest.raises(SystemExit) as exc_info:
        load_catalog("nonexistent.module:catalog")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Could not import module" in captured.out


def test_load_catalog_missing_attribute(capsys):
    """Test load_catalog with a missing attribute."""
    with pytest.raises(SystemExit) as exc_info:
        load_catalog("jx:nonexistent_attr")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Could not resolve" in captured.out


def test_load_catalog_missing_nested_attribute(capsys):
    """Test load_catalog with a missing nested attribute."""
    with pytest.raises(SystemExit) as exc_info:
        load_catalog("jx:Catalog.nonexistent")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Could not resolve" in captured.out


def test_load_catalog_success():
    """Test load_catalog successfully imports a catalog."""
    catalog = load_catalog("jx:Catalog")
    assert catalog is Catalog


def test_load_catalog_dotted_attribute():
    """Test load_catalog with a dotted attribute path."""
    # jx.Catalog.__name__ is "Catalog" (a string)
    result = load_catalog("jx:Catalog.__name__")
    assert result == "Catalog"


# -- File path detection --


def test_is_file_path_with_slash():
    assert _is_file_path("docs/docs.py") is True


def test_is_file_path_with_py_extension():
    assert _is_file_path("setup.py") is True


def test_is_file_path_with_module_path():
    assert _is_file_path("myapp.setup") is False


# -- load_catalog from file path --


def test_load_catalog_file_path(tmp_path):
    """Test load_catalog with a file path instead of module path."""
    setup_file = tmp_path / "mysetup.py"
    setup_file.write_text(
        "from jx import Catalog\n"
        "catalog = Catalog()\n"
    )
    result = load_catalog(f"{setup_file}:catalog")
    assert isinstance(result, Catalog)


def test_load_catalog_file_path_nested_attr(tmp_path):
    """Test load_catalog with a file path and dotted attribute."""
    setup_file = tmp_path / "mysetup.py"
    setup_file.write_text(
        "from jx import Catalog\n"
        "class docs:\n"
        "    catalog = Catalog()\n"
    )
    result = load_catalog(f"{setup_file}:docs.catalog")
    assert isinstance(result, Catalog)


def test_load_catalog_file_path_not_found(capsys):
    """Test load_catalog with a file path that doesn't exist."""
    with pytest.raises(SystemExit) as exc_info:
        load_catalog("nonexistent/file.py:catalog")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.out


def test_load_catalog_file_path_missing_attr(tmp_path, capsys):
    """Test load_catalog with a file path but missing attribute."""
    setup_file = tmp_path / "mysetup.py"
    setup_file.write_text("x = 1\n")
    with pytest.raises(SystemExit) as exc_info:
        load_catalog(f"{setup_file}:catalog")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Could not resolve" in captured.out


def test_main_check_file_path(tmp_path, capsys):
    """Test main check subcommand with a file path argument."""
    folder = tmp_path / "components"
    folder.mkdir()
    (folder / "alert.jinja").write_text("<div>Alert</div>")

    setup_file = tmp_path / "mysetup.py"
    setup_file.write_text(
        f"from jx import Catalog\n"
        f"catalog = Catalog()\n"
        f"catalog.add_folder('{folder}', preload=False)\n"
    )

    with patch.object(sys, "argv", ["jx", "check", f"{setup_file}:catalog"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "alert.jinja - OK" in captured.out


def test_main_no_command(capsys):
    """Test main with no subcommand prints help and exits."""
    with patch.object(sys, "argv", ["jx"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_main_check(tmp_path, capsys):
    """Test main with check subcommand."""
    # Create a valid component
    folder = tmp_path / "components"
    folder.mkdir()
    (folder / "button.jinja").write_text("<button>Click</button>")

    # Create a module that exposes a catalog
    setup_file = tmp_path / "testsetup.py"
    setup_file.write_text(
        f"from jx import Catalog\n"
        f"catalog = Catalog()\n"
        f"catalog.add_folder('{folder}', preload=False)\n"
    )

    with patch.object(sys, "argv", ["jx", "check", "testsetup:catalog"]):
        sys.path.insert(0, str(tmp_path))
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        finally:
            sys.path.pop(0)
            sys.modules.pop("testsetup", None)

    captured = capsys.readouterr()
    assert "button.jinja - OK" in captured.out


def test_main_check_json(tmp_path, capsys):
    """Test main with check --format json."""
    folder = tmp_path / "components"
    folder.mkdir()
    (folder / "card.jinja").write_text("<div>OK</div>")

    setup_file = tmp_path / "testsetup2.py"
    setup_file.write_text(
        f"from jx import Catalog\n"
        f"catalog = Catalog()\n"
        f"catalog.add_folder('{folder}', preload=False)\n"
    )

    with patch.object(sys, "argv", ["jx", "check", "--format", "json", "testsetup2:catalog"]):
        sys.path.insert(0, str(tmp_path))
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        finally:
            sys.path.pop(0)
            sys.modules.pop("testsetup2", None)

    import json

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["checked"] == 1
    assert result["errors"] == []


def test_main_collect_assets(tmp_path, capsys):
    """Test main with collect_assets subcommand."""
    # Create component and asset folders
    comp_folder = tmp_path / "components"
    comp_folder.mkdir()
    (comp_folder / "widget.jinja").write_text("<div>widget</div>")

    assets_folder = tmp_path / "assets"
    assets_folder.mkdir()
    (assets_folder / "style.css").write_text("body { color: red; }")

    output_folder = tmp_path / "static"

    setup_file = tmp_path / "testsetup3.py"
    setup_file.write_text(
        f"from jx import Catalog\n"
        f"catalog = Catalog()\n"
        f"catalog.add_folder('{comp_folder}', prefix='ui', assets='{assets_folder}', preload=False)\n"
    )

    with patch.object(sys, "argv", ["jx", "collect_assets", "testsetup3:catalog", str(output_folder)]):
        sys.path.insert(0, str(tmp_path))
        try:
            main()
        finally:
            sys.path.pop(0)
            sys.modules.pop("testsetup3", None)

    captured = capsys.readouterr()
    assert "ui/style.css" in captured.out
    assert "1 file collected" in captured.out
    assert (output_folder / "ui" / "style.css").exists()


def test_main_collect_assets_multiple(tmp_path, capsys):
    """Test collect_assets with multiple files uses plural."""
    comp_folder = tmp_path / "components"
    comp_folder.mkdir()
    (comp_folder / "a.jinja").write_text("<div>a</div>")

    assets_folder = tmp_path / "assets"
    assets_folder.mkdir()
    (assets_folder / "a.css").write_text(".a {}")
    (assets_folder / "b.css").write_text(".b {}")

    output_folder = tmp_path / "static"

    setup_file = tmp_path / "testsetup4.py"
    setup_file.write_text(
        f"from jx import Catalog\n"
        f"catalog = Catalog()\n"
        f"catalog.add_folder('{comp_folder}', prefix='ui', assets='{assets_folder}', preload=False)\n"
    )

    with patch.object(sys, "argv", ["jx", "collect_assets", "testsetup4:catalog", str(output_folder)]):
        sys.path.insert(0, str(tmp_path))
        try:
            main()
        finally:
            sys.path.pop(0)
            sys.modules.pop("testsetup4", None)

    captured = capsys.readouterr()
    assert "2 files collected" in captured.out


def test_load_module_from_file_bad_spec(tmp_path, capsys):
    """Test _load_module_from_file with an unloadable file."""
    bad_file = tmp_path / "not_python.txt"
    bad_file.write_text("not a python file")
    from jx.cli import _load_module_from_file

    with pytest.raises(SystemExit) as exc_info:
        _load_module_from_file(str(bad_file))
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Cannot load module" in captured.out


def test_main_collect_assets_no_prefix(tmp_path, capsys):
    """Test collect_assets with no assets folders produces 0 files."""
    comp_folder = tmp_path / "components"
    comp_folder.mkdir()
    (comp_folder / "btn.jinja").write_text("<button />")

    output_folder = tmp_path / "static"

    setup_file = tmp_path / "testsetup5.py"
    setup_file.write_text(
        f"from jx import Catalog\n"
        f"catalog = Catalog()\n"
        f"catalog.add_folder('{comp_folder}', preload=False)\n"
    )

    with patch.object(sys, "argv", ["jx", "collect_assets", "testsetup5:catalog", str(output_folder)]):
        sys.path.insert(0, str(tmp_path))
        try:
            main()
        finally:
            sys.path.pop(0)
            sys.modules.pop("testsetup5", None)

    captured = capsys.readouterr()
    assert "0 files collected" in captured.out
