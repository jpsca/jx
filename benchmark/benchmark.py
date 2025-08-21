import timeit
from pathlib import Path

from jx import Catalog


NUMBER = 10_000
FOLDER = Path(__file__).parent / "views"
catalog = Catalog()


def render_jx():
    catalog.render("main.jinja", message="Hey there")


def benchmark():
    time = timeit.timeit(render_jx, number=NUMBER)
    print(f"{(time / NUMBER):.12f}s per render ({(1_000_000 * time / NUMBER):.0f}µs), {time:.1f}s total\n")


def benchmark_with_auto_reload():
    print(f"WITH AUTO-RELOAD: {NUMBER:_} renders...")
    catalog.auto_reload = True
    catalog.components = {}
    catalog.add_folder(FOLDER)
    benchmark()


def benchmark_without_auto_reload():
    print(f"WITHOUT AUTO-RELOAD: {NUMBER:_} renders...")
    catalog.auto_reload = False
    catalog.components = {}
    catalog.add_folder(FOLDER)
    benchmark()


if __name__ == "__main__":
    print("Benchmarking...\n")
    benchmark_with_auto_reload()
    benchmark_without_auto_reload()
