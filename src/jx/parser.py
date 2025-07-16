"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import re
import typing as t
from uuid import uuid4

from markupsafe import Markup

from .exceptions import TemplateSyntaxError
from .utils import logger


RENDER_CMD = '_self._co["[TAG]"].render'
BLOCK_CALL = '{% call(_slot="") [CMD]([ATTRS]) -%}[CONTENT]{%- endcall %}'.replace("[CMD]", RENDER_CMD)
INLINE_CALL = "{{ [CMD]([ATTRS]) }}".replace("[CMD]", RENDER_CMD)

re_raw = r"\{%-?\s*raw\s*-?%\}.+?\{%-?\s*endraw\s*-?%\}"
RX_RAW = re.compile(re_raw, re.DOTALL)

re_tag_prefix = r"([0-9A-Za-z_-]+\:)?"
re_tag_path = r"([0-9A-Za-z_-]+\.)*[A-Z][0-9A-Za-z_-]*"
re_tag_name = rf"{re_tag_prefix}{re_tag_path}"
RX_TAG_NAME = re.compile(rf"<(?P<tag>{re_tag_name})(\s|\n|/|>)")

re_attr_name = r""
re_equal = r""
re_attr = r"""
(?P<name>[:a-zA-Z@$_][a-zA-Z@:$_0-9-]*)
(?:
    \s*=\s*
    (?P<value>".*?"|'.*?'|\{\{.*?\}\})
)?
(?:\s+|/|"|$)
"""
RX_ATTR = re.compile(re_attr, re.VERBOSE | re.DOTALL)


def escape(s: t.Any, /) -> Markup:
    if hasattr(s, "__html__"):
        return Markup(s.__html__())

    return Markup(
        str(s)
        .replace("&", "&amp;")
        .replace(">", "&gt;")
        .replace("<", "&lt;")
        .replace("'", "&#39;")
        .replace('"', "&#34;")
    )


class JxParser:
    def __init__(self, *, name: str, source: str, components: list[str]) :
        self.name = name
        self.source = source
        self.components = components

    def process(self, *, validate_tags: bool = True) -> str:
        raw_blocks = {}
        source = self.source
        source, raw_blocks = self.replace_raw_blocks(source)
        source = self.process_tags(source, validate_tags=validate_tags)
        source = self.restore_raw_blocks(source, raw_blocks)
        return source

    def replace_raw_blocks(self, source: str) -> tuple[str, dict[str, str]]:
        raw_blocks = {}
        while True:
            match = RX_RAW.search(source)
            if not match:
                break
            start, end = match.span(0)
            repl = escape(match.group(0))
            key = f"--RAW-{uuid4().hex}--"
            raw_blocks[key] = repl
            source = f"{source[:start]}{key}{source[end:]}"

        return source, raw_blocks

    def restore_raw_blocks(self, source: str, raw_blocks: dict[str, str]) -> str:
        for uid, code in raw_blocks.items():
            source = source.replace(uid, code)
        return source

    def process_tags(self, source: str, *, validate_tags: bool = True) -> str:
        while True:
            match = RX_TAG_NAME.search(source)
            if not match:
                break
            source = self.replace_tag(source, match, validate_tags=validate_tags)
        return source

    def replace_tag(self, source: str, match: re.Match, *, validate_tags: bool = True) -> str:
        start, curr = match.span(0)
        lineno = source[:start].count("\n") + 1

        tag = match.group("tag")
        if validate_tags and tag not in self.components:
            line = self.source.split("\n")[lineno - 1]
            raise TemplateSyntaxError(f"[{self.name}:{lineno}] Unknown component `{tag}`\n{line}")

        attrs, end = self._parse_opening_tag(source, start=curr - 1)
        if end == -1:
            line = self.source.split("\n")[lineno - 1]
            raise TemplateSyntaxError(f"[{self.name}:{lineno}] Syntax error: `{tag}`\n{line}")

        inline = source[end - 2:end] == "/>"
        if inline:
            content = ""
        else:
            close_tag = f"</{tag}>"
            index = source.find(close_tag, end, None)
            if index == -1:
                line = self.source.split("\n")[lineno - 1]
                raise TemplateSyntaxError(f"[{self.name}:{lineno}] Unclosed component `{tag}`\n{line}")

            content = source[end:index]
            end = index + len(close_tag)

        attrs_list = self._parse_attrs(attrs)
        repl = self._build_call(tag, attrs_list, content)

        return f"{source[:start]}{repl}{source[end:]}"

    def _parse_opening_tag(self, source: str, start: int) -> tuple[str, int]:
        eof = len(source)
        in_single_quotes = in_double_quotes = in_braces = False   # dentro de '…'  /  "…"
        i = start
        end = -1

        while i < eof:
            ch = source[i]
            ch2 = source[i:i + 2]
            # print(ch, ch2, in_single_quotes, in_double_quotes, in_braces)

            # Detects {{ … }} only when NOT inside quotes
            if not in_single_quotes and not in_double_quotes:
                if ch2 == "{{":
                    if in_braces:
                        # Unmatched braces!
                        break
                    in_braces = True
                    i += 2
                    continue

                if ch2 == "}}":
                    if not in_braces:
                        # Unmatched braces!
                        break
                    in_braces = False
                    i += 2
                    continue

            if (in_single_quotes or in_double_quotes) and ch2 in (r'\"', r"\'"):
                i += 2
                continue

            if ch == "'" and not in_double_quotes:
                in_single_quotes = not in_single_quotes
                i += 1
                continue

            if ch == '"' and not in_single_quotes:
                in_double_quotes = not in_double_quotes
                i += 1
                continue

            # End of the tag: ‘>’ outside of quotes and outside of {{ … }}
            if ch == ">" and not (in_single_quotes or in_double_quotes or in_braces):
                end = i + 1
                break

            i += 1

        attrs = source[start:end].strip().removesuffix("/>").removesuffix(">")
        return attrs, end

    def _parse_attrs(self, attrs: str) -> list[tuple[str, str]]:
        attrs = attrs.replace("\n", " ").strip()
        if not attrs:
            return []
        return RX_ATTR.findall(attrs)

    def _build_call(
        self,
        tag: str,
        attrs_list: list[tuple[str, str]],
        content: str = "",
    ) -> str:
        logger.debug(f"{tag} {attrs_list} {'inline' if not content else ''}")
        attrs = []
        for name, value in attrs_list:
            name = name.strip().replace("-", "_")
            value = value.strip()

            if not value:
                attrs.append(f'"{name}"=True')
            else:
                # vue-like syntax
                if (
                    name[0] == ":"
                    and value[0] in ("\"'")
                    and value[-1] in ("\"'")
                ):
                    value = value[1:-1].strip()
                    name = name.lstrip(":")

                # double curly braces syntax
                if value[:2] == "{{" and value[-2:] == "}}":
                    value = value[2:-2].strip()

                attrs.append(f'"{name}"={value}')

        if not attrs:
            str_attrs = ""
        else:
            str_attrs = "**{" + ", ".join([a.replace("=", ":", 1) for a in attrs]) + "}"

        if not content:
            call = INLINE_CALL.replace("[TAG]", tag).replace("[ATTRS]", str_attrs)
        else:
            call = (
                BLOCK_CALL
                .replace("[TAG]", tag)
                .replace("[ATTRS]", str_attrs)
                .replace("[CONTENT]", content)
            )
        return call
