# pycodelift

Build-time class-inheritance flattener. Write thin diff-only child
classes against a base file; get back a single self-contained module
with the inheritance inlined.

Generalizes HuggingFace `transformers`'
[modular](https://huggingface.co/docs/transformers/main/en/modular_transformers)
codegen into a framework-agnostic library. **Status:** alpha.

## When this is worth using

When all three apply:
1. Many sibling files share a base (10+).
2. They are read and forked, not just called.
3. Edits to the base must not silently ripple into already-released
   siblings.

For five subclasses in a normal app, plain Python inheritance is the
right answer.

## Install

```bash
pip install pycodelift     # or: uv add pycodelift
```

## Quickstart

```
mypkg/
├── base/modeling_base.py       # parent
└── child/modular_child.py      # diff
```

`mypkg/child/modular_child.py`:

```python
from ..base.modeling_base import BaseModel

class ChildModel(BaseModel):
    def __init__(self, config):
        super().__init__(config)
        self.y = 2

__all__ = ["ChildModel"]
```

Convert:

```bash
pycodelift convert mypkg/child/modular_child.py --package mypkg
```

Or:

```python
from pycodelift import Flattener
files = Flattener(package_name="mypkg").convert("mypkg/child/modular_child.py")
print(files["modeling"])
```

The output `modeling_child.py` has `BaseModel`'s body inlined and no
inheritance edge.

## How it works

Eight CST passes: parse → walk → resolve parent classes →
**inline-flatten one level** → case-preserving rename → pull in
transitive helpers → split outputs by class-suffix → render. Each pass
with code examples in [`docs/how-it-works.md`](docs/how-it-works.md).

## Policies

`Flattener(...)` keyword args (all optional):

| Argument | Purpose | Default |
|---|---|---|
| `rename` | irregular casing overrides | snake↔Pascal derivation |
| `file_types` | suffix → output stem (`Config` → `configuration_<x>.py`) | everything → `modeling_<x>.py` |
| `pre_body_vars` | top-level vars that come first | `("logger",)` |
| `skip_imports` | imports to drop | `()` |
| `post_class_hooks` | e.g. `TrailingCallHook("post_init")` for trailing-call rules | `()` |
| `header_template` | banner with `{relative_path}` / `{short_name}` slots | default banner |
| `excluded_external_files` | per-package files to skip when walking imports | `None` |
| `prepend_namespace_parent` | transformers' `optimum.habana`-style prefix | `False` |

`flatten_levels=2` and non-empty `special_bases` raise
`NotImplementedError` in v0.1.

## transformers compatibility

```python
from pycodelift.adapters.transformers import make_transformers_flattener

flattener = make_transformers_flattener()
files = flattener.convert("src/transformers/models/olmo2/modular_olmo2.py")
```

The adapter pins every transformers convention so output matches
upstream `utils/modular_model_converter.py`. CLI: `--transformers`.
Combine with `--package optimum` for transformers forks.

## CLI

```
pycodelift convert <file>...      # one or many
pycodelift convert-tree <root>     # recursive
pycodelift describe                # dump effective config as JSON
```

Flags: `--package`, `--transformers`, `--write`, `--target-dir`.

## Caveats

- One-level flatten only. `Foo2(Foo)` works; `Foo`'s own parent is not
  inlined.
- Not thread-safe (v0.1 mutates module-level vendor state). Use a
  process pool for parallelism.
- `del self.x` is line-level — removes the assignment, not later
  references.

## Examples

Three runnable mini-projects under [`examples/`](examples/):
`01_minimal`, `02_split_outputs`, `03_transformers_compat`.

## Lineage

Derived from [`huggingface/transformers`'s
`utils/modular_model_converter.py`](https://github.com/huggingface/transformers/blob/main/utils/modular_model_converter.py)
(Apache-2.0). The CST passes are theirs (battle-tested across 200+
models); pycodelift extracts the policy slots they hard-coded.
See [`NOTICE`](./NOTICE).

## License

Apache-2.0.
