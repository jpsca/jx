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
        "imports",
        "css",
        "js",
        "slots",
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
        imports: dict[str, str] | None = None,
        css: tuple[str, ...] = (),
        js: tuple[str, ...] = (),
        slots: tuple[str, ...] = (),
    ) -> None:
        """
        Internal object that represents a Jx component.

        Arguments:
            relpath:
                The "name" of the component.
            tmpl:
                The jinja2.Template for the component.
            get_component:
                A callable that retrieves a component by its name/relpath.
            required:
                A tuple of required attribute names.
            optional:
                A dictionary of optional attributes and their default values.
            imports:
                A dictionary of imported component names as "name": "relpath" pairs.
            css:
                A tuple of CSS file URLs.
            js:
                A tuple of JS file URLs.
            slots:
                A tuple of slot names.

        """
        self.relpath = relpath
        self.tmpl = tmpl
        self.get_component = get_component

        self.required = required
        self.optional = optional or {}
        self.imports = imports or {}
        self.css = css
        self.js = js
        self.slots = slots

        self.globals: dict[str, t.Any] = {}

    def render(
        self,
        *,
        content: str | None = None,
        attrs: Attrs | dict[str, t.Any] | None = None,
        caller: Callable[[str], str] | None = None,
        **params: t.Any
    ) -> Markup:
        content = content if content is not None else caller("") if caller else ""
        attrs = attrs.as_dict if isinstance(attrs, Attrs) else attrs or {}
        params = {**attrs, **params}
        props, attrs = self.filter_attrs(params)

        globals = {**self.globals, "_get": self.get_child}
        globals.setdefault("attrs", Attrs(attrs))
        globals.setdefault("content", content)

        slots = {}
        if caller:
            for name in self.slots:
                body = caller(name)
                if body != content:
                    slots[name] = body
        props["_slots"] = slots

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

    def collect_css(self, _visited: set[str] | None = None) -> list[str]:
        """
        Returns a list of CSS files for the component and its children.
        """
        urls = dict.fromkeys(self.css, 1)
        _visited = _visited or set()
        _visited.add(self.relpath)

        for name, relpath in self.imports.items():
            if relpath in _visited:
                continue
            co = self.get_child(name)
            for file in co.collect_css(_visited=_visited):
                if file not in urls:
                    urls[file] = 1
            _visited.add(relpath)

        return list(urls.keys())

    def collect_js(self, _visited: set[str] | None = None) -> list[str]:
        """
        Returns a list of JS files for the component and its children.
        """
        urls = dict.fromkeys(self.js, 1)
        _visited = _visited or set()
        _visited.add(self.relpath)

        for name, relpath in self.imports.items():
            if relpath in _visited:
                continue
            co = self.get_child(name)
            for file in co.collect_js(_visited=_visited):
                if file not in urls:
                    urls[file] = 1
            _visited.add(relpath)

        return list(urls.keys())

    def render_css(self) -> Markup:
        """
        Uses the `collect_css()` list to generate an HTML fragment
        with `<link rel="stylesheet" href="{url}">` tags.
        """
        html = []
        for url in self.collect_css():
            html.append(f'<link rel="stylesheet" href="{url}">')

        return Markup("\n".join(html))

    def render_js(self, module: bool = True, defer: bool = True) -> Markup:
        """
        Uses the `collected_js()` list to generate an HTML fragment
        with `<script type="module" src="{url}"></script>` tags.

        Arguments:
            module:
                Whether to render the script tags as modules, e.g.:
                `<script type="module" src="..."></script>`
            defer:
                Whether to add the `defer` attribute to the script tags,
                if `module` is `False` (all module scripts are also deferred), e.g.:
                `<script src="..." defer></script>`

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

        Arguments:
            module:
                Whether to render the script tags as modules, e.g.:
                `<script type="module" src="..."></script>`
            defer:
                Whether to add the `defer` attribute to the script tags,
                if `module` is `False` (all module scripts are also deferred), e.g.:
                `<script src="..." defer></script>`

        """
        html_css = self.render_css()
        html_js = self.render_js()
        return Markup(("\n".join([html_css, html_js]).strip()))
