"""Command-line entry point for pycodelift. See ``pycodelift --help``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import Flattener
from . import __version__ as PYCODELIFT_VERSION


def _build_flattener(args: argparse.Namespace) -> Flattener:
    if args.transformers:
        from .adapters.transformers import make_transformers_flattener

        return make_transformers_flattener(package_name=args.package or "transformers")
    return Flattener(package_name=args.package or "pycodelift")


def _emit(modular_file: Path, files: dict[str, str], args: argparse.Namespace) -> None:
    if args.write:
        target_dir = Path(args.target_dir) if args.target_dir else None
        for path in Flattener.write(modular_file, files, target_dir=target_dir):
            print(path, file=sys.stderr)
    else:
        for stem, source in files.items():
            print(f"========= {stem} =========")
            print(source, end="")
            if not source.endswith("\n"):
                print()


def _cmd_convert(args: argparse.Namespace) -> int:
    flattener = _build_flattener(args)
    rc = 0
    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"pycodelift: not a file: {path}", file=sys.stderr)
            rc = 2
            continue
        try:
            files = flattener.convert(str(path))
        except Exception as exc:
            print(f"pycodelift: failed to convert {path}: {exc}", file=sys.stderr)
            rc = 1
            continue
        if not files:
            print(f"pycodelift: nothing to write for {path}", file=sys.stderr)
            continue
        _emit(path, files, args)
    return rc


def _cmd_convert_tree(args: argparse.Namespace) -> int:
    flattener = _build_flattener(args)
    root = Path(args.root)
    if not root.is_dir():
        print(f"pycodelift: not a directory: {root}", file=sys.stderr)
        return 2
    results = flattener.convert_tree(str(root), pattern=args.pattern, on_error="continue")
    if not results:
        print(f"pycodelift: no modular_*.py files under {root}", file=sys.stderr)
        return 0
    for modular_file, files in results.items():
        if not files:
            continue
        _emit(Path(modular_file), files, args)
    return 0


def _cmd_describe(args: argparse.Namespace) -> int:
    description = _build_flattener(args).describe()
    description["__version__"] = PYCODELIFT_VERSION
    json.dump(description, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pycodelift",
        description="Build-time class-inheritance flattener.",
    )
    parser.add_argument("--version", action="version", version=f"pycodelift {PYCODELIFT_VERSION}")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--package", default=None, help="Top-level package name (default: 'pycodelift').")
    common.add_argument(
        "--transformers",
        action="store_true",
        help="Use the transformers compatibility adapter. Combine with --package for forks.",
    )
    common.add_argument("--write", action="store_true", help="Write to disk instead of stdout.")
    common.add_argument("--target-dir", default=None, help="Output directory when --write is set.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_convert = sub.add_parser("convert", parents=[common], help="Convert one or more modular_*.py files.")
    p_convert.add_argument("files", nargs="+")
    p_convert.set_defaults(func=_cmd_convert)

    p_tree = sub.add_parser("convert-tree", parents=[common], help="Recursively convert modular_*.py files.")
    p_tree.add_argument("root")
    p_tree.add_argument("--pattern", default="**/modular_*.py")
    p_tree.set_defaults(func=_cmd_convert_tree)

    p_describe = sub.add_parser("describe", parents=[common], help="Dump effective config as JSON.")
    p_describe.set_defaults(func=_cmd_describe)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
