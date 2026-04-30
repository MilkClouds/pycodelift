"""Example 03 — transformers compatibility adapter.

Run::

    uv run python examples/03_transformers_compat/run.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from pycodelift.adapters.transformers import make_transformers_flattener


HERE = Path(__file__).parent
MODULAR = HERE / "src" / "mypkg" / "child" / "modular_child.py"


def main() -> int:
    # The transformers adapter enables ``prepend_namespace_parent`` — the
    # parent of the package directory is added to absolute imports unless
    # it's named ``src`` (transformers' own layout). We mirror that
    # convention here so the example doesn't trigger the namespace prefix.
    sys.path.insert(0, str(HERE / "src"))

    # ``package_name`` overrides default "transformers" so the engine
    # treats the surrounding directory as the package root.
    flattener = make_transformers_flattener(package_name="mypkg")
    files = flattener.convert(str(MODULAR))

    for stem, source in files.items():
        print(f"--- generated {stem}_child.py ---")
        print(source.rstrip())
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
