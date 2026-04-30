# Changelog

All notable changes to `pycodelift` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

First public alpha. Establishes the framework-agnostic engine,
policy/hook surface, transformers compatibility adapter, CLI, examples,
and documentation set.

### Added

- **Engine** (`pycodelift.core`): `Flattener`, `FlattenerOptions`,
  `convert_modular_file`, `find_priority_list`. One-level inheritance
  flattening derived from HuggingFace `transformers`'
  `utils/modular_model_converter.py` (Apache-2.0).
- **Policies** (`pycodelift.policies`):
  `RenamePolicy` / `AutoCasingRenamePolicy`, `FileTypeMap`,
  `HeaderTemplate`, `ClassHook` / `TrailingCallHook`,
  `SpecialBaseHandler` (protocol).
- **transformers compatibility adapter**
  (`pycodelift.adapters.transformers`):
  `make_transformers_flattener()`, `load_transformers_casing_table()`,
  and the underlying constants
  (`TRANSFORMERS_TYPE_TO_FILE_TYPE`,
  `TRANSFORMERS_PRE_BODY_VARS`,
  `TRANSFORMERS_SKIP_IMPORTS`,
  `TRANSFORMERS_AUTO_GENERATED_MESSAGE`).
- **CLI** (`pycodelift`): `convert`, `convert-tree`, `describe`,
  with `--package`, `--transformers`, `--write`, `--target-dir`
  flags.
- **Examples**: `01_minimal`, `02_split_outputs`,
  `03_transformers_compat`, each with a runnable `run.py` driver.
- **Docs**: README + `docs/how-it-works.md` (the eight-pass
  conversion pipeline, pass by pass with code examples).
- **Tests**: 49 unit + integration tests covering policies,
  policy injection round-trips, file-type splitting, transformers
  adapter wiring, and the CLI surface.

### Generalized from transformers

The following transformers-specific assumptions are now policy
objects (or default values) instead of hard-coded constants:

| Transformers source | pycodelift surface |
|---|---|
| `CONFIG_MAPPING_NAMES` | `RenamePolicy.casing_table` |
| `TYPE_TO_FILE_TYPE` | `FileTypeMap` |
| `AUTO_GENERATED_MESSAGE` | `HeaderTemplate` |
| `VARIABLES_AT_THE_BEGINNING` | `Flattener.pre_body_vars` |
| `IMPORTS_TO_SKIP_IN_MODULAR` | `Flattener.skip_imports` |
| `EXCLUDED_EXTERNAL_FILES` | `Flattener.excluded_external_files` |
| `_fix_post_init_location` | `TrailingCallHook` |
| namespace-prefix heuristic | `Flattener.prepend_namespace_parent` |
| `src/transformers/` path regex | `Flattener.package_name` |

### Known limitations

- One-level inheritance flatten only (matches transformers).
- `Flattener._apply_options` mutates module-level vendor state — not
  thread-safe. Use process-pool parallelism for now.
- `SpecialBaseHandler` protocol exists but only the hard-coded
  transformers `PreTrainedModel` rule is honoured by the engine in
  v0.1.
- No corpus byte-equivalence tests yet against transformers'
  `examples/modular-transformers/` (planned for v0.2).
- `_vendor/` is a transient holding zone and will dissolve in v0.2.

[0.1.0]: https://github.com/milkclouds/lazyregistry/tree/main/pycodelift
