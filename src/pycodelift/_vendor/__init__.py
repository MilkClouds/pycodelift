"""Vendor staging zone — temporary home for transformers code being ported.

This subpackage is INTERNAL and TRANSIENT. It exists during Phase 1 of the
pycodelift port to hold a near-verbatim copy of the three transformers
utilities that pycodelift is derived from:

* ``modular_model_converter.py``   ← transformers/utils/modular_model_converter.py
* ``modular_integrations.py``      ← transformers/utils/modular_integrations.py
* ``create_dependency_mapping.py`` ← transformers/utils/create_dependency_mapping.py

Source commit: huggingface/transformers @ 53b92b94ed7e48ff5db11b88a271cb8941c2df9e

The files have been minimally edited so they import without a ``transformers``
install (Phase 1 stubs); their substantive logic is unchanged. Phase 2
splits this code into ``pycodelift.core.*`` modules and removes this
subpackage.

DO NOT depend on anything in ``pycodelift._vendor`` from outside the package.
The public API is exposed via ``pycodelift.Flattener`` (added in Phase 2).
"""
