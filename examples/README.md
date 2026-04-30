# pycodelift examples

Each subdirectory is a self-contained mini-project. From the
`pycodelift/` root, run:

```bash
uv run python examples/<example>/run.py
```

| Example | What it shows |
|---|---|
| [01_minimal](./01_minimal/) | The smallest possible inheritance flatten — one base file, one modular file, one generated output. |
| [02_split_outputs](./02_split_outputs/) | Use a `FileTypeMap` to split the generated code into multiple files (`configuration_*.py`, `modeling_*.py`). |
| [03_transformers_compat](./03_transformers_compat/) | Use the transformers adapter to reproduce upstream `utils/modular_model_converter.py` behaviour. |

Each example is also exercised by `tests/integration/` so they stay
working as the engine evolves.
