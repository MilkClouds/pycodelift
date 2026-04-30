# How conversion works

The pipeline is short. Eight passes, all over a libcst Concrete Syntax
Tree (CST) — never raw text, never `ast`. Whitespace, comments, and
formatting in the parent files flow through unchanged.

```
modular_<x>.py
      │
      ▼  ① parse with libcst.parse_module
CST
      │
      ▼  ② walk the modular file with ModularFileMapper (CSTVisitor)
      │     ─ collect classes, functions, top-level assignments, imports
      │     ─ for every `from ..foo.modeling_foo import FooThing` import,
      │       importlib-load `foo.modeling_foo`, parse it too, cache the CST
      │
      ▼  ③ for each class declared in the modular file, run
      │     ClassDependencyMapper to resolve its parent class node
      │     (in this file, in a sibling file, or in a parent module's CST)
      │
      ▼  ④ inline-flatten one level of inheritance — see below
      │
      ▼  ⑤ rename pass — preserve_case_replace
      │     base name → new name in every case variant: snake / Camel /
      │     UPPER / kebab. Irregular casing overridden by RenamePolicy.
      │
      ▼  ⑥ pull in transitive helper dependencies
      │     functions / module-level vars used by inlined parent bodies
      │     get copied into the output module if not already present
      │
      ▼  ⑦ split outputs by class-name suffix
      │     FileTypeMap: { "Config": "configuration", … } →
      │       FooConfig → configuration_foo.py, FooModel → modeling_foo.py
      │
      ▼  ⑧ render: prepend HeaderTemplate, run ruff format
{stem: source_string}
```

## Step ④ — the heart: inheritance inlining

Every concrete rule for what a modular construct *means* at codegen
time lives in this pass.

### Rule 1 — `class Child(Parent): pass`

Replace the `pass` body with the **entire body of `Parent`**, then
rename references (Step ⑤). The output is a self-contained `Child`
class with no inheritance edge to `Parent`.

```
input:                          output:
class Child(Parent):            class Child(nn.Module):
    pass                            def __init__(self, config):
                                        # ...full Parent.__init__...
                                    def forward(self, x):
                                        # ...full Parent.forward...
```

### Rule 2 — `super().__init__(args)` unfolding

When the child overrides `__init__` and the first non-docstring
statement is a `super()` call, the engine *unfolds* the call: the
parent `__init__` body is spliced in where `super().__init__(args)`
used to sit, and the child's remaining statements stay around it.

```
input:                                  output:
class Child(Parent):                    class Child(nn.Module):
    def __init__(self, config):             def __init__(self, config):
        super().__init__(config)                # ...all of Parent.__init__'s body...
        self.extra = 1                          self.extra = 1
```

If you want the *generated* class to keep a runtime super call (because
its base in the output is not `Parent` but something else, e.g.
`nn.Module`), call the grandparent explicitly:
`nn.Module.__init__(self)` becomes `super().__init__()` in the output.

### Rule 3 — `del self.attr` is line-level deletion

`del self.attr` after `super().__init__(...)` *removes the
`self.attr = ...` line* from the inlined parent `__init__`. It does
not delete other references; if the parent's `forward` reads
`self.attr`, override `forward` too.

```
parent:                              child:                          output:
class Parent:                        class Child(Parent):            class Child:
    def __init__(self, c):               def __init__(self, c):          def __init__(self, c):
        self.x = 1                           super().__init__(c)             # self.x = 1 line removed
        self.y = 2                           del self.x                      self.y = 2
```

### Rule 4 — `attr = AttributeError()` deletes a config field

For dataclass-like config classes, assigning `AttributeError()` at the
class level *removes the attribute declaration entirely* from the
generated config.

```
input:                                  output:
class ChildConfig(ParentConfig):        class ChildConfig:
    removed_field = AttributeError()        # (other fields, but no
                                            #  `removed_field` declaration)
```

### Rule 5 — `def m(...): raise AttributeError("...")` deletes a method

A method whose body is a single `raise AttributeError(...)` statement
gets removed from the generated class entirely. Use this when an
inherited method doesn't apply to the child.

### Rule 6 — `def m(**super_kwargs)` inherits the signature

Writing `def forward(**super_kwargs): return super().forward(**super_kwargs)`
asks the engine to **expand the parent's full signature into the
generated child**, while keeping the new docstring or decorators.
Used to add docs without rewriting the signature.

### Rule 7 — one-level flatten

If `Parent` itself inherits from `GrandParent`, the engine inlines
`Parent` into `Child` but **does not** inline `GrandParent` into
`Parent`. References to `GrandParent` are kept as ordinary imports.
This matches transformers' constraint and bounds the cost of any one
conversion.

## Step ⑤ — case-preserving rename, in detail

The engine builds a regex that matches every case variant of the base
name simultaneously and replaces each with the corresponding variant of
the new name:

| In source | Becomes | Driver |
|---|---|---|
| `foo` | `foo2` | snake_case |
| `Foo` | `Foo2` | PascalCase, derived from snake |
| `FOO` | `FOO2` | UPPER, derived from snake |
| `foo-bar` | `foo2-bar` | kebab-case |

For acronyms or irregular casing where naive PascalCase derivation is
wrong, register the canonical form via `AutoCasingRenamePolicy`
(`pycodelift.policies.AutoCasingRenamePolicy`).

The same regex run also rewrites `# Copied from ...` comments and
relative imports (`from ..base.modeling_base import ...` →
`from ..base.modeling_<new_name> import ...` for sibling generated
files only — absolute imports are left alone).

## Step ⑥ — transitive helper closure

If `Parent.__init__` calls a module-level helper `apply_rope` defined
in the parent's file, `apply_rope` is *also* copied (or imported, if
already in the modular file's namespace) into the output. The user
doesn't have to declare it in the modular file. The closure walks
transitively until no new names are pulled in.

## Step ⑦ — splitting by class suffix

A `FileTypeMap` maps a *trailing PascalCase token* to a *file stem*:

```python
FileTypeMap({"Config": "configuration", "Tokenizer": "tokenization"})
```

Every class is bucketed by its longest matching suffix; classes
without a registered suffix fall into the `default_stem` (typically
`modeling`). Buckets become separate output files. Within a bucket,
class order in the output follows the topological order of
intra-bucket dependencies.

## Step ⑧ — render

For each bucket: dotted-import deduplication → header-template prepend
(`{relative_path}`, `{short_name}` slots filled in) → emit source as a
string.

The result is a `dict[str, str]` of `{file_type_stem: source_string}`.
:meth:`pycodelift.Flattener.write` materializes that to disk. pycodelift
itself does **not** invoke a formatter — projects that want one (e.g.
transformers' `make style` flow) should run `ruff format` or `black`
on the written files as a follow-up step.

## Where to find the implementation

| Pass | File | Class / function |
|---|---|---|
| ① parse | libcst | `cst.parse_module` |
| ② walk + parent CSTs | `_vendor/modular_model_converter.py` | `ModularFileMapper`, `ModelFileMapper` |
| ③ class deps | `_vendor/modular_model_converter.py` | `ClassDependencyMapper`, `find_all_dependencies` |
| ④ inline | `_vendor/modular_model_converter.py` | `replace_class_node`, `ReplaceSuperCallTransformer`, `ReplaceParentClassCallTransformer` |
| ⑤ rename | `_vendor/modular_model_converter.py` | `ReplaceNameTransformer`, `preserve_case_replace` |
| ⑥ closure | `_vendor/modular_model_converter.py` | `_compute_recursive_object_dependencies` |
| ⑦ split | `_vendor/modular_model_converter.py` + policies | `find_file_type` (uses `TYPE_TO_FILE_TYPE` set by `FileTypeMap`) |
| ⑧ render | `_vendor/modular_model_converter.py` | `create_modules`, `convert_modular_file` |

The CST passes themselves are derived from HuggingFace transformers'
`utils/modular_model_converter.py` (Apache-2.0); they've been
exercised against 200+ models in the upstream repository. pycodelift
generalizes their *configuration* — the eight policy slots — without
re-implementing the passes.
