"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

from jx.cli import check, find_component_tags, suggest_tag


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
