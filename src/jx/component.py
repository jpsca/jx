"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import inspect
import re
import typing as t
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path

import jinja2
from markupsafe import Markup

from . import utils
from .attrs import Attrs
from .parser import JxParser


rx_external_url = re.compile(r"^([a-z]+://|/)", re.IGNORECASE)


class Component:
    name: str
    jinja_env: jinja2.Environment
    required: tuple[str, ...] = ()
    optional: dict[str, t.Any] = {}

    template: str = ""
    components: Sequence["Component | type[Component]"] = ()
    css: tuple[str, ...] = ()
    js: tuple[str, ...] = ()

    url_relative_to: str | Path = ""
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
        **global_vars: t.Any,
    ) -> None:
        env = jinja_env or getattr(self, "jinja_env", None) or self._make_default_jinja_env()
        env.add_extension("jinja2.ext.do")
        env.globals.update({"_get_random_id": utils.get_random_id})
        self.jinja_env = env

        self.name = name or self.__class__.__name__
        self.globals = global_vars

        self.filepath = Path(inspect.getfile(self.__class__))
        self._parse_signature()
        self._init_components()
        self._add_default_assets()

        self.template = self.template or self._load_template()
        self._template = self._prepare_template(self.template)
        self.url_relative_to = Path(self.url_relative_to or self.filepath.parent).resolve()
        self._attrs = Attrs({})

    def render(self, *__args, **__kwargs) -> Markup:
        """
        Renders the component's template with the provided arguments.
        """
        return self._render()

    def collect_css(self, fingerprint: bool = False) -> list[str]:
        """
        Returns a list of CSS files for the component.

        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        if `fingerprint` is `True`, a hash to invalidate the cache if the content changes,
        will be added to the URL.
        """
        urls = dict.fromkeys(self._parse_urls(self.css, fingerprint=fingerprint), 1)
        for co in self.c.values():
            for file in co.collect_css(fingerprint=fingerprint):
                if file not in urls:
                    urls[file] = 1

        return list(urls.keys())

    def collect_js(self, fingerprint: bool = False) -> list[str]:
        """
        Returns a list of JS files for the component and its children.

        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        if `fingerprint` is `True`, a hash to invalidate the cache if the content changes,
        will be added to the URL.
        """
        urls = dict.fromkeys(self._parse_urls(self.js, fingerprint=fingerprint), 1)
        for co in self.c.values():
            for file in co.collect_js(fingerprint=fingerprint):
                if file not in urls:
                    urls[file] = 1

        return list(urls.keys())

    def render_css(self, fingerprint: bool = False) -> Markup:
        """
        Uses the `self.collect_css()` list to generate an HTML fragment
        with `<link rel="stylesheet" href="{url}">` tags.

        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        the URL is prefixed by `self.base_url`. A hash can also be added to
        invalidate the cache if the content changes, if `fingerprint` is `True`.
        """
        html = []
        for url in self.collect_css(fingerprint=fingerprint):
            if not rx_external_url.match(url):
                url = f"{self.base_url}{url}"
            html.append(f'<link rel="stylesheet" href="{url}">')

        return Markup("\n".join(html))

    def render_js(self, fingerprint: bool = False) -> Markup:
        """
        Uses the `self.collected_js()` list to generate an HTML fragment
        with `<script type="module" src="{url}"></script>` tags.

        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        the URL is prefixed by `self.base_url`. A hash can also be added to
        invalidate the cache if the content changes, if `fingerprint` is `True`.
        """
        html = []
        for url in self.collect_js(fingerprint=fingerprint):
            if not rx_external_url.match(url):
                url = f"{self.base_url}{url}"
            html.append(f'<script type="module" src="{url}"></script>')

        return Markup("\n".join(html))

    def render_assets(self, fingerprint: bool = False) -> Markup:
        """
        Calls `self.render_css()` and `self.render_js()` to generate
        an HTML fragment with `<link rel="stylesheet" href="{url}">`
        and `<script type="module" src="{url}"></script>` tags.
        Unless it's an external URL (e.g.: beginning with "http://" or "https://"),
        the URL is prefixed by `self.base_url`. A hash can also be added to
        invalidate the cache if the content changes, if `fingerprint` is `True`.
        """
        html_css = self.render_css(fingerprint=fingerprint)
        html_js = self.render_js(fingerprint=fingerprint)
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
            else:
                if not issubclass(cls, Component):
                    raise TypeError(f"'{cls.__name__}' is not a component or a subclass of Component")
                co = cls(jinja_env=self.jinja_env, **self.globals)
            self.c[co.name] = co

    def _add_default_assets(self) -> None:
        css = self.filepath.with_suffix(".css")
        if css.exists() and css not in self.css:
            self.css = (css.name, *self.css)

        js = self.filepath.with_suffix(".js")
        if js.exists() and js not in self.js:
            self.js = (js.name, *self.js)

    def _load_template(self) -> str:
        filepath = self.filepath.with_suffix(".jinja")
        return filepath.read_text() if filepath.exists() else ""

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

    def _render(self, **params: t.Any) -> Markup:
        params["_self"] = self
        params.setdefault("_attrs", self._attrs)
        params.setdefault("_content", self._content)

        tmpl = self.jinja_env.from_string(self._template, globals=self.globals)
        html = tmpl.render(params).strip()
        return Markup(html)

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

    def _parse_urls(self, assets: Sequence[str], fingerprint: bool = False) -> list[str]:
        urls = []
        for asset in assets:
            if rx_external_url.match(asset):
                urls.append(asset)
                continue
            file = (self.filepath.parent / asset).resolve()
            if fingerprint:
                file = self._fingerprint(file)
            url = file.relative_to(self.url_relative_to).as_posix()
            urls.append(url)

        return urls

    def _fingerprint(self, file: Path) -> Path:
        stat = file.stat()
        fingerprint = sha256(str(stat.st_mtime).encode()).hexdigest()
        return file.with_stem(f"{file.stem}-{fingerprint}")
