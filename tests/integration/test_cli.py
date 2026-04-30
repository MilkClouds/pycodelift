"""Integration tests for the ``pycodelift`` CLI.

We invoke :func:`pycodelift.cli.main` directly with a list of args (no
subprocess) so coverage tracks both the CLI and the engine, and so the
tests stay fast.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from pycodelift.cli import main


@pytest.fixture
def modular_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    pkg = tmp_path / "mypkg"
    (pkg / "foo").mkdir(parents=True)
    (pkg / "foo2").mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "foo" / "__init__.py").write_text("")
    (pkg / "foo2" / "__init__.py").write_text("")
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
            from ..foo.modeling_foo import FooModel

            class Foo2Model(FooModel):
                pass

            __all__ = ["Foo2Model"]
            """
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    return modular


def test_convert_prints_to_stdout(modular_fixture: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["convert", "--package", "mypkg", str(modular_fixture)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "========= modeling =========" in captured.out
    assert "class Foo2Model" in captured.out


def test_convert_write_creates_modeling_file(
    modular_fixture: Path,
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "out"
    rc = main(
        [
            "convert",
            "--package",
            "mypkg",
            "--write",
            "--target-dir",
            str(out_dir),
            str(modular_fixture),
        ]
    )
    assert rc == 0
    written = list(out_dir.glob("*.py"))
    assert any(p.name == "modeling_foo2.py" for p in written)


def test_convert_unknown_file_returns_nonzero(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    rc = main(["convert", "--package", "mypkg", str(tmp_path / "no-such.py")])
    captured = capsys.readouterr()
    assert rc == 2
    assert "not a file" in captured.err


def test_convert_tree_walks_directory(
    modular_fixture: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pkg_root = modular_fixture.parent.parent  # mypkg/
    rc = main(["convert-tree", "--package", "mypkg", str(pkg_root)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "class Foo2Model" in captured.out


def test_convert_tree_empty_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(["convert-tree", str(tmp_path)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "no modular_*.py files" in captured.err


def test_describe_emits_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["describe", "--package", "mypkg"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["package_name"] == "mypkg"
    assert "__version__" in payload


def test_describe_with_transformers_adapter(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["describe", "--transformers"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["package_name"] == "transformers"
    assert payload["rename"] == "AutoCasingRenamePolicy"
    assert "TrailingCallHook" in payload["post_class_hooks"]


def test_package_with_transformers_adapter_targets_a_fork(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--transformers --package optimum` is a real use case for transformers forks."""
    rc = main(["describe", "--package", "optimum", "--transformers"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["package_name"] == "optimum"
    assert payload["rename"] == "AutoCasingRenamePolicy"


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("pycodelift ")
