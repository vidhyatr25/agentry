from .errors import ConfigError
from .registry import registry


def resolve_provider_spec(ctx, ref):
    if isinstance(ref, dict):
        spec = ref
    elif isinstance(ref, str):
        roles = ctx.workflow.get("providers", {})
        if ref not in roles:
            raise ConfigError(
                f"provider role '{ref}' not defined in workflow.providers"
            )
        spec = roles[ref]
    else:
        raise ConfigError(f"invalid provider reference: {ref!r}")
    spec = ctx.render(dict(spec))
    for field in ("kind", "provider"):
        if field not in spec:
            raise ConfigError(f"provider spec missing '{field}': {spec}")
    return spec


def build_provider(ctx, ref):
    spec = resolve_provider_spec(ctx, ref)
    cls = registry.get(f"provider:{spec['kind']}", spec["provider"])
    return cls(spec, ctx)


def build_step(spec):
    cls = registry.get("step", spec["type"])
    return cls(spec)
