"""Public :class:`Flattener` API.

Configuration shell that pushes policy values into vendor module-level
slots, runs one conversion via :mod:`pycodelift._vendor`, and restores
the slots. See ``docs/how-it-works.md`` for the conversion pipeline.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Mapping, Sequence

if TYPE_CHECKING:
    from ..policies.file_types import FileTypeMap
    from ..policies.header import HeaderTemplate
    from ..policies.hooks import ClassHook, SpecialBaseHandler
    from ..policies.naming import RenamePolicy

from .._vendor import modular_integrations as _vi
from .._vendor import modular_model_converter as _v
from .._vendor.create_dependency_mapping import find_priority_list as _find_priority_list

__all__ = ["Flattener", "find_priority_list"]


def find_priority_list(
    modular_files: Sequence[str | os.PathLike[str]],
) -> tuple[list[list[str]], dict[str, set[str]]]:
    """Topologically sort modular files; return ``(levels, graph)``."""
    return _find_priority_list([os.fspath(f) for f in modular_files])


class Flattener:
    """Configured inheritance flattener. See README for the keyword args."""

    def __init__(
        self,
        package_name: str = "pycodelift",
        *,
        rename: "RenamePolicy | None" = None,
        file_types: "FileTypeMap | None" = None,
        pre_body_vars: Sequence[str] = ("logger",),
        skip_imports: Sequence[str] = (),
        special_bases: Mapping[str, "SpecialBaseHandler"] | None = None,
        post_class_hooks: Sequence["ClassHook"] = (),
        flatten_levels: int = 1,
        header_template: "str | HeaderTemplate | None" = None,
        excluded_external_files: Mapping[str, list[Mapping[str, str]]] | None = None,
        prepend_namespace_parent: bool = False,
    ) -> None:
        if flatten_levels != 1:
            raise NotImplementedError("flatten_levels=1 only in v0.1.")
        if special_bases:
            raise NotImplementedError("SpecialBaseHandlers not honoured in v0.1.")

        from ..policies.header import HeaderTemplate as _HT

        if isinstance(header_template, _HT):
            header_template = header_template.template

        self.package_name = package_name
        self.rename = rename
        self.file_types = file_types
        self.pre_body_vars = tuple(pre_body_vars)
        self.skip_imports = tuple(skip_imports)
        self.special_bases = dict(special_bases or {})
        self.post_class_hooks = tuple(post_class_hooks)
        self.flatten_levels = flatten_levels
        self.header_template = header_template
        self.excluded_external_files = excluded_external_files
        self.prepend_namespace_parent = prepend_namespace_parent

    def convert(self, modular_file: str | os.PathLike[str]) -> dict[str, str]:
        """Convert one modular file. Returns ``{file_type_stem: source}``."""
        path = Path(os.fspath(modular_file))
        if not path.is_file():
            raise FileNotFoundError(f"modular file not found: {path}")
        if not (path.name.startswith("modular_") and path.suffix == ".py"):
            raise ValueError(f"expected a 'modular_<name>.py' file, got: {path.name}")
        with self._apply_options():
            return _v.convert_modular_file(str(path), source_library=self.package_name)

    def convert_tree(
        self,
        root: str | os.PathLike[str],
        *,
        pattern: str = "**/modular_*.py",
        on_error: str = "raise",
    ) -> dict[str, dict[str, str]]:
        """Convert every modular file under *root* in dependency order.

        ``on_error`` is ``"raise"`` (default) or ``"continue"`` (log to
        stderr, store ``{}`` for the failing file, keep going).
        """
        if on_error not in {"raise", "continue"}:
            raise ValueError(f"on_error must be 'raise' or 'continue', got: {on_error!r}")

        files = sorted(str(p) for p in Path(root).glob(pattern))
        if not files:
            return {}
        levels, _ = find_priority_list(files)
        result: dict[str, dict[str, str]] = {}
        with self._apply_options():
            for level in levels:
                for f in level:
                    try:
                        result[f] = _v.convert_modular_file(f, source_library=self.package_name)
                    except Exception as exc:
                        if on_error == "raise":
                            raise
                        print(f"pycodelift: failed to convert {f}: {exc}", file=sys.stderr)
                        result[f] = {}
        return result

    @staticmethod
    def write(
        modular_file: str | os.PathLike[str],
        converted: Mapping[str, str],
        *,
        target_dir: str | os.PathLike[str] | None = None,
    ) -> list[Path]:
        """Write a ``convert(...)`` dict to disk as ``{stem}_{model_name}.py``."""
        modular_path = Path(modular_file)
        if not modular_path.name.startswith("modular_"):
            raise ValueError(f"expected modular_<name>.py, got: {modular_path.name}")
        model_name = modular_path.stem.removeprefix("modular_")

        out_dir = Path(target_dir) if target_dir is not None else modular_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for stem, source in converted.items():
            if not stem.isidentifier():
                raise ValueError(f"file-type stem is not a valid identifier: {stem!r}")
            path = out_dir / f"{stem}_{model_name}.py"
            path.write_text(source, encoding="utf-8")
            written.append(path)
        return written

    def describe(self) -> dict[str, Any]:
        """JSON-friendly config snapshot."""
        return {
            "package_name": self.package_name,
            "pre_body_vars": list(self.pre_body_vars),
            "skip_imports": list(self.skip_imports),
            "flatten_levels": self.flatten_levels,
            "rename": type(self.rename).__name__ if self.rename else None,
            "file_types": type(self.file_types).__name__ if self.file_types else None,
            "special_bases": sorted(self.special_bases),
            "post_class_hooks": [type(h).__name__ for h in self.post_class_hooks],
            "header_template": "custom" if self.header_template is not None else "default",
            "prepend_namespace_parent": self.prepend_namespace_parent,
            "excluded_external_files": sorted(self.excluded_external_files or {}),
        }

    def __repr__(self) -> str:
        return f"Flattener(package_name={self.package_name!r})"

    @contextmanager
    def _apply_options(self) -> Iterator[None]:
        """Snapshot vendor module-level state, push policies, restore on exit."""
        from ..policies.file_types import FileTypeMap
        from ..policies.header import DEFAULT_HEADER_TEMPLATE
        from ..policies.hooks import TrailingCallHook

        slots: list[tuple[Any, str, Any]] = []

        def push(mod: Any, attr: str, value: Any) -> None:
            slots.append((mod, attr, getattr(mod, attr)))
            setattr(mod, attr, value)

        try:
            ft = self.file_types or FileTypeMap.default()
            trailing = tuple(h.call_pattern() for h in self.post_class_hooks if isinstance(h, TrailingCallHook))

            push(_v, "CONFIG_MAPPING_NAMES", dict(self.rename.to_vendor_table()) if self.rename else {})
            push(_v, "TYPE_TO_FILE_TYPE", dict(ft.suffix_to_stem))
            push(_v, "ALL_FILE_TYPES", ft.all_stems())
            push(_v, "AUTO_GENERATED_MESSAGE", self.header_template or DEFAULT_HEADER_TEMPLATE)
            push(_v, "VARIABLES_AT_THE_BEGINNING", self.pre_body_vars)
            push(_v, "IMPORTS_TO_SKIP_IN_MODULAR", self.skip_imports)
            push(_v, "TRAILING_METHOD_CALLS", trailing)
            push(_vi, "EXCLUDED_EXTERNAL_FILES", dict(self.excluded_external_files or {}))
            push(_vi, "PREPEND_NAMESPACE_PARENT", self.prepend_namespace_parent)
            yield
        finally:
            for mod, attr, original in reversed(slots):
                setattr(mod, attr, original)
