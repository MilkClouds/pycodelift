"""Unit tests for :mod:`pycodelift.policies.hooks`."""

from __future__ import annotations

from pycodelift.policies import ClassHook, TrailingCallHook


def test_trailing_call_hook_is_a_class_hook() -> None:
    hook = TrailingCallHook("post_init")
    assert isinstance(hook, ClassHook)


def test_trailing_call_hook_call_pattern() -> None:
    assert TrailingCallHook("post_init").call_pattern() == "self.post_init("
    assert TrailingCallHook("foo").call_pattern() == "self.foo("


def test_trailing_call_hook_is_frozen_and_hashable() -> None:
    h1 = TrailingCallHook("post_init")
    h2 = TrailingCallHook("post_init")
    # ``frozen=True`` dataclass — equal instances hash equal.
    assert h1 == h2
    assert {h1, h2} == {h1}
