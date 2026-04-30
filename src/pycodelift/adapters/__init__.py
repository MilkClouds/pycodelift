"""pycodelift.adapters — opt-in framework integrations.

Each adapter wires the framework-agnostic engine in :mod:`pycodelift.core`
to a specific upstream project's conventions. Adapters are kept in their
own subpackage so the core has zero dependency on the frameworks they
target — importing :mod:`pycodelift` does not import :mod:`transformers`.

v0.1 ships a single adapter:

* :mod:`pycodelift.adapters.transformers` — exact-fidelity reproduction of
  HuggingFace transformers' ``utils/modular_model_converter.py``
  behaviour. Used both as a regression target and as a drop-in
  replacement for projects that follow transformers' conventions.
"""
