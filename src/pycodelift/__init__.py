"""pycodelift — build-time class-inheritance flattener.

Derived from HuggingFace transformers' ``utils/modular_model_converter.py``
(Apache-2.0); see ``NOTICE``.
"""

from __future__ import annotations

try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0.dev0"

from .core import Flattener, find_priority_list

__all__ = ["Flattener", "__version__", "find_priority_list"]
