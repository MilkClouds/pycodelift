"""File-type splitting policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class FileTypeMap:
    """Map a class-name suffix to an output-file stem.

    ``FileTypeMap({"Config": "configuration"})`` routes ``FooConfig`` to
    ``configuration_foo.py``. Classes without a registered suffix fall
    into ``default_stem``.
    """

    suffix_to_stem: Mapping[str, str] = field(default_factory=dict)
    default_stem: str = "modeling"

    @classmethod
    def default(cls) -> "FileTypeMap":
        return cls()

    def all_stems(self) -> tuple[str, ...]:
        """Every stem this map can produce, default first."""
        seen = [self.default_stem]
        for stem in self.suffix_to_stem.values():
            if stem not in seen:
                seen.append(stem)
        return tuple(seen)


__all__ = ["FileTypeMap"]
