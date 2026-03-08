"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import re
from uuid import uuid4

from .exceptions import TemplateSyntaxError
from .utils import logger


BLOCK_CALL = '{% call(_slot="") _get("[TAG]").render([ATTRS]) -%}[CONTENT]{%- endcall %}'
INLINE_CALL = '{{ _get("[TAG]").render([ATTRS]) }}'

re_raw = r"\{%-?\s*raw\s*-?%\}.+?\{%-?\s*endraw\s*-?%\}"
RX_RAW = re.compile(re_raw, re.DOTALL)

re_tag_name = r"[A-Z][0-9A-Za-z_.:$-]*"
RX_TAG_NAME = re.compile(rf"<(?P<tag>{re_tag_name})(\s|\n|/|>)")

re_attr = r"""
(?P<name>[:a-zA-Z@$_][a-zA-Z@:$_0-9-\.]*)
(?:
    \s*=\s*
    (?P<value>".*?"|'.*?'|\{\{.*?\}\})
)?
(?:\s+|/|"|$)
"""
RX_ATTR = re.compile(re_attr, re.VERBOSE | re.DOTALL)

RE_LSTRIP = r"\s*(?P<lstrip>-?)%}"
RE_RSTRIP = r"{%(?P<rstrip>-?)\s*"

RE_SLOT_OPEN = r"{%-?\s*slot\s+(?P<name>[0-9A-Za-z_.:$-]+)" + RE_LSTRIP
RE_SLOT_CLOSE = RE_RSTRIP + r"endslot\s*-?%}"
RX_SLOT = re.compile(rf"{RE_SLOT_OPEN}(?P<default>.*?)({RE_SLOT_CLOSE})", re.DOTALL)

RE_FILL_OPEN = r"{%-?\s*fill\s+(?P<name>[0-9A-Za-z_.:$-]+)" + RE_LSTRIP
RE_FILL_CLOSE = RE_RSTRIP + r"endfill\s*-?%}"
RX_FILL = re.compile(rf"{RE_FILL_OPEN}(?P<body>.*?)({RE_FILL_CLOSE})", re.DOTALL)


class JxParser:
    def __init__(
        self,
        *,
        name: str,
        source: str,
        components: list[str],
    ):
        """
        A parser that transforms a template's source code by replacing
        TitledCased HTML tags with their corresponding component calls.

        Only the names defined in the `components` list are allowed.

        Arguments:
            name:
                The name of the template for error reporting.
            source:
                The source code of the template.
            components:
                A list of allowed component names.

        """
        self.name = name
        self.source = source
        self.components = components

    def parse(self, *, validate_tags: bool = True) -> tuple[str, tuple[str, ...]]:
        """
        Parses the template source code.

        Arguments:
            validate_tags:
                Whether to raise an error for unknown TitleCased tags.

        Returns:
            - The transformed template source code
            - The list of slot names.

        Raises:
            TemplateSyntaxError:
                If the template contains unknown components or syntax errors.

        """
        source = self.source
        source, raw_blocks = self.replace_raw_blocks(source)
        source = self.process_tags(source, validate_tags=validate_tags)
        source, slots = self.process_slots(source)
        source = self.restore_raw_blocks(source, raw_blocks)
        return source, slots

    def replace_raw_blocks(self, source: str) -> tuple[str, dict[str, str]]:
        """
        Replace the `{% raw %}` blocks with temporary placeholders.

        Arguments:
            source:
                The template source code.

        """
        raw_blocks = {}
        while True:
            match = RX_RAW.search(source)
            if not match:
                break
            start, end = match.span(0)
            repl = match.group(0)
            key = f"--RAW-{uuid4().hex}--"
            raw_blocks[key] = repl
            source = f"{source[:start]}{key}{source[end:]}"

        return source, raw_blocks

    def restore_raw_blocks(self, source: str, raw_blocks: dict[str, str]) -> str:
        """
        Restores the original `{% raw %}` blocks from the temporary placeholders.

        Arguments:
            source:
                The template source code.
            raw_blocks:
                A dictionary mapping placeholder keys to their original raw block content.

        """
        for uid, code in raw_blocks.items():
            source = source.replace(uid, code)
        return source

    def process_tags(self, source: str, *, validate_tags: bool = True) -> str:
        """
        Search for TitledCased HTML tags in the template source code and replace
        them with their corresponding component calls.

        Arguments:
            source:
                The template source code.
            validate_tags:
                Whether to raise an error for unknown TitleCased tags.

        """
        while True:
            match = RX_TAG_NAME.search(source)
            if not match:
                break
            source = self.replace_tag(source, match, validate_tags=validate_tags)
        return source

    def replace_tag(
        self,
        source: str,
        match: re.Match,
        *,
        validate_tags: bool = True,
    ) -> str:
        """
        Replaces a single TitledCased HTML tag with its corresponding component call.

        Arguments:
            source:
                The template source code.
            match:
                The regex match object for the tag.
            validate_tags:
                Whether to raise an error for unknown TitleCased tags.

        """
        start, curr = match.span(0)
        lineno = source[:start].count("\n") + 1
        line_start = source.rfind("\n", 0, start) + 1
        col = start - line_start

        tag = match.group("tag")
        if validate_tags and tag not in self.components:
            line = self.source.split("\n")[lineno - 1]
            raise TemplateSyntaxError(
                f"[{self.name}:{lineno}:{col}] Unknown component `{tag}`\n"
                f"  {line}\n"
                f"  {' ' * col}^"
            )

        raw_attrs, end = self._parse_opening_tag(source, lineno=lineno, col=col, start=curr - 1)
        if end == -1:
            line = self.source.split("\n")[lineno - 1]
            raise TemplateSyntaxError(
                f"[{self.name}:{lineno}:{col}] Syntax error: `{tag}`\n"
                f"  {line}\n"
                f"  {' ' * col}^"
            )

        inline = source[end - 2 : end] == "/>"
        if inline:
            content = ""
        else:
            close_tag = f"</{tag}>"
            index = self._find_closing_tag(source, tag, end)
            if index == -1:
                line = self.source.split("\n")[lineno - 1]
                raise TemplateSyntaxError(
                    f"[{self.name}:{lineno}:{col}] Unclosed component `{tag}`\n"
                    f"  {line}\n"
                    f"  {' ' * col}^"
                )

            content = source[end:index]
            end = index + len(close_tag)

        if content:
            content = self.process_fills(content)

        attrs = self._parse_attrs(raw_attrs)
        repl = self._build_call(tag, attrs, content)
        return f"{source[:start]}{repl}{source[end:]}"

    def process_slots(self, source: str) -> tuple[str, tuple[str, ...]]:
        """
        Extracts slot content from the template source code.

        Arguments:
            source:
                The template source code

        Returns:
            - The transformed template source code
            - The list of slot names.

        """
        slots = {}
        while True:
            match = RX_SLOT.search(source)
            if not match:
                break
            start, end = match.span(0)
            slot_name = match.group("name")
            slot_default = match.group("default") or ""
            lstrip = match.group("lstrip") == "-"
            rstrip = match.group("rstrip") == "-"
            if lstrip:
                slot_default = slot_default.lstrip()
            if rstrip:
                slot_default = slot_default.rstrip()

            slot_expr = "".join([
                "{% if _slots.get('", slot_name,
                "') %}{{ _slots['", slot_name,
                "'] }}{% else %}", slot_default,
                "{% endif %}"
            ])
            source = f"{source[:start]}{slot_expr}{source[end:]}"
            slots[slot_name] = 1

        return source, tuple(slots.keys())

    def process_fills(self, source: str) -> str:
        """
        Processes `{% fill slot_name %}...{% endfill %}` blocks in the template source code.

        Arguments:
            source:
                The template source code.

        Returns:
            The modified source code prepended by fill contents as `if` statements.

        """
        fills = {}

        while True:
            match = RX_FILL.search(source)
            if not match:
                break
            start, end = match.span(0)
            fill_name = match.group("name")
            fill_body = match.group("body") or ""
            lstrip = match.group("lstrip") == "-"
            rstrip = match.group("rstrip") == "-"
            if lstrip:
                fill_body = fill_body.lstrip()
            if rstrip:
                fill_body = fill_body.rstrip()
            fills[fill_name] = fill_body
            source = f"{source[:start]}{source[end:]}"

        if not fills:
            return source

        parts = []
        for i, (fill_name, fill_body) in enumerate(fills.items()):
            keyword = "if" if i == 0 else "elif"
            parts.append(f"{{% {keyword} _slot == '{fill_name}' %}}{fill_body}")
        str_ifs = "\n" + "".join(parts)

        return f"{str_ifs}{{% else -%}}\n{source.strip()}\n{{%- endif %}}\n"

    # Private

    def _find_closing_tag(self, source: str, tag: str, start: int) -> int:
        """
        Find the matching closing tag, correctly handling nested same-name tags.

        Arguments:
            source:
                The template source code.
            tag:
                The tag name to find the closing tag for.
            start:
                Position to start searching from (right after the opening tag's `>`).

        Returns:
            The index of the matching `</Tag>`, or -1 if not found.

        """
        open_rx = re.compile(rf"<{re.escape(tag)}(\s|\n|/|>)")
        close_tag = f"</{tag}>"
        close_len = len(close_tag)
        depth = 1
        pos = start

        while depth > 0:
            next_open = open_rx.search(source, pos)
            next_close = source.find(close_tag, pos)

            if next_close == -1:
                return -1

            if next_open and next_open.start() < next_close:
                # Nested opening tag found before the next close tag.
                # Parse it to check whether it is self-closing.
                _, tag_end = self._parse_opening_tag(
                    source, lineno=0, col=0, start=next_open.end() - 1
                )
                if tag_end == -1:
                    return -1
                if source[tag_end - 2 : tag_end] != "/>":
                    depth += 1
                pos = tag_end
            else:
                depth -= 1
                if depth == 0:
                    return next_close
                pos = next_close + close_len

        return -1

    def _parse_opening_tag(
        self, source: str, *, lineno: int, col: int, start: int
    ) -> tuple[str, int]:
        """
        Parses the opening tag and returns the raw attributes and the position
        where the opening tag ends.
        """
        eof = len(source)
        in_single_quotes = in_double_quotes = in_braces = False
        i = start
        end = -1

        while i < eof:
            ch = source[i]
            ch2 = source[i : i + 2]

            # Detects {{ … }} only when NOT inside quotes
            if not in_single_quotes and not in_double_quotes:
                if ch2 == "{{":
                    if in_braces:
                        line = self.source.split("\n")[lineno - 1]
                        raise TemplateSyntaxError(
                            f"[{self.name}:{lineno}:{col}] Unmatched braces\n"
                            f"  {line}\n"
                            f"  {' ' * col}^"
                        )
                    in_braces = True
                    i += 2
                    continue

                if ch2 == "}}":
                    if not in_braces:
                        line = self.source.split("\n")[lineno - 1]
                        raise TemplateSyntaxError(
                            f"[{self.name}:{lineno}:{col}] Unmatched braces\n"
                            f"  {line}\n"
                            f"  {' ' * col}^"
                        )
                    in_braces = False
                    i += 2
                    continue

            if ch == "'" and not in_double_quotes and not in_braces:
                in_single_quotes = not in_single_quotes
                i += 1
                continue

            if ch == '"' and not in_single_quotes and not in_braces:
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

    def _parse_attrs(self, raw_attrs: str) -> list[str]:
        """
        Parses the HTML attributes string and returns a list of '"key":value'
        strings to be used in a components call.
        """
        raw_attrs = raw_attrs.replace("\n", " ").strip()
        if not raw_attrs:
            return []

        attrs = []
        for name, value in RX_ATTR.findall(raw_attrs):
            name = name.strip().replace("-", "_")
            value = value.strip()

            if not value:
                attrs.append(f'"{name}":True')
            else:
                # vue-like syntax could be possible
                # if (name[0] == ":" and value[0] in ("\"'") and value[-1] in ("\"'")):
                #     value = value[1:-1].strip()
                #     name = name.lstrip(":")

                # double curly braces syntax
                if value[:2] == "{{" and value[-2:] == "}}":
                    value = value[2:-2].strip()

                attrs.append(f'"{name}":{value}')

        return attrs

    def _build_call(self, tag: str, attrs: list[str], content: str = "") -> str:
        """
        Builds a component call string.
        """
        logger.debug(f"{tag} {attrs} {'inline' if not content else ''}")

        str_attrs = ""
        if attrs:
            str_attrs = "**{" + ", ".join(attrs) + "}"

        if content:
            return (
                BLOCK_CALL.replace("[TAG]", tag)
                .replace("[ATTRS]", str_attrs)
                .replace("[CONTENT]", content)
            )
        else:
            return INLINE_CALL.replace("[TAG]", tag).replace("[ATTRS]", str_attrs)
