from .errors import RegistryError


class Registry:
    def __init__(self):
        self._items = {}

    def register(self, namespace, name):
        def decorator(target):
            bucket = self._items.setdefault(namespace, {})
            if name in bucket:
                raise RegistryError(f"{namespace}:{name} already registered")
            bucket[name] = target
            return target

        return decorator

    def get(self, namespace, name):
        bucket = self._items.get(namespace, {})
        if name not in bucket:
            available = ", ".join(sorted(bucket)) or "none"
            raise RegistryError(
                f"unknown {namespace} '{name}'. available: {available}"
            )
        return bucket[name]

    def names(self, namespace):
        return sorted(self._items.get(namespace, {}))

    def snapshot(self):
        return {ns: sorted(items) for ns, items in self._items.items()}


registry = Registry()


def provider(kind, name):
    return registry.register(f"provider:{kind}", name)


def step(name):
    return registry.register("step", name)
