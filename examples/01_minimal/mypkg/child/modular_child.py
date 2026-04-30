"""Modular file: child class inheriting from BaseModel.

The generated `modeling_child.py` will contain a self-contained
`ChildModel` class with the inherited body inlined and the new
attribute appended.
"""

from ..base.modeling_base import BaseModel


class ChildModel(BaseModel):
    def __init__(self, config):
        super().__init__(config)
        self.y = 2


__all__ = ["ChildModel"]
