# Example 03 — transformers compatibility

This example shows how `make_transformers_flattener()` reproduces the
exact behaviour of transformers'
`utils/modular_model_converter.py` for projects that follow transformers'
conventions (`Config`/`Tokenizer`/... suffixes, `self.post_init()`
trailing call, transformers banner).

The example does **not** import transformers itself — it just uses the
adapter on a transformers-shaped fixture. If you have transformers
installed the adapter additionally pulls in the live
`CONFIG_MAPPING_NAMES` table for irregular casing (e.g. acronyms).

> **Why the extra `src/` layer?** The transformers adapter turns on
> `prepend_namespace_parent` — every absolute import gets the parent
> directory prepended *unless* that parent is named `src` (transformers'
> own convention for namespace packages like `optimum.habana`). We
> mirror that convention here.

## Run

```bash
uv run python examples/03_transformers_compat/run.py
```

You'll see the transformers banner at the top of each generated file
and `Config` classes routed to `configuration_*.py`.
