"""The base implementation that the child modular file inherits from."""


class BaseModel:
    """A trivial stand-in for any 'parent' class.

    In a real project this might be a transformer block, a database
    model, an SDK client, etc. — anything you want to specialize.
    """

    def __init__(self, config):
        self.config = config
        self.x = 1

    def forward(self, x):
        return x
