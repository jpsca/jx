"""
Jx | Copyright (c) Juan-Pablo Scaletti

Differential tests: the parser must agree with the frozen regex parser
(`tests/_legacy_parser.py`) on every input.

The rest of the suite is covered by the `JX_DIFF=1` hook in `conftest.py`, which
compares every template any test builds. This module adds the `.jx` files that
live on disk plus inputs chosen to be awkward.
"""

from pathlib import Path

import pytest

from jx.meta import extract_metadata
from jx.parser import JxParser

from ._legacy_parser import LegacyParser
from .conftest import KNOWN_DIVERGENCES, canonical


REPO = Path(__file__).parent.parent
DOCS_VIEWS = sorted((REPO / "docs" / "views").glob("*.jx"))


def compare(name: str, source: str, components: list[str], *, validate_tags: bool = True):
    reason = KNOWN_DIVERGENCES.get(source.strip())
    if reason:
        pytest.skip(f"deliberate divergence: {reason}")

    def run(parser):
        try:
            src, slots = parser.parse(validate_tags=validate_tags)
        except Exception as err:
            return ("raised", type(err).__name__, str(err))
        return ("ok", canonical(src), slots)

    new = run(JxParser(name=name, source=source, components=components))
    old = run(LegacyParser(name=name, source=source, components=components))

    if new[0] == "raised" and old[0] == "raised":
        # Both reject it. The message is allowed to improve.
        assert new[1] == old[1], f"{name}: different error type"
        return
    assert new == old, f"{name}: parsers disagree"


@pytest.mark.skipif(not DOCS_VIEWS, reason="no .jx files on disk")
@pytest.mark.parametrize("path", DOCS_VIEWS, ids=lambda p: p.name)
def test_docs_views(path):
    """The real templates that build the Jx documentation site."""
    source = path.read_text(encoding="utf-8")
    meta = extract_metadata(source, base_path=path.parent, fullpath=path)
    compare(path.name, source, list(meta.imports.keys()))


AWKWARD = {
    "empty": "",
    "text only": "just some text, no tags at all",
    "lone lt": "a < b and c > d",
    "lowercase tag": "<div class='x'>hello</div>",
    "tag lookalike in text": "use <Card /> like this",
    "self closing": "<Card />",
    "self closing no space": "<Card/>",
    "attr with slash": '<Card href="http://a/b" />',
    "attr with gt in string": '<Card label="a > b" />',
    "attr with lt in string": '<Card label="a < b" />',
    "expr attr with braces": '<Card data="{{ {\'a\': 1} }}" />',
    "expr attr with quotes": '<Card label="{{ x if y else \'a>b\' }}" />',
    "expr attr with rbrace in string": "<Card label={{ '}}' }} />",
    "flag attrs": "<Card green large />",
    "multiline attrs": '<Card\n  a="1"\n  b="2"\n>x</Card>',
    "nested same tag": "<Card><Card>inner</Card></Card>",
    "nested same tag siblings": "<Card><Card>a</Card><Card>b</Card></Card>",
    "nested self closing inside": "<Card><Card />after</Card>",
    "comment hides tag": "{# <Card /> #}<Card />",
    "raw hides tag": "{% raw %}<Card />{% endraw %}<Card />",
    "raw hides fill": "{% raw %}{% fill x %}{% endfill %}{% endraw %}",
    "empty raw": "{% raw %}{% endraw %}<Card />",
    "raw with dashes": "{%- raw -%}<Card />{%- endraw -%}",
    "raw with plus": "{% raw %}<Card />{%+ endraw %}",
    "raw hides a bare block start": "{% raw %}Use {% in a sentence{% endraw %}<Card />",
    "raw hides an unterminated quote": '{% raw %}{% "oops{% endraw %}<Card />',
    "slot basic": "{% slot header %}default{% endslot %}",
    "slot empty default": "{% slot header %}{% endslot %}",
    "slot strip": "{% slot header -%}  x  {%- endslot %}",
    "two slots": "{% slot a %}A{% endslot %}{% slot b %}B{% endslot %}",
    "fill basic": "<Card>{% fill a %}A{% endfill %}main</Card>",
    "fill only": "<Card>{% fill a %}A{% endfill %}</Card>",
    "fill empty": "<Card>{% fill a %}{% endfill %}main</Card>",
    "fill strip": "<Card>{% fill a -%} A {%- endfill %}main</Card>",
    "fills nested components": (
        "<Card>{% fill a %}<Card>{% fill b %}in{% endfill %}x</Card>{% endfill %}out</Card>"
    ),
    "fill inside for": "{% for i in x %}<Card>{% fill a %}{{ i }}{% endfill %}</Card>{% endfor %}",
    "component inside if": "{% if x %}<Card />{% endif %}",
    "expr with filter": '<Card title="{{ x | title }}" />',
    "expr with pipe in string": "<Card title=\"{{ 'a|b' }}\" />",
    "dotted tag name": "<Ui.Card />",
    "dashed attr": '<Card data-foo="1" />',
    "colon attr": '<Card :bind="x" />',
    "at attr": '<Card @click="go()" />',
    "unicode text": "<Card>ñandú 日本語 🎉</Card>",
    "crlf": '<Card\r\n  a="1"\r\n>x</Card>',
    "deep nesting": "<Card>" * 5 + "x" + "</Card>" * 5,
}

BROKEN = {
    "unclosed component": "<Card>never closed",
    "unknown component": "<Nope />",
    "unclosed quote": '<Card a="unterminated>x</Card>',
    "unclosed expr": "<Card a={{ x />",
    "stray close": "</Card>",
}


@pytest.mark.parametrize("name", list(AWKWARD), ids=list(AWKWARD))
def test_awkward_input(name):
    compare(name, AWKWARD[name], ["Card", "Ui.Card"])


@pytest.mark.parametrize("name", list(BROKEN), ids=list(BROKEN))
def test_broken_input(name):
    compare(name, BROKEN[name], ["Card"])
