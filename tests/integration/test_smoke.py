"""End-to-end smoke test for the Phase 2 :class:`Flattener` API.

Builds a minimal two-package fixture (``mypkg.foo`` + ``mypkg.foo2``) on
the fly, asks :class:`pycodelift.Flattener` to convert
``modular_foo2.py``, and asserts the output is non-empty and contains the
expected child class.

This is intentionally loose — we don't pin output bytes here. Byte-level
golden tests live in ``tests/corpus/`` (Phase 6).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pycodelift import Flattener


@pytest.fixture
def minimal_modular_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Lay out a minimal package and put it on ``sys.path``.

    Returns the path to the ``modular_foo2.py`` file ready for conversion.
    """
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    foo = pkg / "foo"
    foo.mkdir()
    (foo / "__init__.py").write_text("")
    (foo / "modeling_foo.py").write_text(
        textwrap.dedent(
            """
            class FooModel:
                def __init__(self, config):
                    self.config = config
                    self.x = 1

                def forward(self, x):
                    return x
            """
        )
    )

    foo2 = pkg / "foo2"
    foo2.mkdir()
    (foo2 / "__init__.py").write_text("")
    modular = foo2 / "modular_foo2.py"
    modular.write_text(
        textwrap.dedent(
            """
            from ..foo.modeling_foo import FooModel


            class Foo2Model(FooModel):
                def __init__(self, config):
                    super().__init__(config)
                    self.y = 2


            __all__ = ["Foo2Model"]
            """
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    return modular


def test_convert_returns_nonempty_dict(minimal_modular_tree: Path) -> None:
    flattener = Flattener(package_name="mypkg")
    files = flattener.convert(str(minimal_modular_tree))

    assert files, "expected at least one generated file"
    # The default file-type stem is `modeling`.
    assert "modeling" in files


def test_generated_modeling_file_contains_child_class(minimal_modular_tree: Path) -> None:
    flattener = Flattener(package_name="mypkg")
    files = flattener.convert(str(minimal_modular_tree))

    source = files["modeling"]
    assert "class Foo2Model" in source
    assert '__all__ = ["Foo2Model"]' in source


def test_describe_reflects_options() -> None:
    flattener = Flattener(package_name="mypkg")
    described = flattener.describe()
    assert described["package_name"] == "mypkg"
    assert described["flatten_levels"] == 1
    assert described["pre_body_vars"] == ["logger"]


def test_flatten_levels_other_than_one_rejected() -> None:
    with pytest.raises(NotImplementedError):
        Flattener(flatten_levels=2)


def test_write_produces_files_on_disk(
    minimal_modular_tree: Path, tmp_path: Path
) -> None:
    flattener = Flattener(package_name="mypkg")
    files = flattener.convert(str(minimal_modular_tree))

    target_dir = tmp_path / "out"
    written = Flattener.write(minimal_modular_tree, files, target_dir=target_dir)

    assert written, "expected Flattener.write to return at least one path"
    assert all(p.exists() for p in written)
    # `modeling_foo2.py` is the canonical output filename.
    assert any(p.name == "modeling_foo2.py" for p in written)
