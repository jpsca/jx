"""
Jx | Copyright (c) Juan-Pablo Scaletti
"""

import threading
import typing as t
from dataclasses import dataclass, field
from pathlib import Path
from types import CodeType

import jinja2

from . import utils
from .component import Component
from .exceptions import ImportError
from .meta import extract_metadata
from .parser import JxParser
from .utils import logger


@dataclass(slots=True)
class CData:
    base_path: Path
    path: Path
    mtime: float
    code: CodeType | None = None
    required: dict[str, type | None] = field(default_factory=dict)  # { attr: type or None }
    optional: dict[str, tuple[t.Any, type | None]] = field(default_factory=dict)  # { attr: (default, type or None) }
    imports: dict[str, str] = field(default_factory=dict)  # { name: relpath }
    css: tuple[str, ...] = ()
    js: tuple[str, ...] = ()
    slots: tuple[str, ...] = ()


class Catalog:

    # IDEA: This dict could be replaced by a dict-like object
    # that uses a LRU cache (to limit the memory used)
    # or even a shared Redis/Memcache cache.
    components: dict[str, CData]

    def __init__(
        self,
        folder: str | Path | None = None,
        *,
        jinja_env: jinja2.Environment | None = None,
        extensions: list | None = None,
        filters: dict[str, t.Any] | None = None,
        tests: dict[str, t.Any] | None = None,
        auto_reload: bool = True,
        **globals: t.Any,
    ) -> None:
        """
        Manager of the components and their global settings.

        Arguments:
            folder:
                Optional folder path to scan for components. It's a shortcut to
                calling `add_folder` when only one is used.
            jinja_env:
                Optional Jinja2 environment to use for rendering.
            extensions:
                Optional extra Jinja2 extensions to add to the environment.
            filters:
                Optional extra Jinja2 filters to add to the environment.
            tests:
                Optional extra Jinja2 tests to add to the environment.
            auto_reload:
                Whether to check the last-modified time of the components files and
                automatically re-process them if they change. The performance impact of
                leaving it on is minimal, but *might* be noticeable when rendering a
                component that uses a large number of child components.
            **globals:
                Variables to make available to all components by default.

        """
        self._lock = threading.RLock()  # Protects self.components access
        self.components = {}
        self.jinja_env = self._make_jinja_env(
            jinja_env=jinja_env,
            globals=globals,
            filters=filters,
            tests=tests,
            extensions=extensions,
        )
        self.auto_reload = auto_reload
        if folder:
            self.add_folder(folder)

    def add_folder(
        self, path: str | Path, *, prefix: str = "", preload: bool = True
    ) -> None:
        """
        Add a folder path from which to search for components, optionally under a prefix.

        Components without a prefix can be imported as a path relative to the folder,
        e.g.: `sub/folder/component.jinja` or with a path relative to the component
        where it is used: `./folder/component.jinja`.

        Relative imports cannot go outside the folder.

        Components added with a prefix must be imported using the prefix followed
        by a colon: `prefix:sub/folder/component.jinja`. If the importing is
        done from within a component with the prefix itself, a relative
        import can also be used, e.g.: `./component.jinja`.

        All the folders added under the same prefix will be treated as if they
        were a single folder. This means if you add two folders, under the same prefix,
        with a component with the same subpath/filename, the one in the folder
        added **first** will be used and the other ignored.

        WARNING: You cannot move or delete components files from the folder after
        calling this method, but you can call it again to add new components added
        to the folder. This is unrelated to the value of `preload`.

        Arguments:
            path:
                Absolute path of the folder with component files.
            prefix:
                Optional path prefix that all the components in the folder
                will have. The default is empty.
            preload:
                Whether to preload the data of components in the folder.
                If set to `True` (the default), the component data will be loaded into
                memory when the folder is added, instead of just before rendering it.
                This makes the first render faster at the expense of a few
                microseconds upfront.

        """
        base_path = Path(path).resolve()
        prefix = prefix.replace("\\", "/").strip("./@ ")
        prefix = f"@{prefix}/" if prefix else ""
        if prefix:
            logger.debug(f"Adding folder `{base_path}` with the prefix `{prefix}`")
        else:
            logger.debug(f"Adding folder `{base_path}`")

        with self._lock:
            for filepath in base_path.rglob("*.jinja"):
                relpath = f"{prefix}{filepath.relative_to(base_path).as_posix()}"
                if relpath in self.components:
                    logger.debug(f"Component already exists: {relpath}")
                    continue
                cdata = CData(
                    base_path=base_path, path=filepath, mtime=filepath.stat().st_mtime
                )
                self.components[relpath] = cdata

            if preload:
                # Take a snapshot of keys to avoid "dict changed size during iteration"
                relpaths = list(self.components.keys())

        # Preload outside the lock to avoid holding it during compilation
        if preload:
            for relpath in relpaths:
                self.get_component_data(relpath)

    def render(
        self, relpath: str, globals: dict[str, t.Any] | None = None, **kwargs
    ) -> str:
        """
        Render a component with the given relative path and context.

        Arguments:
            relpath:
                The path of the component to render, including the extension,relative to its view folder.
                e.g.: "sub/component.jinja". Always use the forward slash (/) as the path separator.
            globals:
                Optional global variables to make available to the component and all its
                imported components.
            **kwargs:
                Keyword arguments to pass to the component.
                They will be available in the component's context but not to its imported components.

        Returns:
            The rendered component as a string.

        """
        relpath = relpath.replace("\\", "/").strip("/")
        co = self.get_component(relpath)

        globals = globals or {}
        globals.update({
            "assets": {
                "collect_css": co.collect_css,
                "collect_js": co.collect_js,
                "render_css": co.render_css,
                "render_js": co.render_js,
                "render": co.render_assets,
            }
        })
        co.globals = globals

        return co.render(**kwargs)

    def render_string(
        self, source: str, globals: dict[str, t.Any] | None = None, **kwargs
    ) -> str:
        """
        Render a component from a string source.
        Works like `render`, but the component is not cached and cannot do relative imports.

        Arguments:
            source:
                The Jinja2 source code of the component to render.
            globals:
                Optional global variables to make available to the component and all its
                imported components.
            **kwargs:
                Keyword arguments to pass to the component.
                They will be available in the component's context but not to its imported components.

        Returns:
            The rendered component as a string.

        """
        meta = extract_metadata(source, base_path=Path(), fullpath=Path())
        name = "<string>"

        parser = JxParser(name=name, source=source, components=list(meta.imports.keys()))
        parsed_source, slots = parser.parse()

        code = self.jinja_env.compile(source=parsed_source, name=name, filename=name)
        tmpl = jinja2.Template.from_code(self.jinja_env, code, self.jinja_env.globals)

        co = Component(
            relpath=name,
            tmpl=tmpl,
            get_component=self.get_component,
            required=meta.required,
            optional=meta.optional,
            imports=meta.imports,
            css=meta.css,
            js=meta.js,
            slots=slots,
        )

        globals = globals or {}
        globals.update({
            "assets": {
                "collect_css": co.collect_css,
                "collect_js": co.collect_js,
                "render_css": co.render_css,
                "render_js": co.render_js,
                "render": co.render_assets,
            }
        })
        co.globals = globals

        return co.render(**kwargs)

    def get_component_data(self, relpath: str) -> CData:
        """
        Get the component data from the cache.
        If the file has been updated, the component is re-processed.

        Arguments:
            relpath:
                The path of the component to render, including the extension,relative to its view folder.
                e.g.: "sub/component.jinja". Always use the forward slash (/) as the path separator.

        """
        with self._lock:
            cdata = self.components.get(relpath)
            if not cdata:
                raise ImportError(relpath)

            mtime = cdata.path.stat().st_mtime if self.auto_reload else 0
            if cdata.code is not None:
                if self.auto_reload:
                    if mtime == cdata.mtime:
                        return cdata
                else:
                    return cdata

            # Need to recompile - read file and parse while holding the lock
            # to prevent other threads from seeing partial state
            source = cdata.path.read_text()
            meta = extract_metadata(source, base_path=cdata.base_path, fullpath=cdata.path)

            parser = JxParser(
                name=relpath, source=source, components=list(meta.imports.keys())
            )
            parsed_source, slots = parser.parse()
            code = self.jinja_env.compile(
                source=parsed_source, name=relpath, filename=cdata.path.as_posix()
            )

            # Update all fields atomically (from other threads' perspective)
            cdata.mtime = mtime
            cdata.code = code
            cdata.required = meta.required
            cdata.optional = meta.optional
            cdata.imports = meta.imports
            cdata.css = meta.css
            cdata.js = meta.js
            cdata.slots = slots
            return cdata

    def get_component(self, relpath: str) -> Component:
        """
        Instantiate and return a component object by its relative path.

        Arguments:
            relpath:
                The path of the component to render, including the extension,relative to its view folder.
                e.g.: "sub/component.jinja". Always use the forward slash (/) as the path separator.

        """
        with self._lock:
            cdata = self.get_component_data(relpath)
            assert cdata.code is not None  # for type checker
            tmpl = jinja2.Template.from_code(
                self.jinja_env, cdata.code, self.jinja_env.globals
            )

            co = Component(
                relpath=relpath,
                tmpl=tmpl,
                get_component=self.get_component,
                required=cdata.required,
                optional=cdata.optional,
                imports=cdata.imports,
                css=cdata.css,
                js=cdata.js,
                slots=cdata.slots,
            )
            return co

    def list_components(self) -> list[str]:
        """
        Return all registered component paths.

        Returns:
            A list of component relative paths (e.g., ["button.jinja", "card.jinja"]).

        """
        with self._lock:
            return list(self.components.keys())

    def get_signature(self, relpath: str) -> dict[str, t.Any]:
        """
        Return a component's signature including its arguments and metadata.

        Arguments:
            relpath:
                The path of the component, including the extension, relative to its view folder.
                e.g.: "sub/component.jinja". Always use the forward slash (/) as the path separator.

        Returns:
            A dictionary containing:
                - required: dict of required argument names mapped to their type (or None)
                - optional: dict of optional arguments mapped to (default_value, type or None)
                - slots: tuple of slot names
                - css: tuple of CSS file URLs
                - js: tuple of JS file URLs

        """
        cdata = self.get_component_data(relpath)
        return {
            "required": cdata.required,
            "optional": cdata.optional,
            "slots": cdata.slots,
            "css": cdata.css,
            "js": cdata.js,
        }

    # Private

    def _make_jinja_env(
        self,
        *,
        jinja_env: jinja2.Environment | None = None,
        globals: dict[str, t.Any] | None = None,
        filters: dict[str, t.Any] | None = None,
        tests: dict[str, t.Any] | None = None,
        extensions: list | None = None,
    ) -> jinja2.Environment:
        """
        Create a new Jinja2 environment with the specified settings.

        Arguments:
            jinja_env:
                Optional Jinja2 environment to use as a base.
            globals:
                Optional global variables to add to the environment.
            filters:
                Optional extra Jinja2 filters to add to the environment.
            extensions:
                Optional extra Jinja2 extensions to add to the environment.
            tests:
                Optional extra Jinja2 tests to add to the environment.

        """
        jinja_env = jinja_env or getattr(self, "jinja_env", None)
        if jinja_env:
            # It could be `jinja_env.overlay()` instead, but that might
            # might lead to confusion if the user expects changes
            # to the original environment to be reflected here.
            env = jinja_env
        else:
            env = jinja2.Environment()

        globals = globals or {}
        globals.update(
            {
                # A unique ID generator for HTML elements, see `utils.get_random_id`
                # docstring for more information.
                "_get_random_id": utils.get_random_id,
            }
        )
        env.globals.update(globals)

        filters = filters or {}
        env.filters.update(filters)

        tests = tests or {}
        env.tests.update(tests)

        extensions = extensions or []
        # The "jinja2.ext.do" extension allows the use of the "do" statement in templates,
        # that execute statements without outputting a value.
        # Is specially useful for manipulating the `attrs` object.
        extensions.extend(["jinja2.ext.do"])
        for ext in extensions:
            env.add_extension(ext)

        env.autoescape = True
        env.undefined = jinja2.StrictUndefined

        return env
