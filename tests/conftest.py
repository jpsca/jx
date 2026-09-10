"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import os
import re

import pytest


@pytest.fixture()
def folder(tmp_path):
    d = tmp_path / "views"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Differential oracle
#
# With JX_DIFF=1, every template parsed anywhere in the suite is also parsed by
# the frozen regex parser and the two results compared. The test suite builds
# ~200 templates on the fly, so this turns all of them into a corpus for free.
# ---------------------------------------------------------------------------

RX_MACRO = re.compile(r"_jx_fill_(\d+)")

# Inputs where the two parsers are *meant* to disagree, because the frozen one
# is wrong. Each entry needs a reason and a test pinning the correct behavior.
KNOWN_DIVERGENCES = {
    "</Card>": (
        "the regex parser only ever matched opening tags, so a closing tag with "
        "nothing to close passed through as literal text; "
        "see test_stray_closing_tag_is_an_error"
    ),
    "bar={{ oops": (
        "the regex parser only looked at {{ }} inside a tag's attributes, so an "
        "unclosed one in plain text passed through to fail later inside Jinja; "
        "see test_unclosed_expr_block_raises"
    ),
    "{% raw %}<Card />{%+ endraw %}": (
        "the regex parser did not recognize `{%+ endraw %}` as a terminator, so "
        "it kept scanning and turned the tag inside the raw block into a render "
        "call; Jinja emits it literally, and so does the lexer now; "
        "see test_token_kinds"
    ),
    r'<Foo title="say \"hello\"" />': (
        "the regex parser cut the value at the escaped quote and emitted an "
        "unterminated Python string; see test_escaped_quotes_in_tag_attrs"
    ),
}


RX_TWO_CALL_EMPTY = re.compile(r"""_get\(("[^"]*"|'[^']*')\)\.render\(\)""")
RX_TWO_CALL = re.compile(r"""_get\(("[^"]*"|'[^']*')\)\.render\(""")


def canonical(source: str) -> str:
    """
    Renumber the generated fill macros by order of first appearance, and put
    both parsers on the same component-call convention.

    The two parsers walk the tree in opposite directions, so they hand out
    different numbers to the same macros. The numbers are arbitrary; what must
    match is that each definition lines up with its use.

    The frozen parser still emits `_get("X").render(...)`, the two-call form
    the emitter replaced with a single `_render("X", ...)`. That is a codegen
    change, not a parsing one, so it is normalized away here rather than by
    editing the reference.
    """
    source = RX_TWO_CALL_EMPTY.sub(r"_render(\1)", source)
    source = RX_TWO_CALL.sub(r"_render(\1, ", source)

    mapping: dict[str, str] = {}

    def _sub(match: re.Match) -> str:
        key = match.group(1)
        if key not in mapping:
            mapping[key] = str(len(mapping) + 1)
        return f"_jx_fill_{mapping[key]}"

    return RX_MACRO.sub(_sub, source)


def _outcome(parse):
    try:
        source, slots = parse()
    except Exception as err:
        return ("raised", type(err).__name__)
    return ("ok", canonical(source), slots)


def _meta_outcome(call):
    try:
        meta = call()
    except Exception as err:
        return ("raised", type(err).__name__)
    return (
        "ok",
        meta.required,
        meta.optional,
        meta.imports,
        meta.css,
        meta.js,
    )


@pytest.fixture(autouse=True)
def _differential(monkeypatch):
    if os.environ.get("JX_DIFF") != "1":
        yield
        return

    import jx.catalog
    import jx.meta
    import jx.parser
    import jx.tools

    from ._legacy_parser import LegacyParser

    original = jx.parser.JxParser.parse

    def checked(self, *, validate_tags: bool = True):
        # Exactly one call: the parser carries per-instance state (the fill
        # macro counter), so parsing twice would not give the same answer.
        failure = None
        result = None
        try:
            result = original(self, validate_tags=validate_tags)
            new = ("ok", canonical(result[0]), result[1])
        except Exception as err:
            failure = err
            new = ("raised", type(err).__name__)

        if self.source.strip() in KNOWN_DIVERGENCES:
            if failure is not None:
                raise failure
            return result

        legacy = LegacyParser(
            name=self.name, source=self.source, components=self.components
        )
        old = _outcome(lambda: legacy.parse(validate_tags=validate_tags))

        if new != old:
            raise AssertionError(
                "differential mismatch for "
                f"{self.name!r}\n--- source ---\n{self.source}"
                f"\n--- legacy ---\n{old}\n--- new ---\n{new}"
            )

        if failure is not None:
            raise failure
        return result

    monkeypatch.setattr(jx.parser.JxParser, "parse", checked)

    from ._legacy_meta import legacy_extract_metadata

    original_meta = jx.meta.extract_metadata

    def checked_meta(source, base_path, fullpath):
        failure = None
        result = None
        try:
            result = original_meta(source, base_path, fullpath)
            new = _meta_outcome(lambda: result)
        except Exception as err:
            failure = err
            new = ("raised", type(err).__name__)

        old = _meta_outcome(
            lambda: legacy_extract_metadata(source, base_path, fullpath)
        )
        if new != old:
            raise AssertionError(
                f"metadata differential mismatch\n--- source ---\n{source}"
                f"\n--- legacy ---\n{old}\n--- new ---\n{new}"
            )

        if failure is not None:
            raise failure
        return result

    monkeypatch.setattr(jx.meta, "extract_metadata", checked_meta)
    # `catalog` and `tools` imported the name directly, so rebind it there too.
    monkeypatch.setattr(jx.catalog, "extract_metadata", checked_meta)
    monkeypatch.setattr(jx.tools, "extract_metadata", checked_meta)
    yield
