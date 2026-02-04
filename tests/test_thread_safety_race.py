"""
Jx | Copyright (c) Juan-Pablo Scaletti

Test for thread-safety of Catalog.components dict.

The race condition occurs in get_component_data() when auto_reload=True:
1. Thread A checks mtime, sees file changed, starts recompiling
2. Thread B checks mtime, also sees file changed, also starts recompiling
3. Both threads modify the same CData object's attributes simultaneously
4. Thread B may read partially-updated CData, getting inconsistent state

The fix uses a lock to ensure atomic check-and-update.
"""

import os
import tempfile
import threading

import pytest

from jx import Catalog


def atomic_write(path, content):
    """
    Write file atomically by writing to temp file then renaming.
    This is how real editors work and avoids partial reads.
    """
    dir_path = path.parent
    with tempfile.NamedTemporaryFile(
        mode="w", dir=dir_path, delete=False, suffix=".tmp"
    ) as f:
        f.write(content)
        temp_path = f.name
    os.replace(temp_path, path)


def test_concurrent_auto_reload_race_condition(tmp_path):
    """
    Tests thread-safety when multiple threads render a component
    while the source file is being modified (triggering auto-reload).

    Uses atomic file writes to ensure file content is never partial.
    This isolates the test to only check library thread-safety,
    not file system race conditions.
    """
    folder = tmp_path / "components"
    folder.mkdir()

    comp_file = folder / "counter.jinja"
    comp_file.write_text("{#def count=0 #}<div>{{ count }}</div>")

    catalog = Catalog(folder, auto_reload=True)

    # First render to populate cache
    catalog.render("counter.jinja")

    results = []
    errors = []
    barrier = threading.Barrier(10)

    def render_and_update(thread_id):
        """Render while file is being modified by thread 0"""
        barrier.wait()  # Sync all threads to start together
        for i in range(50):
            try:
                # Thread 0 modifies the file atomically to trigger reload
                if thread_id == 0 and i % 5 == 0:
                    atomic_write(
                        comp_file,
                        f"{{#def count=0 #}}<div>v{i}: {{{{ count }}}}</div>",
                    )

                result = catalog.render("counter.jinja", count=thread_id)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))

    threads = []
    for i in range(10):
        t = threading.Thread(target=render_and_update, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Check for exceptions that indicate race conditions
    race_errors = [
        e for _, e in errors
        if "dictionary" in str(e).lower() or "NoneType" in str(e)
    ]
    if race_errors:
        pytest.fail(f"Race condition caused exception: {race_errors[0]}")

    # Check that all renders produced valid HTML
    # Race condition causes some threads to get empty results
    invalid_results = [
        (tid, r) for tid, r in results
        if "<div>" not in str(r)
    ]
    if invalid_results:
        tid, result = invalid_results[0]
        pytest.fail(
            f"Race condition: Thread {tid} got invalid result: {result!r}\n"
            f"Total invalid results: {len(invalid_results)} out of {len(results)}"
        )
