"""Unit tests for :mod:`pycodelift.policies.header`."""

from __future__ import annotations

from pycodelift.policies import DEFAULT_HEADER_TEMPLATE, HeaderTemplate


def test_default_template_renders_with_placeholders() -> None:
    rendered = HeaderTemplate().render(
        relative_path="my_pkg/foo2/modular_foo2.py",
        short_name="modular_foo2.py",
    )
    assert "my_pkg/foo2/modular_foo2.py" in rendered
    assert "modular_foo2.py" in rendered


def test_custom_template() -> None:
    tpl = HeaderTemplate("# from {short_name} via pycodelift\n")
    rendered = tpl.render(relative_path="ignored.py", short_name="modular_x.py")
    assert rendered == "# from modular_x.py via pycodelift\n"


def test_default_template_constant_is_string() -> None:
    assert isinstance(DEFAULT_HEADER_TEMPLATE, str)
    assert "{relative_path}" in DEFAULT_HEADER_TEMPLATE
