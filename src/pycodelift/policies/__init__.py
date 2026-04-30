"""Policy objects passed to :class:`pycodelift.Flattener`."""

from .file_types import FileTypeMap
from .header import DEFAULT_HEADER_TEMPLATE, HeaderTemplate
from .hooks import ClassHook, SpecialBaseHandler, TrailingCallHook
from .naming import AutoCasingRenamePolicy, RenamePolicy

__all__ = [
    "AutoCasingRenamePolicy",
    "ClassHook",
    "DEFAULT_HEADER_TEMPLATE",
    "FileTypeMap",
    "HeaderTemplate",
    "RenamePolicy",
    "SpecialBaseHandler",
    "TrailingCallHook",
]
