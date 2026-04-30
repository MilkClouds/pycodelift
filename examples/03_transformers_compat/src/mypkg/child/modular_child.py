from ..base.configuration_base import BaseConfig
from ..base.modeling_base import BaseModel


class ChildConfig(BaseConfig):
    model_type = "child"


class ChildModel(BaseModel):
    pass


__all__ = ["ChildConfig", "ChildModel"]
