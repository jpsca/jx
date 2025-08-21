from pathlib import Path

from jx import Catalog
from jx.component import Component

from line_profiler import LineProfiler


HERE = Path(__file__).parent

catalog = Catalog(auto_reload=False)
catalog.add_folder(HERE / "views")

profile = LineProfiler(
    Catalog.render,
    Catalog.get_component,
    Catalog.get_component_data,
    Component.__init__,
    Component.filter_attrs,
    Component.render,
)

def render_jx():
    for _ in range(10_000):
        catalog.render("main.jinja", message="Hey there")


if __name__ == "__main__":
    print("Profiling...")
    profile.runcall(render_jx)
    profile.print_stats()
