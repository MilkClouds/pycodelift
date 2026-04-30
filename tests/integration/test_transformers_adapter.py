"""Integration tests for :mod:`pycodelift.adapters.transformers`.

These verify that ``make_transformers_flattener()`` wires up the
expected vendor module-level state. Byte-equivalence regression tests
against the transformers golden corpus live in ``tests/corpus/``
(Phase 6).
"""

from __future__ import annotations

from pycodelift._vendor import modular_integrations as vi
from pycodelift._vendor import modular_model_converter as v
from pycodelift.adapters.transformers import (
    TRANSFORMERS_AUTO_GENERATED_MESSAGE,
    TRANSFORMERS_PRE_BODY_VARS,
    TRANSFORMERS_SKIP_IMPORTS,
    TRANSFORMERS_TYPE_TO_FILE_TYPE,
    load_transformers_casing_table,
    make_transformers_flattener,
)


def test_make_transformers_flattener_returns_configured_flattener() -> None:
    f = make_transformers_flattener(casing_table={"olmo": "OlmoConfig"})
    described = f.describe()
    assert described["package_name"] == "transformers"
    assert described["rename"] == "AutoCasingRenamePolicy"
    assert described["file_types"] == "FileTypeMap"
    assert "TrailingCallHook" in described["post_class_hooks"]


def test_apply_options_writes_transformers_specific_state() -> None:
    f = make_transformers_flattener(casing_table={"olmo": "OlmoConfig"})
    with f._apply_options():
        # casing table propagates verbatim (already had Config suffix).
        assert v.CONFIG_MAPPING_NAMES == {"olmo": "OlmoConfig"}

        # transformers' file-type splitting in place.
        assert v.TYPE_TO_FILE_TYPE["Config"] == "configuration"
        assert v.TYPE_TO_FILE_TYPE["Tokenizer"] == "tokenization"

        # transformers' pre-body variables.
        assert v.VARIABLES_AT_THE_BEGINNING == TRANSFORMERS_PRE_BODY_VARS

        # transformers' skip-list.
        assert v.IMPORTS_TO_SKIP_IN_MODULAR == TRANSFORMERS_SKIP_IMPORTS

        # post_init trailing rule active.
        assert v.TRAILING_METHOD_CALLS == ("self.post_init(",)

        # banner is transformers' verbatim string.
        assert v.AUTO_GENERATED_MESSAGE == TRANSFORMERS_AUTO_GENERATED_MESSAGE

        # namespace prefix heuristic is re-enabled.
        assert vi.PREPEND_NAMESPACE_PARENT is True

        # habana exclusions present.
        assert "habana" in vi.EXCLUDED_EXTERNAL_FILES


def test_state_is_restored_after_context() -> None:
    snapshot_before = (
        dict(v.CONFIG_MAPPING_NAMES),
        v.AUTO_GENERATED_MESSAGE,
        dict(v.TYPE_TO_FILE_TYPE),
        v.ALL_FILE_TYPES,
        v.VARIABLES_AT_THE_BEGINNING,
        v.IMPORTS_TO_SKIP_IN_MODULAR,
        v.TRAILING_METHOD_CALLS,
        dict(vi.EXCLUDED_EXTERNAL_FILES),
        vi.PREPEND_NAMESPACE_PARENT,
    )

    f = make_transformers_flattener(casing_table={"olmo": "OlmoConfig"})
    with f._apply_options():
        pass

    snapshot_after = (
        dict(v.CONFIG_MAPPING_NAMES),
        v.AUTO_GENERATED_MESSAGE,
        dict(v.TYPE_TO_FILE_TYPE),
        v.ALL_FILE_TYPES,
        v.VARIABLES_AT_THE_BEGINNING,
        v.IMPORTS_TO_SKIP_IN_MODULAR,
        v.TRAILING_METHOD_CALLS,
        dict(vi.EXCLUDED_EXTERNAL_FILES),
        vi.PREPEND_NAMESPACE_PARENT,
    )
    assert snapshot_before == snapshot_after


def test_load_casing_table_returns_empty_when_transformers_missing(monkeypatch) -> None:
    """If transformers is unimportable, the loader falls back to empty dict."""

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("transformers"):
            raise ImportError("simulated absence")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert load_transformers_casing_table() == {}


def test_constants_are_consistent() -> None:
    """Public constants exposed by the adapter must match what it pushes."""
    assert "Config" in TRANSFORMERS_TYPE_TO_FILE_TYPE
    assert TRANSFORMERS_TYPE_TO_FILE_TYPE["Config"] == "configuration"
    assert "auto.modeling_auto" in TRANSFORMERS_SKIP_IMPORTS
    # The banner is loaded from the vendor module, so it must contain the
    # placeholder slots the engine .format()s into.
    assert "{relative_path}" in TRANSFORMERS_AUTO_GENERATED_MESSAGE
    assert "{short_name}" in TRANSFORMERS_AUTO_GENERATED_MESSAGE
