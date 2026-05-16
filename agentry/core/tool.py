from abc import ABC, abstractmethod

from .registry import registry


class Tool(ABC):
    name = "tool"
    description = ""
    cost = "free"
    inputs = {}
    outputs = {}

    def __init__(self, ctx):
        self.ctx = ctx

    @abstractmethod
    def run(self, **kwargs):
        raise NotImplementedError

    @classmethod
    def manifest(cls):
        return {
            "name": cls.name,
            "description": cls.description,
            "cost": cls.cost,
            "inputs": cls.inputs,
            "outputs": cls.outputs,
        }


def tools_manifest():
    out = []
    for name in registry.names("tool"):
        out.append(registry.get("tool", name).manifest())
    return out


def build_tool(ctx, name):
    return registry.get("tool", name)(ctx)
