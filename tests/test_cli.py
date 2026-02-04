"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""


from jx.cli import check, find_component_tags, suggest_component, suggest_tag


def test_find_component_tags():
    source = """
<div>
  <Button label="Click" />
  <Card title="Hello">
    <CloseBtn />
  </Card>
</div>
"""
    tags = find_component_tags(source)
    assert ("Button", 3) in tags
    assert ("Card", 4) in tags
    assert ("CloseBtn", 5) in tags


def test_suggest_tag():
    imported = {"Button", "Card", "Layout"}
    all_components = {"button.jinja", "card.jinja", "layout.jinja"}

    assert suggest_tag("Buttn", imported, all_components) == "Button"
    assert suggest_tag("Crad", imported, all_components) == "Card"
    assert suggest_tag("XYZ123", imported, all_components) is None


def test_check_valid_components(folder):
    (folder / "button.jinja").write_text(
        "{#def label #}\n<button>{{ label }}</button>"
    )
    (folder / "card.jinja").write_text(
        '{#import "button.jinja" as Button #}\n<div><Button label="OK" /></div>'
    )

    exit_code = check([folder])
    assert exit_code == 0


def test_check_unknown_component(folder, capsys):
    (folder / "button.jinja").write_text("<button>Click</button>")
    (folder / "card.jinja").write_text("<div><Buttn /></div>")

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Unknown component 'Buttn'" in captured.out
    assert "did you mean 'Button'?" in captured.out


def test_check_unknown_import(folder, capsys):
    (folder / "button.jinja").write_text("<button>Click</button>")
    (folder / "card.jinja").write_text(
        '{#import "buton.jinja" as Button #}\n<Button />'
    )

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Unknown import 'buton.jinja'" in captured.out
    assert "did you mean 'button.jinja'?" in captured.out


def test_check_not_imported(folder, capsys):
    (folder / "button.jinja").write_text("<button>Click</button>")
    (folder / "card.jinja").write_text("<div><Button /></div>")

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Component 'Button' used but not imported" in captured.out


def test_check_single_file(folder, capsys):
    """Test checking a single file instead of a directory."""
    file_path = folder / "button.jinja"
    file_path.write_text("{#def label #}\n<button>{{ label }}</button>")

    exit_code = check([file_path])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "button.jinja - OK" in captured.out


def test_check_no_components(tmp_path, capsys):
    """Test checking an empty directory with no components."""
    empty_folder = tmp_path / "empty"
    empty_folder.mkdir()

    exit_code = check([empty_folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "No components found" in captured.out


def test_check_invalid_utf8(folder, capsys):
    """Test checking a component with invalid UTF-8 encoding."""
    file_path = folder / "broken.jinja"
    file_path.write_bytes(b"<div>\xff\xfe invalid</div>")

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "broken.jinja - Not valid UTF-8" in captured.out


def test_check_invalid_metadata(folder, capsys):
    """Test checking a component with invalid metadata syntax."""
    (folder / "broken.jinja").write_text("{#def $invalid #}\n<div>test</div>")

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "broken.jinja -" in captured.out


def test_check_unknown_import_no_suggestion(folder, capsys):
    """Test unknown import with no similar component to suggest."""
    (folder / "card.jinja").write_text(
        '{#import "xyzabc123.jinja" as Thing #}\n<Thing />'
    )

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Unknown import 'xyzabc123.jinja'" in captured.out
    assert "did you mean" not in captured.out


def test_check_unknown_component_no_suggestion(folder, capsys):
    """Test unknown component tag with no similar tag to suggest."""
    (folder / "card.jinja").write_text("<div><Xyzabc123 /></div>")

    exit_code = check([folder])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Unknown component 'Xyzabc123'" in captured.out
    assert "did you mean" not in captured.out


def test_suggest_component():
    """Test component path suggestion."""
    all_components = {"button.jinja", "card.jinja", "layout.jinja"}

    assert suggest_component("buton.jinja", all_components) == "button.jinja"
    assert suggest_component("xyzabc123.jinja", all_components) is None


def test_check_nonexistent_path(tmp_path, capsys):
    """Test checking a path that doesn't exist (neither file nor directory)."""
    nonexistent = tmp_path / "does_not_exist"

    exit_code = check([nonexistent])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "No components found" in captured.out
