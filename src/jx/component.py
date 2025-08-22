"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import re
import typing as t
from collections.abc import Callable

import jinja2
from markupsafe import Markup

from .attrs import Attrs
from .exceptions import MissingRequiredArgument


rx_external_url = re.compile(r"^[a-z]+://", re.IGNORECASE)


class Component:
    __slots__ = (
        "relpath",
        "tmpl",
        "get_component",
        "required",
        "optional",
        "css",
        "js",
        "imports",
        "globals",
    )

    def __init__(
        self,
        *,
        relpath: str,
        tmpl: jinja2.Template,
        get_component: Callable[[str], "Component"],
        required: tuple[str, ...] = (),
        optional: dict[str, t.Any] | None = None,
        css: tuple[str, ...] = (),
        js: tuple[str, ...] = (),
        imports: dict[str, str] | None = None,
    ) -> None:
        self.relpath = relpath
        self.tmpl = tmpl
        self.get_component = get_component

        self.required = required
        self.optional = optional or {}
        self.css = css
        self.js = js
        self.imports = imports or {}

        self.globals: dict[str, t.Any] = {}

    def render(
        self,
        *,
        content: str | None = None,
        attrs: Attrs | dict[str, t.Any] | None = None,
        caller: Callable[[], str] | None = None,
        **params: t.Any
    ) -> Markup:
        content = content if content is not None else caller() if caller else ""
        attrs = attrs.as_dict if isinstance(attrs, Attrs) else attrs or {}
        params = {**attrs, **params}
        props, attrs = self.filter_attrs(params)

        globals = {**self.globals, "_get": self.get_child}
        globals.setdefault("attrs", Attrs(attrs))
        globals.setdefault("content", content)

        html = self.tmpl.render({**props, **globals}).lstrip()
        return Markup(html)

    def filter_attrs(
        self, kw: dict[str, t.Any]
    ) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
        props = {}

        for key in self.required:
            if key not in kw:
                raise MissingRequiredArgument(self.relpath, key)
            props[key] = kw.pop(key)

        for key in self.optional:
            props[key] = kw.pop(key, self.optional[key])
        extra = kw.copy()
        return props, extra

    def get_child(self, name: str) -> "Component":
        relpath = self.imports[name]
        child = self.get_component(relpath)
        child.globals = self.globals
        return child

    def collect_css(self, visited: set[str] | None = None) -> list[str]:
        """
        Returns a list of CSS files for the component and its children.
        """
        urls = dict.fromkeys(self.css, 1)
        visited = visited or set()
        visited.add(self.relpath)

        for name, relpath in self.imports.items():
            if relpath in visited:
                continue
            co = self.get_child(name)
            for file in co.collect_css(visited=visited):
                if file not in urls:
                    urls[file] = 1
            visited.add(relpath)

        return list(urls.keys())

    def collect_js(self, visited: set[str] | None = None) -> list[str]:
        """
        Returns a list of JS files for the component and its children.
        """
        urls = dict.fromkeys(self.js, 1)
        visited = visited or set()
        visited.add(self.relpath)

        for name, relpath in self.imports.items():
            if relpath in visited:
                continue
            co = self.get_child(name)
            for file in co.collect_js(visited=visited):
                if file not in urls:
                    urls[file] = 1
            visited.add(relpath)

        return list(urls.keys())

    def render_css(self) -> Markup:
        """
        Uses the `collect_css()` list to generate an HTML fragment
        with `<link rel="stylesheet" href="{url}">` tags.

        Unless it's an external URL (e.g.: beginning with "http://" or "https://")
        or a root-relative URL (e.g.: starting with "/"),
        the URL is prefixed by `base_url`.
        """
        html = []
        for url in self.collect_css():
            html.append(f'<link rel="stylesheet" href="{url}">')

        return Markup("\n".join(html))

    def render_js(self, module: bool = True, defer: bool = True) -> Markup:
        """
        Uses the `collected_js()` list to generate an HTML fragment
        with `<script type="module" src="{url}"></script>` tags.

        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        the URL is prefixed by `base_url`. A hash can also be added to
        invalidate the cache if the content changes, if `fingerprint` is `True`.
        """
        html = []
        for url in self.collect_js():
            if module:
                tag = f'<script type="module" src="{url}"></script>'
            elif defer:
                tag = f'<script src="{url}" defer></script>'
            else:
                tag = f'<script src="{url}"></script>'
            html.append(tag)

        return Markup("\n".join(html))

    def render_assets(self, module: bool = True, defer: bool = False) -> Markup:
        """
        Calls `render_css()` and `render_js()` to generate
        an HTML fragment with `<link rel="stylesheet" href="{url}">`
        and `<script type="module" src="{url}"></script>` tags.
        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        the URL is prefixed by `base_url`. A hash can also be added to
        invalidate the cache if the content changes, if `fingerprint` is `True`.
        """
        html_css = self.render_css()
        html_js = self.render_js()
        return Markup(("\n".join([html_css, html_js]).strip()))
