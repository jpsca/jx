"""
Benchmark comparison: Jx vs JinjaX

Renders equivalent component trees and compares timings.

Usage:
    uv run python bench_compare.py
"""

import tempfile
import time
import typing as t
from pathlib import Path

from jx import Catalog as JxCatalog

import jinjax

# ---------------------------------------------------------------------------
# Jx templates (use {# import #} for child components)
# ---------------------------------------------------------------------------

JX_TEMPLATES: dict[str, str] = {
    "icon.jinja": """\
{# def name: str, size: str = "md" #}
<svg class="icon icon-{{ size }}"><use href="#{{ name }}"></use></svg>""",

    "button.jinja": """\
{# def bid: str, text: str = "Click", variant: str = "primary", disabled: bool = False #}
{# import "icon.jinja" as Icon #}
<button id="{{ bid }}" class="btn btn-{{ variant }}">
  <Icon name="check" size="sm" />
  {{ text }}
</button>""",

    "input.jinja": """\
{# def name: str, label: str = "", input_type: str = "text", value: str = "" #}
<label class="input-label" for="{{ name }}">{{ label }}</label>
<input id="{{ name }}" name="{{ name }}" type="{{ input_type }}" value="{{ value }}">""",

    "card.jinja": """\
{# def title: str, subtitle: str = "" #}
<div class="card">
  <div class="card-header">
    <h3>{{ title }}</h3>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  </div>
  <div class="card-body">{{ content }}</div>
</div>""",

    "nav.jinja": """\
{# def items: list, active: str = "" #}
<nav class="nav">
  <ul>
    {% for item in items %}
    <li class="{% if item == active %}active{% endif %}">
      <a href="/{{ item }}">{{ item | title }}</a>
    </li>
    {% endfor %}
  </ul>
</nav>""",

    "form.jinja": """\
{# def action: str, method: str = "post" #}
{# import "input.jinja" as Input #}
{# import "button.jinja" as Button #}
<form action="{{ action }}" method="{{ method }}">
  <Input name="email" label="Email" input_type="email" />
  <Input name="password" label="Password" input_type="password" />
  <Button bid="submit-btn" text="Submit" variant="primary" />
</form>""",

    "alert.jinja": """\
{# def message: str, level: str = "info" #}
{# import "icon.jinja" as Icon #}
<div class="alert alert-{{ level }}" role="alert">
  <Icon name="{{ level }}" />
  <span>{{ message }}</span>
</div>""",

    "sidebar.jinja": """\
{# def title: str = "Menu" #}
{# import "nav.jinja" as Nav #}
<aside class="sidebar">
  <h2>{{ title }}</h2>
  <Nav items={{ ["home", "about", "settings", "profile", "help"] }} active="home" />
</aside>""",

    "layout.jinja": """\
{# def title: str = "Page" #}
{# import "sidebar.jinja" as Sidebar #}
{# import "alert.jinja" as Alert #}
<div class="layout">
  <header><h1>{{ title }}</h1></header>
  <Sidebar />
  <main>
    <Alert message="Welcome back!" level="info" />
    {{ content }}
  </main>
</div>""",

    "page.jinja": """\
{# def title: str, items: list, user: str = "Guest" #}
{# import "layout.jinja" as Layout #}
{# import "card.jinja" as Card #}
{# import "form.jinja" as Form #}
{# import "button.jinja" as Button #}
<Layout title={{ title }}>
  <h2>Hello {{ user }}</h2>
  {% for item in items %}
  <Card title={{ item.title }} subtitle={{ item.subtitle }}>
    <p>{{ item.body }}</p>
  </Card>
  {% endfor %}
  <Form action="/submit" />
</Layout>""",
}

# ---------------------------------------------------------------------------
# JinjaX templates (components discovered by filename, no import needed)
# ---------------------------------------------------------------------------

JINJAX_TEMPLATES: dict[str, str] = {
    "Icon.jinja": """\
{#def name, size="md" #}
<svg class="icon icon-{{ size }}"><use href="#{{ name }}"></use></svg>""",

    "Button.jinja": """\
{#def bid, text="Click", variant="primary", disabled=False #}
<button id="{{ bid }}" class="btn btn-{{ variant }}">
  <Icon name="check" size="sm" />
  {{ text }}
</button>""",

    "Input.jinja": """\
{#def name, label="", input_type="text", value="" #}
<label class="input-label" for="{{ name }}">{{ label }}</label>
<input id="{{ name }}" name="{{ name }}" type="{{ input_type }}" value="{{ value }}">""",

    "Card.jinja": """\
{#def title, subtitle="" #}
<div class="card">
  <div class="card-header">
    <h3>{{ title }}</h3>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  </div>
  <div class="card-body">{{ content }}</div>
</div>""",

    "Nav.jinja": """\
{#def items, active="" #}
<nav class="nav">
  <ul>
    {% for item in items %}
    <li class="{% if item == active %}active{% endif %}">
      <a href="/{{ item }}">{{ item | title }}</a>
    </li>
    {% endfor %}
  </ul>
</nav>""",

    "Form.jinja": """\
{#def action, method="post" #}
<form action="{{ action }}" method="{{ method }}">
  <Input name="email" label="Email" input_type="email" />
  <Input name="password" label="Password" input_type="password" />
  <Button bid="submit-btn" text="Submit" variant="primary" />
</form>""",

    "Alert.jinja": """\
{#def message, level="info" #}
<div class="alert alert-{{ level }}" role="alert">
  <Icon name="{{ level }}" />
  <span>{{ message }}</span>
</div>""",

    "Sidebar.jinja": """\
{#def title="Menu" #}
<aside class="sidebar">
  <h2>{{ title }}</h2>
  <Nav items={{ ["home", "about", "settings", "profile", "help"] }} active="home" />
</aside>""",

    "Layout.jinja": """\
{#def title="Page" #}
<div class="layout">
  <header><h1>{{ title }}</h1></header>
  <Sidebar />
  <main>
    <Alert message="Welcome back!" level="info" />
    {{ content }}
  </main>
</div>""",

    "Page.jinja": """\
{#def title, items, user="Guest" #}
<Layout title={{ title }}>
  <h2>Hello {{ user }}</h2>
  {% for item in items %}
  <Card title={{ item.title }} subtitle={{ item.subtitle }}>
    <p>{{ item.body }}</p>
  </Card>
  {% endfor %}
  <Form action="/submit" />
</Layout>""",
}


# ---------------------------------------------------------------------------
# Shared render kwargs
# ---------------------------------------------------------------------------

RENDER_KWARGS: dict[str, t.Any] = {
    "title": "Dashboard",
    "user": "Alice",
    "items": [
        {"title": f"Item {i}", "subtitle": f"Sub {i}", "body": f"Body text for item {i}."}
        for i in range(20)
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_templates(base: Path, templates: dict[str, str]) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    for name, src in templates.items():
        (base / name).write_text(src)
    return base


def bench(label: str, fn, iterations: int = 500) -> float:
    # Warm up
    fn()

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn()
        times.append(time.perf_counter_ns() - t0)

    times.sort()
    median = times[len(times) // 2]
    p95 = times[int(len(times) * 0.95)]
    avg_us = (sum(times) / len(times)) / 1_000
    median_us = median / 1_000
    p95_us = p95 / 1_000

    print(f"  {label:.<55s} avg {avg_us:>8.1f} µs  "
          f"med {median_us:>8.1f} µs  p95 {p95_us:>8.1f} µs")
    return median_us


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    iterations = 500

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        jx_folder = write_templates(base / "jx", JX_TEMPLATES)
        jinjax_folder = write_templates(base / "jinjax", JINJAX_TEMPLATES)

        # ---- Setup ----
        jx_cat = JxCatalog(jx_folder, auto_reload=False)
        jinjax_cat = jinjax.Catalog(use_cache=True, auto_reload=False)
        jinjax_cat.add_folder(jinjax_folder)

        # Verify both produce similar output
        jx_html = jx_cat.render("page.jinja", **RENDER_KWARGS)
        jinjax_html = jinjax_cat.render("Page", **RENDER_KWARGS)

        # Quick sanity check
        for marker in ["Hello Alice", "Item 0", "Item 19", "btn btn-primary", "icon icon-sm"]:
            assert marker in jx_html, f"Jx output missing: {marker}"
            assert marker in jinjax_html, f"JinjaX output missing: {marker}"

        print("=" * 90)
        print(f"Benchmark: Jx vs JinjaX ({iterations} iterations)")
        print(f"Components: 10, items in loop: {len(RENDER_KWARGS['items'])}")
        print("=" * 90)

        # ---- Simple component ----
        print("\n--- Simple component (Button) ---")
        jx_simple = bench(
            "Jx    render button",
            lambda: jx_cat.render("button.jinja", bid="b1", text="Go"),
            iterations=iterations,
        )
        jinjax_simple = bench(
            "JinjaX render Button",
            lambda: jinjax_cat.render("Button", bid="b1", text="Go"),
            iterations=iterations,
        )
        ratio = jinjax_simple / jx_simple if jx_simple else float("inf")
        print(f"  -> Jx is {ratio:.1f}x {'faster' if ratio > 1 else 'slower'}")

        # ---- Full page ----
        print("\n--- Full page (10 components, 20 loop items) ---")
        jx_page = bench(
            "Jx    render page",
            lambda: jx_cat.render("page.jinja", **RENDER_KWARGS),
            iterations=iterations,
        )
        jinjax_page = bench(
            "JinjaX render Page",
            lambda: jinjax_cat.render("Page", **RENDER_KWARGS),
            iterations=iterations,
        )
        ratio = jinjax_page / jx_page if jx_page else float("inf")
        print(f"  -> Jx is {ratio:.1f}x {'faster' if ratio > 1 else 'slower'}")

        # ---- Catalog setup ----
        print("\n--- Catalog setup (folder scan) ---")

        def jx_setup():
            c = JxCatalog(jx_folder, auto_reload=False)

        def jinjax_setup():
            c = jinjax.Catalog(use_cache=True, auto_reload=False)
            c.add_folder(jinjax_folder)

        bench("Jx catalog setup", jx_setup, iterations=200)
        bench("JinjaX catalog setup", jinjax_setup, iterations=200)

    print("\nDone.")


if __name__ == "__main__":
    main()
