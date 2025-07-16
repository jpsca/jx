import pytest

from jx.exceptions import TemplateSyntaxError
from jx.parser import JxParser


VALID_DATA = (
    # Simple case
    (
        """<Foo bar="baz">content</Foo>""",
        """{% call(_slot="") _self._co["Foo"].render(**{"bar":"baz"}) -%}content{%- endcall %}""",
    ),
    # Self-closing tag
    (
        """<Alert type="success" message="Success!" />""",
        """{{ _self._co["Alert"].render(**{"type":"success", "message":"Success!"}) }}""",
    ),
    # No attributes
    (
        """<Foo>content</Foo>""",
        """{% call(_slot="") _self._co["Foo"].render() -%}content{%- endcall %}""",
    ),
    # No attributes, self-closing tag
    (
        """<Foo />""",
        """{{ _self._co["Foo"].render() }}""",
    ),
    # Strings vs expressions
    (
        """<Foo bar="baz" :lorem="ipsum">content</Foo>""",
        """{% call(_slot="") _self._co["Foo"].render(**{"bar":"baz", "lorem":ipsum}) -%}content{%- endcall %}""",
    ),
    # Line breaks
    (
        """<Foo
          bar="baz"
          lorem="ipsum"
        >content</Foo>""",
        """{% call(_slot="") _self._co["Foo"].render(**{"bar":"baz", "lorem":"ipsum"}) -%}content{%- endcall %}""",
    ),
    # Line breaks, self-closing tag
    (
        """<Foo
          bar="baz"
          lorem="ipsum"
          green
        />""",
        """{{ _self._co["Foo"].render(**{"bar":"baz", "lorem":"ipsum", "green":True}) }}""",
    ),
    # Python expression in attribute and boolean attributes
    (
        """<Foo :bar="42 + 4" green large>content</Foo>""",
        """{% call(_slot="") _self._co["Foo"].render(**{"bar":42 + 4, "green":True, "large":True}) -%}content{%- endcall %}""",
    ),
    (
        """<Foo bar={{ 42 + 4 }} green large>content</Foo>""",
        """{% call(_slot="") _self._co["Foo"].render(**{"bar":42 + 4, "green":True, "large":True}) -%}content{%- endcall %}""",
    ),
    # `>` in expression
    (
        """<CloseBtn :disabled="num > 4" />""",
        """{{ _self._co["CloseBtn"].render(**{"disabled":num > 4}) }}""",
    ),
    (
        """<CloseBtn disabled={{ num > 4 }} />""",
        """{{ _self._co["CloseBtn"].render(**{"disabled":num > 4}) }}""",
    ),
    # `>` in attribute value
    (
        """<CloseBtn data-closer-action="click->closer#close" />""",
        """{{ _self._co["CloseBtn"].render(**{"data_closer_action":"click->closer#close"}) }}""",
    ),
    # Raw blocks
    (
        """<Foo bar="baz">content</Foo>
{% raw %}{{ a + b }}{% endraw %}
what""",
        """{% call(_slot="") _self._co["Foo"].render(**{"bar":"baz"}) -%}content{%- endcall %}
{% raw %}{{ a + b }}{% endraw %}
what""",
    ),
)


@pytest.mark.parametrize("source, expected", VALID_DATA)
def test_process_valid_tags(source, expected):
    parser = JxParser(name="test", source=source, components=[])
    result = parser.process(validate_tags=False)
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
    # Expression not opened
    (
        """<Foo bar=42 + 4}}>content</Foo>""",
        TemplateSyntaxError,
        "Syntax error",
    ),
)


@pytest.mark.parametrize("source, exception, match", INVALID_DATA)
def test_process_invalid_tags(source, exception, match):
    parser = JxParser(name="test", source=source, components=[])
    with pytest.raises(exception, match=f".*{match}.*"):
        parser.process(validate_tags=False)


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
{% call(_slot="") _self._co["Card"].render(**{"class":"card"}) -%}
  WTF
  {% call(_slot="") _self._co["Card"].render(**{"class":"card-header"}) -%}abc{%- endcall %}
  {% call(_slot="") _self._co["Card"].render(**{"class":"card-body"}) -%}
    <div>{% call(_slot="") _self._co["Card"].render() -%}Text{%- endcall %}</div>
  {%- endcall %}
{%- endcall %}
"""
    parser = JxParser(name="test", source=source, components=[])
    result = parser.process(validate_tags=False)
    print(result)
    assert result.strip() == expected.strip()


def test_validate_tags():
    source = """<Button><Icon name="alert" /> Click me</Button>"""
    parser = JxParser(name="test", source=source, components=["Button"])
    with pytest.raises(TemplateSyntaxError, match="Unknown component `Icon`.*"):
        parser.process(validate_tags=True)
