"""Example 02 — split outputs via FileTypeMap.

Run::

    uv run python examples/02_split_outputs/run.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from pycodelift import Flattener
from pycodelift.policies import FileTypeMap


HERE = Path(__file__).parent
MODULAR = HERE / "mypkg" / "child" / "modular_child.py"


def main() -> int:
    sys.path.insert(0, str(HERE))

    flattener = Flattener(
        package_name="mypkg",
        file_types=FileTypeMap({"Config": "configuration"}),
    )
    files = flattener.convert(str(MODULAR))

    for stem, source in files.items():
        print(f"--- generated {stem}_child.py ---")
        print(source.rstrip())
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
