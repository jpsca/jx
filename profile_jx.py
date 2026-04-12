"""
Profiling script for Jx.

Measures time for each phase of the pipeline:
  1. Catalog setup & folder scanning
  2. Metadata extraction
  3. Parsing (TitleCased tag → Jinja2 call transformation)
  4. Jinja2 compilation
  5. Rendering (cached, no recompile)

Usage:
    uv run python profile_jx.py
    uv run python profile_jx.py --cprofile   # deterministic cProfile dump
"""

import argparse
import cProfile
import pstats
import tempfile
import time
import typing as t
from pathlib import Path

from jx import Catalog
from jx.meta import extract_metadata
from jx.parser import JxParser


# ---------------------------------------------------------------------------
# Fixture helpers — build a realistic component tree on disk
# ---------------------------------------------------------------------------

COMPONENT_TEMPLATES = {
    "icon.jx": """\
{# def name: str, size: str = "md" #}
{# css "icon.css" #}
<svg class="icon icon-{{ size }}"><use href="#{{ name }}"></use></svg>
""",
    "button.jx": """\
{# def bid: str, text: str = "Click", variant: str = "primary", disabled: bool = False #}
{# import "icon.jx" as Icon #}
{# css "button.css" #}
{# js "button.js" #}
<button id="{{ bid }}" class="btn btn-{{ variant }}" {{ attrs.render(disabled=disabled) }}>
  <Icon name="check" size="sm" />
  {{ text }}
</button>
""",
    "input.jx": """\
{# def name: str, label: str = "", type: str = "text", value: str = "", required: bool = False #}
{# css "input.css" #}
<label class="input-label" for="{{ name }}">{{ label }}</label>
<input id="{{ name }}" name="{{ name }}" type="{{ type }}" value="{{ value }}" {{ attrs.render(required=required) }}>
""",
    "card.jx": """\
{# def title: str, subtitle: str = "" #}
{# css "card.css" #}
<div class="card" {{ attrs.render() }}>
  <div class="card-header">
    <h3>{{ title }}</h3>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  </div>
  <div class="card-body">
    {{ content }}
  </div>
  {% slot footer %}{% endslot %}
</div>
""",
    "nav.jx": """\
{# def items: list, active: str = "" #}
{# css "nav.css" #}
{# js "nav.js" #}
<nav class="nav" {{ attrs.render() }}>
  <ul>
    {% for item in items %}
    <li class="{% if item == active %}active{% endif %}">
      <a href="/{{ item }}">{{ item | title }}</a>
    </li>
    {% endfor %}
  </ul>
</nav>
""",
    "form.jx": """\
{# def action: str, method: str = "post" #}
{# import "input.jx" as Input #}
{# import "button.jx" as Button #}
{# css "form.css" #}
{# js "form.js" #}
<form action="{{ action }}" method="{{ method }}" {{ attrs.render() }}>
  <Input name="email" label="Email" type="email" required />
  <Input name="password" label="Password" type="password" required />
  <Button bid="submit-btn" text="Submit" variant="primary" />
  {{ content }}
</form>
""",
    "alert.jx": """\
{# def message: str, level: str = "info" #}
{# import "icon.jx" as Icon #}
{# css "alert.css" #}
<div class="alert alert-{{ level }}" role="alert" {{ attrs.render() }}>
  <Icon name="{{ level }}" />
  <span>{{ message }}</span>
</div>
""",
    "sidebar.jx": """\
{# def title: str = "Menu" #}
{# import "nav.jx" as Nav #}
{# css "sidebar.css" #}
<aside class="sidebar" {{ attrs.render() }}>
  <h2>{{ title }}</h2>
  <Nav items={{ ["home", "about", "settings", "profile", "help"] }} active="home" />
  {{ content }}
</aside>
""",
    "layout.jx": """\
{# def title: str = "Page" #}
{# import "sidebar.jx" as Sidebar #}
{# import "alert.jx" as Alert #}
{# css "layout.css" #}
{# js "layout.js" #}
{{ assets.render() }}
<div class="layout">
  <header><h1>{{ title }}</h1></header>
  <Sidebar />
  <main>
    <Alert message="Welcome back!" level="info" />
    {{ content }}
  </main>
  {% slot footer %}<footer>Default footer</footer>{% endslot %}
</div>
""",
    "page.jx": """\
{# def title: str, items: list, user: str = "Guest" #}
{# import "layout.jx" as Layout #}
{# import "card.jx" as Card #}
{# import "form.jx" as Form #}
{# import "button.jx" as Button #}
{# css "page.css" #}
{# js "page.js" #}
<Layout title={{ title }}>
  <h2>Hello {{ user }}</h2>
  {% for item in items %}
  <Card title={{ item.title }} subtitle={{ item.subtitle }}>
    <p>{{ item.body }}</p>
    {% fill footer %}
    <div class="card-footer">
      <Button bid="action-{{ loop.index }}" text="View" variant="secondary" />
    </div>
    {% endfill %}
  </Card>
  {% endfor %}
  <Form action="/submit" class="mt-4" />
</Layout>
""",
}

RENDER_KWARGS: dict[str, t.Any] = {
    "title": "Dashboard",
    "user": "Alice",
    "items": [
        {"title": f"Item {i}", "subtitle": f"Sub {i}", "body": f"Body text for item {i}."}
        for i in range(20)
    ],
}


def create_fixtures(base: Path) -> Path:
    folder = base / "components"
    folder.mkdir(parents=True, exist_ok=True)
    for name, source in COMPONENT_TEMPLATES.items():
        (folder / name).write_text(source)
    return folder


# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------

def bench(label: str, fn, *args, iterations: int = 100, **kwargs):
    """Run fn(args, kwargs) `iterations` times and print stats."""
    # Warm-up
    result = fn(*args, **kwargs)

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn(*args, **kwargs)
        times.append(time.perf_counter_ns() - t0)

    times.sort()
    median = times[len(times) // 2]
    p95 = times[int(len(times) * 0.95)]
    total_ms = sum(times) / 1_000_000
    avg_us = (sum(times) / len(times)) / 1_000
    median_us = median / 1_000
    p95_us = p95 / 1_000

    print(f"  {label:.<50s} avg {avg_us:>9.1f} µs  "
          f"med {median_us:>9.1f} µs  p95 {p95_us:>9.1f} µs  "
          f"({iterations} iters, {total_ms:.1f} ms total)")
    return result


# ---------------------------------------------------------------------------
# Individual phase benchmarks
# ---------------------------------------------------------------------------

def bench_metadata(folder: Path, iterations: int):
    """Benchmark metadata extraction alone."""
    sources = {}
    for name, src in COMPONENT_TEMPLATES.items():
        sources[name] = (src, folder, folder / name)

    def run():
        for _name, (src, base, full) in sources.items():
            extract_metadata(src, base_path=base, fullpath=full)

    bench("metadata extraction (all components)", run, iterations=iterations)


def bench_parsing(iterations: int):
    """Benchmark parser transformation alone."""
    # Pre-extract metadata to get import names
    for name, src in COMPONENT_TEMPLATES.items():
        meta = extract_metadata(src, base_path=Path(), fullpath=Path())
        components = list(meta.imports.keys())

        def run(s=src, n=name, c=components):
            parser = JxParser(name=n, source=s, components=c)
            parser.parse()

        bench(f"parse {name}", run, iterations=iterations)


def bench_catalog_setup(folder: Path, iterations: int):
    """Benchmark catalog creation + folder scan."""
    def run():
        Catalog(folder, auto_reload=False)

    bench("catalog setup (scan)", run, iterations=iterations)


def bench_render_cached(folder: Path, iterations: int):
    """Benchmark rendering with fully cached/compiled templates."""
    catalog = Catalog(folder, auto_reload=False)
    # Warm up
    catalog.render("page.jx", **RENDER_KWARGS)

    def run():
        catalog.render("page.jx", **RENDER_KWARGS)

    bench("render page.jx (cached)", run, iterations=iterations)


def bench_render_simple(folder: Path, iterations: int):
    """Benchmark rendering a simple leaf component."""
    catalog = Catalog(folder, auto_reload=False)
    catalog.render("button.jx", bid="b1", text="Go")

    def run():
        catalog.render("button.jx", bid="b1", text="Go")

    bench("render button.jx (cached)", run, iterations=iterations)


def bench_render_auto_reload(folder: Path, iterations: int):
    """Benchmark rendering with auto_reload=True (mtime checks)."""
    catalog = Catalog(folder, auto_reload=True)
    catalog.render("page.jx", **RENDER_KWARGS)

    def run():
        catalog.render("page.jx", **RENDER_KWARGS)

    bench("render page.jx (auto_reload)", run, iterations=iterations)


# ---------------------------------------------------------------------------
# cProfile-based profiling
# ---------------------------------------------------------------------------

def run_cprofile(folder: Path):
    """Run cProfile on a representative workload and print top functions."""
    catalog = Catalog(folder, auto_reload=False)
    catalog.render("page.jx", **RENDER_KWARGS)  # warm up

    prof = cProfile.Profile()
    prof.enable()
    for _ in range(500):
        catalog.render("page.jx", **RENDER_KWARGS)
    prof.disable()

    print("\n" + "=" * 80)
    print("cProfile results (500 cached renders of page.jx)")
    print("=" * 80)
    stats = pstats.Stats(prof)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(40)
    print()
    stats.sort_stats("tottime")
    stats.print_stats(40)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Profile Jx rendering pipeline")
    parser.add_argument("--cprofile", action="store_true", help="Run cProfile analysis")
    parser.add_argument("-n", "--iterations", type=int, default=200, help="Iterations per benchmark")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        folder = create_fixtures(Path(tmpdir))

        print(f"Jx profiling ({args.iterations} iterations per benchmark)")
        print(f"Components: {len(COMPONENT_TEMPLATES)}, render items: {len(RENDER_KWARGS['items'])}")
        print("=" * 100)

        print("\n--- Phase: Metadata extraction ---")
        bench_metadata(folder, args.iterations)

        print("\n--- Phase: Parsing ---")
        bench_parsing(args.iterations)

        print("\n--- Phase: Catalog setup ---")
        bench_catalog_setup(folder, args.iterations)

        print("\n--- Phase: Rendering (cached) ---")
        bench_render_simple(folder, args.iterations)
        bench_render_cached(folder, args.iterations)

        print("\n--- Phase: Rendering (auto_reload) ---")
        bench_render_auto_reload(folder, args.iterations)

        if args.cprofile:
            run_cprofile(folder)

    print("\nDone.")


if __name__ == "__main__":
    main()
