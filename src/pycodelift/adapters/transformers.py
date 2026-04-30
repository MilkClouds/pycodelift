"""HuggingFace ``transformers`` compatibility adapter.

Returns a :class:`pycodelift.Flattener` configured to reproduce the
behaviour of upstream ``utils/modular_model_converter.py``:

>>> from pycodelift.adapters.transformers import make_transformers_flattener
>>> flattener = make_transformers_flattener()
>>> flattener.describe()["rename"]                                # doctest: +SKIP
'AutoCasingRenamePolicy'
"""

from __future__ import annotations

from typing import Mapping, Optional

from .. import Flattener
from .._vendor import modular_model_converter as _vendor
from ..policies import AutoCasingRenamePolicy, FileTypeMap, TrailingCallHook

__all__ = [
    "TRANSFORMERS_AUTO_GENERATED_MESSAGE",
    "TRANSFORMERS_PRE_BODY_VARS",
    "TRANSFORMERS_SKIP_IMPORTS",
    "TRANSFORMERS_TYPE_TO_FILE_TYPE",
    "load_transformers_casing_table",
    "make_transformers_flattener",
]


TRANSFORMERS_TYPE_TO_FILE_TYPE: Mapping[str, str] = {
    "Config": "configuration",
    "Tokenizer": "tokenization",
    "Processor": "processing",
    "ImageProcessor": "image_processing",
    "ImageProcessorPil": "image_processing_pil",
    "VideoProcessor": "video_processing",
    "VideoProcessorInitKwargs": "video_processing",
    "ImageProcessorKwargs": "image_processing",
    "FeatureExtractor": "feature_extraction",
    "ProcessorKwargs": "processing",
    "VideosKwargs": "processing",
    "ImagesKwargs": "processing",
    "TextKwargs": "processing",
}

TRANSFORMERS_PRE_BODY_VARS: tuple[str, ...] = (
    "logger",
    "_CHECKPOINT_FOR_DOC",
    "_CONFIG_FOR_DOC",
)

TRANSFORMERS_SKIP_IMPORTS: tuple[str, ...] = ("auto.modeling_auto",)

#: Verbatim transformers banner — sourced from the vendored converter.
TRANSFORMERS_AUTO_GENERATED_MESSAGE: str = _vendor.AUTO_GENERATED_MESSAGE

TRANSFORMERS_EXCLUDED_EXTERNAL_FILES: Mapping[str, list[Mapping[str, str]]] = {
    "habana": [{"name": "modeling_all_models", "type": "modeling"}],
}


def load_transformers_casing_table() -> dict[str, str]:
    """Best-effort import of transformers' ``CONFIG_MAPPING_NAMES``; ``{}`` if missing."""
    try:
        from transformers.models.auto.configuration_auto import CONFIG_MAPPING_NAMES
    except ImportError:
        return {}
    return dict(CONFIG_MAPPING_NAMES)


def make_transformers_flattener(
    *,
    casing_table: Optional[Mapping[str, str]] = None,
    package_name: str = "transformers",
) -> Flattener:
    """Build a :class:`Flattener` mirroring transformers' upstream behaviour.

    ``casing_table`` defaults to the live transformers table (or ``{}``
    if not installed). ``package_name`` overrides for transformers
    forks (``optimum``, ``optimum-habana``, etc.).
    """
    if casing_table is None:
        casing_table = load_transformers_casing_table()

    return Flattener(
        package_name=package_name,
        rename=AutoCasingRenamePolicy(dict(casing_table)),
        file_types=FileTypeMap(TRANSFORMERS_TYPE_TO_FILE_TYPE, default_stem="modeling"),
        pre_body_vars=TRANSFORMERS_PRE_BODY_VARS,
        skip_imports=TRANSFORMERS_SKIP_IMPORTS,
        post_class_hooks=(TrailingCallHook("post_init"),),
        header_template=TRANSFORMERS_AUTO_GENERATED_MESSAGE,
        excluded_external_files=dict(TRANSFORMERS_EXCLUDED_EXTERNAL_FILES),
        prepend_namespace_parent=True,
    )
