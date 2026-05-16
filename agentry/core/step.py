from abc import ABC, abstractmethod


class Step(ABC):
    type_name = "step"

    def __init__(self, spec):
        self.spec = spec
        self.params = spec.get("params", {})

    def param(self, ctx, key, default=None):
        if key not in self.params:
            return default
        return ctx.render(self.params[key])

    @abstractmethod
    def run(self, ctx):
        raise NotImplementedError
