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
import json
import pstats
import re
import sys
import sysconfig
import tempfile
import threading
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

# Every `bench()` call records into this, so `--json` and `--baseline` see the
# same numbers that were printed, with no second measuring path to drift.
RESULTS: dict[str, dict[str, float]] = {}


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
    # Keep the fastest pass, not the last. A pass can only be slowed down by
    # unrelated load on the machine, never sped up by it, so the minimum is the
    # measurement least contaminated by whatever else the OS was doing.
    prev = RESULTS.get(label)
    if prev is None or median_us < prev["med"]:
        RESULTS[label] = {"avg": avg_us, "med": median_us, "p95": p95_us}
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
# Phase runner
# ---------------------------------------------------------------------------

def run_phases(folder: Path, iterations: int) -> None:
    """One full pass over every benchmark."""
    print("\n--- Phase: Metadata extraction ---")
    bench_metadata(folder, iterations)

    print("\n--- Phase: Parsing ---")
    bench_parsing(iterations)

    print("\n--- Phase: Catalog setup ---")
    bench_catalog_setup(folder, iterations)

    print("\n--- Phase: Rendering (cached) ---")
    bench_render_simple(folder, iterations)
    bench_render_cached(folder, iterations)

    print("\n--- Phase: Rendering (auto_reload) ---")
    bench_render_auto_reload(folder, iterations)


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------

def bench_threads(folder: Path, renders: int = 400) -> None:
    """
    Render throughput as thread count rises.

    Under the GIL this is flat by construction. It is here to show what a
    free-threaded interpreter is worth to a threaded server, which is the
    scaling a pure-Python renderer can reach and a single-lock native engine
    cannot.
    """
    catalog = Catalog(folder, auto_reload=False)
    for _ in range(20):
        catalog.render("page.jx", **RENDER_KWARGS)

    def run(n_threads: int) -> float:
        per = renders // n_threads
        barrier = threading.Barrier(n_threads)

        def worker() -> None:
            barrier.wait()  # start together, so the rate covers real overlap
            for _ in range(per):
                catalog.render("page.jx", **RENDER_KWARGS)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        start = time.perf_counter()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return (per * n_threads) / (time.perf_counter() - start)

    gil = "free-threaded" if sysconfig.get_config_var("Py_GIL_DISABLED") else "GIL"
    print(f"  interpreter: {sys.version.split()[0]} ({gil})")
    base = None
    for n in (1, 2, 4, 8):
        rate = max(run(n) for _ in range(3))
        base = base or rate
        print(f"  {n} thread(s)...................................... "
              f"{rate:>9.0f} renders/s  {rate / base:>5.2f}x")


# ---------------------------------------------------------------------------
# Call counts
# ---------------------------------------------------------------------------

# Timing on a busy machine moves by ~10% run to run, which is too coarse to
# prove that a change removed work. Call counts are exact and reproducible, so
# they are what the optimisation steps are measured against; timing is the
# final check, not the per-step one.

CPROFILE_RENDERS = 500

_ADDR_RE = re.compile(r"0x[0-9a-f]+")


def collect_counts(folder: Path) -> dict[str, int]:
    """Total call counts per function for `CPROFILE_RENDERS` renders of page.jx."""
    catalog = Catalog(folder, auto_reload=False)
    catalog.render("page.jx", **RENDER_KWARGS)  # warm

    prof = cProfile.Profile()
    prof.enable()
    for _ in range(CPROFILE_RENDERS):
        catalog.render("page.jx", **RENDER_KWARGS)
    prof.disable()

    stats = pstats.Stats(prof)
    stats.strip_dirs()
    counts: dict[str, int] = {}
    total = 0
    for (filename, lineno, name), entry in stats.stats.items():  # type: ignore
        nc = entry[1]  # total calls, including recursive
        # Built-in entries carry the type object's address in their name
        # ("<built-in method __new__ of type object at 0x14f00d0>"), which would
        # make two dumps from different processes incomparable.
        key = _ADDR_RE.sub("0x...", f"{filename}:{lineno}({name})")
        counts[key] = nc
        total += nc
    counts["TOTAL"] = total
    return counts


def compare_counts(current: dict[str, int], baseline_path: Path) -> bool:
    """
    Print call-count deltas. Returns True if nothing got called more often.

    Exact equality is the rule: a count that moved without the change intending
    it is a behaviour change worth looking at, in either direction.
    """
    baseline = json.loads(baseline_path.read_text())

    print("\n" + "=" * 100)
    print(f"Call counts vs {baseline_path} ({CPROFILE_RENDERS} renders of page.jx)")
    print("=" * 100)

    keys = sorted(set(baseline) | set(current), key=lambda k: -abs(current.get(k, 0) - baseline.get(k, 0)))
    changed = [k for k in keys if current.get(k, 0) != baseline.get(k, 0)]
    if not changed:
        print("  no change")
        return True

    ok = True
    for key in changed[:30]:
        before = baseline.get(key, 0)
        after = current.get(key, 0)
        delta = after - before
        if delta > 0:
            ok = False
        print(f"  {key:.<70s} {before:>9d} -> {after:>9d}  {delta:>+9d}")
    if len(changed) > 30:
        print(f"  ... and {len(changed) - 30} more")
    return ok


# ---------------------------------------------------------------------------
# Baseline comparison
# ---------------------------------------------------------------------------

def compare_to_baseline(baseline_path: Path, threshold: float) -> bool:
    """
    Print a per-benchmark delta table against a recorded run.

    Returns True if nothing regressed by more than `threshold` percent.
    The median is compared, not the average: a single slow iteration from an
    unrelated process moves the average and says nothing about the change
    being measured.
    """
    baseline = json.loads(baseline_path.read_text())

    print("\n" + "=" * 100)
    print(f"Comparison vs {baseline_path} (median, threshold ±{threshold:.1f}%)")
    print("=" * 100)

    ok = True
    for label, current in RESULTS.items():
        before = baseline.get(label)
        if before is None:
            print(f"  {label:.<50s} {'(new)':>12s}")
            continue
        delta = (current["med"] - before["med"]) / before["med"] * 100
        if delta > threshold:
            verdict = "REGRESSED"
            ok = False
        elif delta < -threshold:
            verdict = "improved"
        else:
            verdict = "same"
        print(f"  {label:.<50s} {before['med']:>9.1f} -> {current['med']:>9.1f} µs  "
              f"{delta:>+7.1f}%  {verdict}")

    missing = set(baseline) - set(RESULTS)
    for label in sorted(missing):
        print(f"  {label:.<50s} {'(not run)':>12s}")

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Profile Jx rendering pipeline")
    parser.add_argument("--cprofile", action="store_true", help="Run cProfile analysis")
    parser.add_argument("-n", "--iterations", type=int, default=200, help="Iterations per benchmark")
    parser.add_argument("--json", type=Path, metavar="PATH", help="Write results to PATH as JSON")
    parser.add_argument("--baseline", type=Path, metavar="PATH", help="Compare results against a previous --json dump")
    parser.add_argument("--threshold", type=float, default=3.0, help="Regression threshold in percent (default: 3.0)")
    parser.add_argument("--repeat", type=int, default=3, help="Full passes to run, keeping the fastest of each (default: 3)")
    parser.add_argument("--counts", type=Path, metavar="PATH", help="Write deterministic call counts to PATH as JSON")
    parser.add_argument("--counts-baseline", type=Path, metavar="PATH", help="Compare call counts against a previous --counts dump")
    parser.add_argument("--only-counts", action="store_true", help="Skip the timing benchmarks and only do call counts")
    parser.add_argument("--threads", action="store_true", help="Measure render throughput across threads")
    args = parser.parse_args()
    ok = True
    counts_ok = True

    with tempfile.TemporaryDirectory() as tmpdir:
        folder = create_fixtures(Path(tmpdir))

        print(f"Jx profiling ({args.iterations} iterations per benchmark, "
              f"{args.repeat} pass(es))")
        print(f"Components: {len(COMPONENT_TEMPLATES)}, render items: {len(RENDER_KWARGS['items'])}")
        print("=" * 100)

        if not args.only_counts:
            for pass_no in range(1, args.repeat + 1):
                if args.repeat > 1:
                    print(f"\n{'=' * 40} pass {pass_no}/{args.repeat} {'=' * 40}")
                run_phases(folder, args.iterations)

        if args.threads:
            print("\n--- Phase: Concurrency ---")
            bench_threads(folder)

        if args.counts or args.counts_baseline:
            counts = collect_counts(folder)
            if args.counts:
                args.counts.write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n")
                print(f"\nWrote {args.counts}")
            if args.counts_baseline:
                counts_ok = compare_counts(counts, args.counts_baseline)

        if args.cprofile:
            run_cprofile(folder)

    if args.json:
        args.json.write_text(json.dumps(RESULTS, indent=2, sort_keys=True) + "\n")
        print(f"\nWrote {args.json}")

    if args.baseline:
        ok = compare_to_baseline(args.baseline, args.threshold) and ok

    print("\nDone.")
    if not (ok and counts_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
