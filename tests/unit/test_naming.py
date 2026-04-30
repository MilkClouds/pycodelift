"""Unit tests for :mod:`pycodelift.policies.naming`."""

from __future__ import annotations

import pytest

from pycodelift.policies import AutoCasingRenamePolicy, RenamePolicy


def test_default_table_is_empty() -> None:
    p = AutoCasingRenamePolicy()
    assert dict(p.casing_table) == {}


def test_to_vendor_table_appends_config_suffix() -> None:
    p = AutoCasingRenamePolicy({"foo": "Foo"})
    assert p.to_vendor_table() == {"foo": "FooConfig"}


def test_to_vendor_table_idempotent_when_value_already_has_config_suffix() -> None:
    p = AutoCasingRenamePolicy({"foo": "FooConfig"})
    assert p.to_vendor_table() == {"foo": "FooConfig"}


def test_acronym_entries_are_preserved() -> None:
    p = AutoCasingRenamePolicy({"got_ocr2": "GotOcr2"})
    assert p.to_vendor_table() == {"got_ocr2": "GotOcr2Config"}


def test_satisfies_renamepolicy_protocol() -> None:
    # ``runtime_checkable`` Protocol — instance check works at runtime.
    assert isinstance(AutoCasingRenamePolicy(), RenamePolicy)


def test_to_vendor_table_returns_new_mapping() -> None:
    """Calling twice should not double-suffix; each call recomputes."""
    p = AutoCasingRenamePolicy({"foo": "Foo"})
    once = p.to_vendor_table()
    twice = p.to_vendor_table()
    assert once == twice == {"foo": "FooConfig"}


@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("Foo", "FooConfig"),
        ("FooConfig", "FooConfig"),
        ("Foo2", "Foo2Config"),
    ],
)
def test_suffix_normalization_table(input_value: str, expected: str) -> None:
    p = AutoCasingRenamePolicy({"foo": input_value})
    assert p.to_vendor_table()["foo"] == expected
