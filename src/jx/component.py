"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import inspect
import re
import typing as t
from collections.abc import Sequence
from pathlib import Path

import jinja2
from markupsafe import Markup

from . import utils
from .attrs import Attrs
from .parser import JxParser


rx_external_url = re.compile(r"^[a-z]+://", re.IGNORECASE)


class Component:
    name: str
    jinja_env: jinja2.Environment
    required: tuple[str, ...] = ()
    optional: dict[str, t.Any] = {}

    jx_template: str = ""
    components: Sequence["Component | type[Component]"] = ()
    css: tuple[str, ...] = ()
    js: tuple[str, ...] = ()

    base_url: str = "/static/"

    c: dict[str, "Component"]  # Dictionary of instances of child components
    _attrs: Attrs
    _content: str = ""
    _template: str = ""

    def __init__(
        self,
        jinja_env: jinja2.Environment | None = None,
        *,
        name: str | None = None,
        base_url: str | None = None,
        **global_vars: t.Any,
    ) -> None:
        env = jinja_env or getattr(self, "jinja_env", None) or self._make_default_jinja_env()
        env.add_extension("jinja2.ext.do")
        env.globals.update({"_get_random_id": utils.get_random_id})

        self.jinja_env = env
        self.name = name or self.__class__.__name__
        global_vars.setdefault("_assets", {
            "css": self.collect_css,
            "js": self.collect_js,
            "render_css": self.render_css,
            "render_js": self.render_js,
            "render": self.render_assets,
        })
        self.globals = global_vars
        self.base_url = self.base_url if base_url is None else base_url

        self._parse_signature()
        self._init_components()

        self.jx_template = self.jx_template or self._load_template()
        self._template = self._prepare_template(self.jx_template)
        self._attrs = Attrs({})

    def __call__(self, **params: t.Any) -> Markup:
        """
        Renders the template with the provided arguments.
        """
        params = {**self.globals, **params}
        params["_self"] = self
        params.setdefault("_attrs", self._attrs)
        params.setdefault("_content", self._content)

        tmpl = self.jinja_env.from_string(self._template)
        html = tmpl.render(params).strip()
        return Markup(html)

    def render(self, *__args, **__kwargs) -> Markup:
        """
        Renders the component's template with the provided arguments.
        """

        return self()

    def collect_css(self) -> list[str]:
        """
        Returns a list of CSS files for the component and its children.
        """
        urls = dict.fromkeys(self.css, 1)
        for co in self.c.values():
            for file in co.collect_css():
                if file not in urls:
                    urls[file] = 1

        return list(urls.keys())

    def collect_js(self) -> list[str]:
        """
        Returns a list of JS files for the component and its children.
        """
        urls = dict.fromkeys(self.js, 1)
        for co in self.c.values():
            for file in co.collect_js():
                if file not in urls:
                    urls[file] = 1

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
            if not rx_external_url.match(url) and not url.startswith("/"):
                url = f"{self.base_url}{url}"
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
            if not rx_external_url.match(url) and not url.startswith("/"):
                url = f"{self.base_url}{url}"
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

    # Private

    def _make_default_jinja_env(self) -> jinja2.Environment:
        """
        Creates a Jinja2 environment with the necessary filters and globals.
        """
        env = jinja2.Environment()
        env.autoescape = True
        env.undefined = jinja2.StrictUndefined
        return env

    def _parse_signature(self) -> None:
        """
        Parses the signature of the `init` method to determine the required and optional arguments.
        """
        sig = inspect.signature(self.render)
        self.required = tuple(
            param.name for param in sig.parameters.values()
            # `__args`` and `__kwargs`` are are read as `_Component_args` and `_Component_kwargs` by python
            # I included there only so the type checker doesn't complain when overriding the method, so they
            # can be ignored.
            if not param.name.startswith("_Component_") and param.default is param.empty
        )
        self.optional = {
            param.name: param.default
            for param in sig.parameters.values()
            if param.default is not param.empty
        }

    def _init_components(self) -> None:
        """
        Instantiate the child components.
        """
        self.c = {}
        for cls in self.components:
            if isinstance(cls, Component):
                co = cls
                co.jinja_env = self.jinja_env
                co.globals = {**self.globals}
                co._init_components()
            else:
                if not issubclass(cls, Component):
                    raise TypeError(f"'{cls.__name__}' is not a component or a subclass of Component")
                co = cls(jinja_env=self.jinja_env, **self.globals)
            self.c[co.name] = co

    def _load_template(self) -> str:
        filepath = Path(inspect.getfile(self.__class__))
        files = list(filepath.parent.glob(f"{filepath.stem}*.jx"))
        if not files:
            files = list(filepath.parent.glob(f"{filepath.stem}*.jinja"))
        if not files:
            return ""
        return files[0].read_text()

    def _prepare_template(self, template: str) -> str:
        parser = JxParser(name=self.name, source=template, components=list(self.c.keys()))
        return parser.process()

    def _irender(
        self,
        *,
        caller: t.Callable[[], str] | None = None,
        _attrs: Attrs | dict[str, t.Any] | None = None,
        **kwargs: t.Any
    ) -> Markup:
        _attrs = _attrs.as_dict if isinstance(_attrs, Attrs) else _attrs or {}
        kwargs = {**_attrs, **kwargs}
        props, extra = self._filter_attrs(kwargs)

        self._attrs = Attrs(extra)
        self._content = caller() if caller else ""
        return self.render(**props)

    def _filter_attrs(
        self, kw: dict[str, t.Any]
    ) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
        props = {}

        for key in self.required:
            if key not in kw:
                raise TypeError(f"'{self.name}' component missing required argument: '{key}'")
            props[key] = kw.pop(key)

        for key in self.optional:
            props[key] = kw.pop(key, self.optional[key])
        extra = kw.copy()
        return props, extra
