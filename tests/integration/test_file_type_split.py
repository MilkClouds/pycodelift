"""Integration test: when a :class:`FileTypeMap` is supplied, classes whose
names end in a registered suffix land in a separate generated file.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pycodelift import Flattener
from pycodelift.policies import FileTypeMap


@pytest.fixture
def split_modular_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    pkg = tmp_path / "mypkg"
    (pkg / "foo").mkdir(parents=True)
    (pkg / "foo2").mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "foo" / "__init__.py").write_text("")
    (pkg / "foo2" / "__init__.py").write_text("")

    (pkg / "foo" / "configuration_foo.py").write_text(
        textwrap.dedent(
            """
            class FooConfig:
                model_type = "foo"
                hidden_size = 768
            """
        )
    )
    (pkg / "foo" / "modeling_foo.py").write_text(
        textwrap.dedent(
            """
            class FooModel:
                def __init__(self, config):
                    self.config = config
            """
        )
    )

    modular = pkg / "foo2" / "modular_foo2.py"
    modular.write_text(
        textwrap.dedent(
            """
            from ..foo.configuration_foo import FooConfig
            from ..foo.modeling_foo import FooModel


            class Foo2Config(FooConfig):
                model_type = "foo2"
                rms_norm_eps = 1e-5


            class Foo2Model(FooModel):
                pass


            __all__ = ["Foo2Config", "Foo2Model"]
            """
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    return modular


def test_config_class_splits_into_configuration_file(split_modular_tree: Path) -> None:
    flattener = Flattener(
        package_name="mypkg",
        file_types=FileTypeMap({"Config": "configuration"}),
    )
    files = flattener.convert(str(split_modular_tree))

    # Both stems present.
    assert "modeling" in files
    assert "configuration" in files

    # Each class lands in the right file.
    assert "class Foo2Config" in files["configuration"]
    assert "class Foo2Model" in files["modeling"]

    # And not in the wrong one.
    assert "class Foo2Model" not in files["configuration"]
    assert "class Foo2Config" not in files["modeling"]


def test_unsplit_default_keeps_everything_in_modeling(split_modular_tree: Path) -> None:
    """Without a FileTypeMap, all classes share the default ``modeling`` stem."""
    flattener = Flattener(package_name="mypkg")
    files = flattener.convert(str(split_modular_tree))

    assert set(files.keys()) == {"modeling"}
    assert "class Foo2Config" in files["modeling"]
    assert "class Foo2Model" in files["modeling"]
