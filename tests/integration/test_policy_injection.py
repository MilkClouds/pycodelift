"""Integration tests for the Phase 3 policy injection mechanism.

Each test exercises one policy slot through :class:`Flattener._apply_options`
and asserts the vendored module-level state is mutated *during* the
context block and exactly restored *after*.
"""

from __future__ import annotations

from pycodelift import Flattener
from pycodelift._vendor import modular_integrations as vi
from pycodelift._vendor import modular_model_converter as v
from pycodelift.policies import (
    AutoCasingRenamePolicy,
    FileTypeMap,
    TrailingCallHook,
)


def _snapshot() -> tuple:
    """Capture all vendor slots that ``_apply_options`` may mutate."""
    return (
        dict(v.CONFIG_MAPPING_NAMES),
        v.AUTO_GENERATED_MESSAGE,
        dict(v.TYPE_TO_FILE_TYPE),
        v.ALL_FILE_TYPES,
        v.VARIABLES_AT_THE_BEGINNING,
        v.IMPORTS_TO_SKIP_IN_MODULAR,
        v.TRAILING_METHOD_CALLS,
        dict(vi.EXCLUDED_EXTERNAL_FILES),
    )


def test_rename_policy_writes_casing_table() -> None:
    before = _snapshot()
    f = Flattener(rename=AutoCasingRenamePolicy({"foo": "Foo"}))
    with f._apply_options():
        assert v.CONFIG_MAPPING_NAMES == {"foo": "FooConfig"}
    assert _snapshot() == before


def test_file_types_writes_both_map_and_stems() -> None:
    before = _snapshot()
    f = Flattener(file_types=FileTypeMap({"Schema": "schema"}, default_stem="impl"))
    with f._apply_options():
        assert v.TYPE_TO_FILE_TYPE == {"Schema": "schema"}
        assert v.ALL_FILE_TYPES == ("impl", "schema")
    assert _snapshot() == before


def test_header_template_writes_string() -> None:
    before = _snapshot()
    custom = "# pycodelift {relative_path}\n"
    f = Flattener(header_template=custom)
    with f._apply_options():
        assert v.AUTO_GENERATED_MESSAGE == custom
    assert _snapshot() == before


def test_trailing_call_hook_appends_to_pattern_list() -> None:
    before = _snapshot()
    f = Flattener(post_class_hooks=(TrailingCallHook("post_init"), TrailingCallHook("post_load")))
    with f._apply_options():
        assert v.TRAILING_METHOD_CALLS == ("self.post_init(", "self.post_load(")
    assert _snapshot() == before


def test_pre_body_vars_and_skip_imports_always_pushed() -> None:
    before = _snapshot()
    f = Flattener(pre_body_vars=("logger", "_DEBUG"), skip_imports=("pkg.auto.modeling_auto",))
    with f._apply_options():
        assert v.VARIABLES_AT_THE_BEGINNING == ("logger", "_DEBUG")
        assert v.IMPORTS_TO_SKIP_IN_MODULAR == ("pkg.auto.modeling_auto",)
    assert _snapshot() == before


def test_excluded_external_files_overrides_vendor_default() -> None:
    before = _snapshot()
    f = Flattener(excluded_external_files={"mypkg": [{"name": "skip_me", "type": "modeling"}]})
    with f._apply_options():
        assert "mypkg" in vi.EXCLUDED_EXTERNAL_FILES
        # Original transformers entries are *replaced*, not merged — a
        # caller who wants both must include them explicitly.
        assert "habana" not in vi.EXCLUDED_EXTERNAL_FILES
    assert _snapshot() == before


def test_restore_runs_even_when_body_raises() -> None:
    before = _snapshot()
    f = Flattener(rename=AutoCasingRenamePolicy({"foo": "Foo"}))
    try:
        with f._apply_options():
            assert v.CONFIG_MAPPING_NAMES == {"foo": "FooConfig"}
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert _snapshot() == before


def test_default_flattener_only_rewrites_always_pushed_slots() -> None:
    """A bare Flattener() should not mutate the rename/file-type slots."""
    before = _snapshot()
    f = Flattener()
    with f._apply_options():
        # Always-pushed defaults still equal the prior value here, because
        # ``Flattener`` defaults match the vendor defaults for these
        # two slots.
        assert v.VARIABLES_AT_THE_BEGINNING[:1] == ("logger",)
    assert _snapshot() == before
