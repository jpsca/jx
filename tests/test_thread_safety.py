"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
from threading import Thread

from jx import Catalog


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=None, kwargs=None):
        args = args or ()
        kwargs = kwargs or {}
        Thread.__init__(
            self,
            group=group,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
        )
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args, **kwargs):
        Thread.join(self, *args, **kwargs)
        return self._return


def test_thread_safety_of_render_assets(folder):
    NUM_THREADS = 5

    child_tmpl = """
{#css "/static/c{i}.css" #}
{#js "/static/c{i}.js" #}
<p>Child {i}</p>""".strip()

    parent_tmpl = """
{{ assets.render() }}
{{ content }}""".strip()

    comp_tmpl = """
{# import "parent{i}.jinja" as Parent{i} #}
{# import "child{i}.jinja" as Child{i} #}
{# css "/static/a{i}.css", "/static/b{i}.css" #}
{# js "/static/a{i}.js", "/static/b{i}.js" #}
<Parent{i}><Child{i} /></Parent{i}>""".strip()

    expected_tmpl = """
<link rel="stylesheet" href="/static/a{i}.css">
<link rel="stylesheet" href="/static/b{i}.css">
<link rel="stylesheet" href="/static/c{i}.css">
<script type="module" src="/static/a{i}.js"></script>
<script type="module" src="/static/b{i}.js"></script>
<script type="module" src="/static/c{i}.js"></script>
<p>Child {i}</p>""".strip()

    for i in range(NUM_THREADS):
        si = str(i)
        child_name = f"child{i}.jinja"
        child_src = child_tmpl.replace("{i}", si)

        parent_name = f"parent{i}.jinja"
        parent_src = parent_tmpl.replace("{i}", si)

        comp_name = f"page{i}.jinja"
        comp_src = comp_tmpl.replace("{i}", si)

        (folder / child_name).write_text(child_src)
        (folder / comp_name).write_text(comp_src)
        (folder / parent_name).write_text(parent_src)

    cat = Catalog(folder)

    def render(i):
        return cat.render(f"page{i}.jinja")

    threads = []

    for i in range(NUM_THREADS):
        thread = ThreadWithReturnValue(target=render, args=(i,))
        threads.append(thread)
        thread.start()

    results = [thread.join() for thread in threads]

    for i, result in enumerate(results):
        expected = expected_tmpl.replace("{i}", str(i))
        print(f"---- EXPECTED {i}----")
        print(expected)
        print(f"---- RESULT {i}----")
        print(result)
        assert result == expected


def test_thread_safety_of_template_globals(folder):
    NUM_THREADS = 5
    (folder / "page.jinja").write_text(
        "{{ globalvar if globalvar is defined else 'not set' }}"
    )

    cat = Catalog(folder)

    def render(i):
        return cat.render("page.jinja", globals={"globalvar": i})

    threads = []

    for i in range(NUM_THREADS):
        thread = ThreadWithReturnValue(target=render, args=(i,))
        threads.append(thread)
        thread.start()

    results = [thread.join() for thread in threads]

    for i, result in enumerate(results):
        assert result == str(i)
