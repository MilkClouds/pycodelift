"""Renaming policies for the case-preserving identifier rewrite pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable


@runtime_checkable
class RenamePolicy(Protocol):
    """Surface read by :class:`pycodelift.Flattener`.

    Implementations expose ``casing_table``: snake_case → canonical
    PascalCase. Used to override irregular casing (acronyms, etc.);
    standard derivation handles everything else.
    """

    @property
    def casing_table(self) -> Mapping[str, str]: ...


@dataclass
class AutoCasingRenamePolicy:
    """Default: empty table → standard snake↔Pascal derivation.

    Pass ``casing_table`` for irregular cases:
        AutoCasingRenamePolicy({"got_ocr2": "GotOcr2"})

    Values get a trailing ``"Config"`` appended when fed to the engine
    (transformers' historical convention); :meth:`to_vendor_table`
    handles that idempotently.
    """

    casing_table: Mapping[str, str] = field(default_factory=dict)

    def to_vendor_table(self) -> dict[str, str]:
        return {
            k: v if v.endswith("Config") else f"{v}Config"
            for k, v in self.casing_table.items()
        }


__all__ = ["AutoCasingRenamePolicy", "RenamePolicy"]
