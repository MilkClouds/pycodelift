"""Hooks fired by the flattener during code generation."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class ClassHook(ABC):
    """Marker base for ``Flattener(post_class_hooks=...)`` entries."""


@dataclass(frozen=True)
class TrailingCallHook(ClassHook):
    """Force a ``self.<method>(...)`` call to be the last statement of ``__init__``.

    transformers uses ``TrailingCallHook("post_init")`` to require
    ``self.post_init()`` always at the end of an inlined ``__init__``.
    """

    method_name: str

    def call_pattern(self) -> str:
        return f"self.{self.method_name}("


@runtime_checkable
class SpecialBaseHandler(Protocol):
    """Hook for framework-specific base-class quirks (v0.1: protocol only — not yet wired)."""

    def matches(self, base_name: str) -> bool: ...


__all__ = ["ClassHook", "SpecialBaseHandler", "TrailingCallHook"]
