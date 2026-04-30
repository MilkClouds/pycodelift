"""Unit tests for the public :class:`Flattener` surface.

Exercises argument validation, ``describe()`` completeness, and the
module-level functional API. Conversion behaviour itself is covered by
``tests/integration/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycodelift import Flattener, find_priority_list
from pycodelift.policies import (
    AutoCasingRenamePolicy,
    FileTypeMap,
    HeaderTemplate,
    TrailingCallHook,
)

# -- input validation -------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "modeling_foo.py",      # missing 'modular_' prefix
        "modular_foo.txt",      # wrong suffix
        "modular_foo",          # no suffix
        "MODULAR_FOO.py",       # case-sensitive prefix
    ],
)
def test_convert_rejects_non_modular_filenames(tmp_path: Path, filename: str) -> None:
    bogus = tmp_path / filename
    bogus.write_text("")
    with pytest.raises(ValueError, match="modular_<name>.py"):
        Flattener().convert(bogus)


def test_flatten_levels_other_than_one_rejected() -> None:
    with pytest.raises(NotImplementedError):
        Flattener(flatten_levels=2)


# -- describe() -------------------------------------------------------------


def test_describe_includes_every_configured_slot() -> None:
    f = Flattener(
        package_name="mypkg",
        rename=AutoCasingRenamePolicy({"foo": "Foo"}),
        file_types=FileTypeMap({"Config": "configuration"}),
        pre_body_vars=("logger", "_X"),
        skip_imports=("auto.modeling_auto",),
        post_class_hooks=(TrailingCallHook("post_init"),),
        header_template="# {short_name}\n",
        excluded_external_files={"habana": []},
        prepend_namespace_parent=True,
    )
    desc = f.describe()

    expected_keys = {
        "package_name",
        "pre_body_vars",
        "skip_imports",
        "flatten_levels",
        "rename",
        "file_types",
        "special_bases",
        "post_class_hooks",
        "header_template",
        "prepend_namespace_parent",
        "excluded_external_files",
    }
    assert set(desc.keys()) == expected_keys
    assert desc["package_name"] == "mypkg"
    assert desc["rename"] == "AutoCasingRenamePolicy"
    assert desc["file_types"] == "FileTypeMap"
    assert desc["post_class_hooks"] == ["TrailingCallHook"]
    assert desc["header_template"] == "custom"
    assert desc["prepend_namespace_parent"] is True
    assert desc["excluded_external_files"] == ["habana"]


def test_describe_default_header_template_is_marked_default() -> None:
    assert Flattener().describe()["header_template"] == "default"


def test_describe_is_json_serializable() -> None:
    import json

    payload = json.dumps(Flattener().describe())
    assert json.loads(payload)["package_name"] == "pycodelift"


# -- repr -------------------------------------------------------------------


def test_repr_shows_package_name() -> None:
    assert repr(Flattener(package_name="x")) == "Flattener(package_name='x')"


# -- functional API ---------------------------------------------------------


def test_find_priority_list_handles_empty_input() -> None:
    levels, graph = find_priority_list([])
    assert levels == []
    assert graph == {}


# -- HeaderTemplate acceptance ----------------------------------------------


def test_header_template_accepts_HeaderTemplate_object() -> None:
    f = Flattener(header_template=HeaderTemplate("# {short_name}\n"))
    # Stored as plain string after normalization.
    assert isinstance(f.header_template, str)
    assert f.header_template == "# {short_name}\n"


def test_header_template_accepts_plain_string() -> None:
    f = Flattener(header_template="# x\n")
    assert f.header_template == "# x\n"


# -- v0.1 NotImplementedError gates -----------------------------------------


def test_special_bases_non_empty_raises() -> None:
    class _DummyHandler:
        def matches(self, base_name: str) -> bool:
            return False

    with pytest.raises(NotImplementedError, match="SpecialBase"):
        Flattener(special_bases={"X": _DummyHandler()})


# -- convert_tree on_error --------------------------------------------------


def test_convert_tree_on_error_invalid_value(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="on_error"):
        Flattener().convert_tree(tmp_path, on_error="explode")


# -- Flattener.write input validation ---------------------------------------


def test_write_rejects_non_modular_filename(tmp_path: Path) -> None:
    bogus = tmp_path / "modeling_x.py"
    bogus.write_text("")
    with pytest.raises(ValueError, match="modular_<name>.py"):
        Flattener.write(bogus, {"modeling": ""})


def test_write_rejects_non_identifier_stem(tmp_path: Path) -> None:
    modular = tmp_path / "modular_x.py"
    modular.write_text("")
    with pytest.raises(ValueError, match="not a valid identifier"):
        Flattener.write(modular, {"image_processing.*pil": ""})


# -- write helpers ----------------------------------------------------------


def test_write_defaults_to_modular_file_directory(tmp_path: Path) -> None:
    modular = tmp_path / "modular_x.py"
    modular.write_text("")
    written = Flattener.write(modular, {"modeling": "# generated\n"})
    assert written == [tmp_path / "modeling_x.py"]
    assert (tmp_path / "modeling_x.py").read_text() == "# generated\n"


def test_write_creates_target_dir_if_missing(tmp_path: Path) -> None:
    modular = tmp_path / "modular_x.py"
    modular.write_text("")
    out_dir = tmp_path / "deep" / "nested" / "out"
    written = Flattener.write(modular, {"modeling": "# x\n"}, target_dir=out_dir)
    assert all(p.exists() for p in written)
    assert out_dir.is_dir()


def test_write_handles_multi_stem_dict(tmp_path: Path) -> None:
    modular = tmp_path / "modular_x.py"
    modular.write_text("")
    written = Flattener.write(
        modular,
        {"modeling": "# m\n", "configuration": "# c\n"},
    )
    names = sorted(p.name for p in written)
    assert names == ["configuration_x.py", "modeling_x.py"]
