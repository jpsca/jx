"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import pytest

from jx import TemplateSyntaxError
from jx.parser import JxParser


VALID_DATA = (
    # Simple case
    (
        """<Foo bar="baz">content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"baz"}) -%}content{%- endcall %}""",
    ),
    # Self-closing tag
    (
        """<Alert type="success" message="Success!" />""",
        """{{ _get("Alert").render(**{"type":"success", "message":"Success!"}) }}""",
    ),
    # No attributes
    (
        """<Foo>content</Foo>""",
        """{% call(_slot="") _get("Foo").render() -%}content{%- endcall %}""",
    ),
    # No attributes, self-closing tag
    (
        """<Foo />""",
        """{{ _get("Foo").render() }}""",
    ),
    # Strings vs expressions
    (
        """<Foo bar="baz" lorem={{ ipsum }}>content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"baz", "lorem":ipsum}) -%}content{%- endcall %}""",
    ),
    # Single quotes
    (
        """<Foo bar='say "hello world"'>content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":'say "hello world"'}) -%}content{%- endcall %}""",
    ),
    (
        """<Foo bar="say 'hello world'">content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"say 'hello world'"}) -%}content{%- endcall %}""",
    ),
    # Braces inside quotes
    (
        """<Foo bar="say 'hello {{world}}'">content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"say 'hello {{world}}'"}) -%}content{%- endcall %}""",
    ),
    # Line breaks
    (
        """<Foo
          bar="baz"
          lorem="ipsum"
        >content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"baz", "lorem":"ipsum"}) -%}content{%- endcall %}""",
    ),
    # Line breaks, self-closing tag
    (
        """<Foo
          bar="baz"
          lorem="ipsum"
          green
        />""",
        """{{ _get("Foo").render(**{"bar":"baz", "lorem":"ipsum", "green":True}) }}""",
    ),
    # Python expression in attribute and boolean attributes
    (
        """<Foo bar={{ 42 + 4 }} green large>content</Foo>""",
        """{% call(_slot="") _get("Foo").render(**{"bar":42 + 4, "green":True, "large":True}) -%}content{%- endcall %}""",
    ),
    # `>` in expression
    (
        """<CloseBtn disabled={{ num > 4 }} />""",
        """{{ _get("CloseBtn").render(**{"disabled":num > 4}) }}""",
    ),
    # `>` in attribute value
    (
        """<CloseBtn data-closer-action="click->closer#close" />""",
        """{{ _get("CloseBtn").render(**{"data_closer_action":"click->closer#close"}) }}""",
    ),
    # Quotes inside expressions (should not break parsing)
    (
        """<Card title={{ items['key'] }} class="foo" />""",
        """{{ _get("Card").render(**{"title":items['key'], "class":"foo"}) }}""",
    ),
    (
        """<Card title={{ data["name"] }} />""",
        """{{ _get("Card").render(**{"title":data["name"]}) }}""",
    ),
    # Closing braces inside string literals within expressions
    (
        """<Card title={{ foo("}}") }} />""",
        """{{ _get("Card").render(**{"title":foo("}}")}) }}""",
    ),
    (
        """<Card title={{ foo('}}') }} />""",
        """{{ _get("Card").render(**{"title":foo('}}')}) }}""",
    ),
    (
        """<Card title={{ "it's }}" }} />""",
        """{{ _get("Card").render(**{"title":"it's }}"}) }}""",
    ),
    # Raw blocks
    (
        """<Foo bar="baz">content</Foo>
{% raw %}{{ a + b }}{% endraw %}
what""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"baz"}) -%}content{%- endcall %}
{% raw %}{{ a + b }}{% endraw %}
what""",
    ),
    # Raw blocks with HTML content (should not be escaped)
    (
        """<Foo bar="baz">content</Foo>
{% raw %}<div class="test">&amp;</div>{% endraw %}""",
        """{% call(_slot="") _get("Foo").render(**{"bar":"baz"}) -%}content{%- endcall %}
{% raw %}<div class="test">&amp;</div>{% endraw %}""",
    ),
)


@pytest.mark.parametrize("source, expected", VALID_DATA)
def test_process_valid_tags(source, expected):
    parser = JxParser(name="test", source=source, components=[])
    result, _ = parser.parse(validate_tags=False)
    print(result)
    assert result == expected


INVALID_DATA = (
    # Tag not closed
    (
        """<Foo bar="baz">content aslasals ls,als,as""",
        TemplateSyntaxError,
        "Unclosed component",
    ),
    # String attribute not closed
    (
        """<Foo bar="baz>content lorem ipsumsdsd""",
        TemplateSyntaxError,
        "Syntax error",
    ),
    # Expression not closed
    (
        """<Foo bar={{ 42 + 4>content</Foo>""",
        TemplateSyntaxError,
        "Syntax error",
    ),
    # Unmatched braces
    (
        """<Foo bar={{ 42 + {{ 4 }}>content</Foo>""",
        TemplateSyntaxError,
        "Unmatched braces",
    ),
    (
        """<Foo bar=42 + 4}}>content</Foo>""",
        TemplateSyntaxError,
        "Unmatched braces",
    ),
)


@pytest.mark.parametrize("source, exception, match", INVALID_DATA)
def test_process_invalid_tags(source, exception, match):
    parser = JxParser(name="test", source=source, components=[])
    with pytest.raises(exception, match=f".*{match}.*"):
        parser.parse(validate_tags=False)


def test_process_nested_same_tag():
    source = """
<Card class="card">
  WTF
  <Card class="card-header">abc</Card>
  <Card class="card-body">
    <div><Card>Text</Card></div>
  </Card>
</Card>
    """
    expected = """
{% call(_slot="") _get("Card").render(**{"class":"card"}) -%}
  WTF
  {% call(_slot="") _get("Card").render(**{"class":"card-header"}) -%}abc{%- endcall %}
  {% call(_slot="") _get("Card").render(**{"class":"card-body"}) -%}
    <div>{% call(_slot="") _get("Card").render() -%}Text{%- endcall %}</div>
  {%- endcall %}
{%- endcall %}
"""
    parser = JxParser(name="test", source=source, components=[])
    result, _ = parser.parse(validate_tags=False)
    print(result)
    assert result.strip() == expected.strip()


def test_nested_same_tag_with_content_between():
    """Content between nested same-name closing tags is preserved."""
    source = """<Card>a<Card>b</Card>c</Card>"""
    expected = (
        '{% call(_slot="") _get("Card").render() -%}'
        'a{% call(_slot="") _get("Card").render() -%}b{%- endcall %}c'
        '{%- endcall %}'
    )
    parser = JxParser(name="test", source=source, components=[])
    result, _ = parser.parse(validate_tags=False)
    assert result == expected


def test_nested_same_tag_self_closing_does_not_increase_depth():
    """Self-closing same-name tags inside a block don't affect nesting."""
    source = """<Card>a<Card />b</Card>"""
    expected = (
        '{% call(_slot="") _get("Card").render() -%}'
        'a{{ _get("Card").render() }}b'
        '{%- endcall %}'
    )
    parser = JxParser(name="test", source=source, components=[])
    result, _ = parser.parse(validate_tags=False)
    assert result == expected


def test_nested_same_tag_siblings():
    """Multiple same-name siblings inside a parent of the same name."""
    source = """<Card><Card>a</Card><Card>b</Card></Card>"""
    expected = (
        '{% call(_slot="") _get("Card").render() -%}'
        '{% call(_slot="") _get("Card").render() -%}a{%- endcall %}'
        '{% call(_slot="") _get("Card").render() -%}b{%- endcall %}'
        '{%- endcall %}'
    )
    parser = JxParser(name="test", source=source, components=[])
    result, _ = parser.parse(validate_tags=False)
    assert result == expected


def test_nested_same_tag_unclosed():
    """An unclosed nested same-name tag is reported."""
    source = """<Card><Card>a</Card>"""
    parser = JxParser(name="test", source=source, components=[])
    with pytest.raises(TemplateSyntaxError, match="Unclosed component"):
        parser.parse(validate_tags=False)


def test_validate_tags():
    source = """<Button><Icon name="alert" /> Click me</Button>"""
    parser = JxParser(name="test", source=source, components=["Button"])
    with pytest.raises(TemplateSyntaxError, match="Unknown component `Icon`.*"):
        parser.parse(validate_tags=True)


def test_error_lineno_after_multiline_tag():
    """Error line numbers stay correct after a multi-line tag replacement."""
    source = (
        '<Valid\n'
        '  foo="bar"\n'
        '  baz="qux"\n'
        '/>\n'
        '<Unknown />\n'
    )
    parser = JxParser(name="test", source=source, components=["Valid"])
    with pytest.raises(TemplateSyntaxError, match=r"\[test:5:0\] Unknown component `Unknown`"):
        parser.parse(validate_tags=True)


def test_slots():
    source = """
<html>
  {% slot header %}
  <h1>Header</h1>
  {% endslot %}

  <p>Main content</p>
  {% if user %}
    <p>Hi, {{ user }}!</p>
  {% endif %}

  {% slot footer %}
    <footer>Footer content</footer>
  {% endslot %}
</html>
    """
    parser = JxParser(name="test", source=source, components=[])
    result, slots = parser.parse(validate_tags=False)
    print(result)

    assert slots == ("header", "footer")
    assert result.strip() == """
<html>
  {% if _slots.get('header') %}{{ _slots['header'] }}{% else %}
  <h1>Header</h1>
  {% endif %}

  <p>Main content</p>
  {% if user %}
    <p>Hi, {{ user }}!</p>
  {% endif %}

  {% if _slots.get('footer') %}{{ _slots['footer'] }}{% else %}
    <footer>Footer content</footer>
  {% endif %}
</html>
""".strip()



def test_slots_strip():
    source = """
<html>
  {% slot header %}
  <h1>Header</h1>
  {% endslot %}

  <p>Main content</p>
  {% if user %}
    <p>Hi, {{ user }}!</p>
  {% endif %}

  {% slot footer -%}
    <footer>Footer content</footer>
  {%- endslot %}
</html>
    """
    parser = JxParser(name="test", source=source, components=[])
    result, _ = parser.parse(validate_tags=False)
    print(result)

    assert result.strip() == """
<html>
  {% if _slots.get('header') %}{{ _slots['header'] }}{% else %}
  <h1>Header</h1>
  {% endif %}

  <p>Main content</p>
  {% if user %}
    <p>Hi, {{ user }}!</p>
  {% endif %}

  {% if _slots.get('footer') %}{{ _slots['footer'] }}{% else %}<footer>Footer content</footer>{% endif %}
</html>
""".strip()


def test_fills():
    source = """
<Layout>
{% fill header %}
<h1>Header</h1>
{% endfill %}

<p>Main content</p>
<p>Hi, {{ user }}!</p>

{% fill footer %}
<footer>Footer content</footer>
{% endfill %}
</Layout>
    """
    parser = JxParser(name="test", source=source, components=["Layout"])
    result, _ = parser.parse(validate_tags=False)
    print(result)

    assert result.strip() == """
{% call(_slot="") _get("Layout").render() -%}
{% if _slot == 'header' %}
<h1>Header</h1>
{% elif _slot == 'footer' %}
<footer>Footer content</footer>
{% else -%}
<p>Main content</p>
<p>Hi, {{ user }}!</p>
{%- endif %}
{%- endcall %}
""".strip()


def test_fills_strip():
    source = """
<Layout>
{% fill header -%}
<h1>Header</h1>
{%- endfill %}

<p>Main content</p>
<p>Hi, {{ user }}!</p>

{% fill footer %}
<footer>Footer content</footer>
{%- endfill %}
</Layout>
    """
    parser = JxParser(name="test", source=source, components=["Layout"])
    result, _ = parser.parse(validate_tags=False)
    print(result)

    assert result.strip() == """
{% call(_slot="") _get("Layout").render() -%}
{% if _slot == 'header' %}<h1>Header</h1>{% elif _slot == 'footer' %}
<footer>Footer content</footer>{% else -%}
<p>Main content</p>
<p>Hi, {{ user }}!</p>
{%- endif %}
{%- endcall %}
""".strip()


def test_comment_blocks_are_protected():
    """Component tags inside Jinja comments should not be processed."""
    source = """{# TODO: Use <Card /> here #}\n<Foo>bar</Foo>"""
    parser = JxParser(name="test", source=source, components=["Foo"])
    result, _ = parser.parse(validate_tags=True)
    assert "{# TODO: Use <Card /> here #}" in result
    assert '_get("Foo")' in result


def test_multiline_comment_blocks_are_protected():
    """Multiline Jinja comments with component tags should not be processed."""
    source = """{#\n  <Card title="hello" />\n  <Button />\n#}\n<Foo />"""
    parser = JxParser(name="test", source=source, components=["Foo"])
    result, _ = parser.parse(validate_tags=True)
    assert "<Card" in result
    assert "<Button" in result
    assert '_get("Foo")' in result
