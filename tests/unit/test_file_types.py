"""Unit tests for :mod:`pycodelift.policies.file_types`."""

from __future__ import annotations

from pycodelift.policies import FileTypeMap


def test_default_is_empty_with_modeling_default() -> None:
    m = FileTypeMap.default()
    assert dict(m.suffix_to_stem) == {}
    assert m.default_stem == "modeling"


def test_all_stems_includes_default_first() -> None:
    m = FileTypeMap({"Config": "configuration"})
    assert m.all_stems() == ("modeling", "configuration")


def test_all_stems_deduplicates() -> None:
    m = FileTypeMap(
        {"Config": "configuration", "ConfigKwargs": "configuration"},
        default_stem="modeling",
    )
    # Same stem mapped twice is reported once.
    assert m.all_stems() == ("modeling", "configuration")


def test_all_stems_preserves_insertion_order() -> None:
    m = FileTypeMap(
        {"A": "alpha", "B": "beta", "C": "gamma"},
        default_stem="modeling",
    )
    assert m.all_stems() == ("modeling", "alpha", "beta", "gamma")


def test_custom_default_stem() -> None:
    m = FileTypeMap({"Config": "configuration"}, default_stem="impl")
    assert m.all_stems()[0] == "impl"
