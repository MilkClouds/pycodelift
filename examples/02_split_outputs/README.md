# Example 02 — split outputs

A modular file declaring both a config and a model class. Without a
`FileTypeMap`, both end up in `modeling_*.py`. With a `FileTypeMap` that
maps the `Config` suffix to the `configuration` stem, the output splits
into two files.

## Run

```bash
uv run python examples/02_split_outputs/run.py
```

You'll see two generated files: `configuration_child.py` (containing
`ChildConfig`) and `modeling_child.py` (containing `ChildModel`).
