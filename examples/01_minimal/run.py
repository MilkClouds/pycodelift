"""Driver script for example 01_minimal.

Run from the pycodelift project root::

    uv run python examples/01_minimal/run.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pycodelift import Flattener


HERE = Path(__file__).parent
MODULAR = HERE / "mypkg" / "child" / "modular_child.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write generated files alongside the modular input instead of printing.",
    )
    args = parser.parse_args()

    # Make `mypkg` importable so the engine can resolve the parent module.
    sys.path.insert(0, str(HERE))

    flattener = Flattener(package_name="mypkg")
    files = flattener.convert(str(MODULAR))

    if args.write:
        Flattener.write(MODULAR, files)
        print(f"wrote: {sorted(p.name for p in MODULAR.parent.iterdir())}")
    else:
        for stem, source in files.items():
            print(f"--- generated {stem}_child.py ---")
            print(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
