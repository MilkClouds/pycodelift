from ..base.configuration_base import BaseConfig
from ..base.modeling_base import BaseModel


class ChildConfig(BaseConfig):
    model_type = "child"
    rms_norm_eps = 1e-5


class ChildModel(BaseModel):
    pass


__all__ = ["ChildConfig", "ChildModel"]
