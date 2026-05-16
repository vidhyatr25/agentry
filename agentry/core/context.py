import re
from pathlib import Path

_DATA_REF = re.compile(r"\{\{\s*([a-zA-Z0-9_.\[\]]+)\s*\}\}")


class Context:
    def __init__(self, workflow, settings, secrets, telemetry, workdir, dry_run, logger):
        self.workflow = workflow
        self.settings = settings
        self.secrets = secrets
        self.telemetry = telemetry
        self.workdir = Path(workdir)
        self.dry_run = dry_run
        self.logger = logger
        self.data = {}
        self.artifacts = []
        self.workdir.mkdir(parents=True, exist_ok=True)

    def set(self, key, value):
        self.data[key] = value
        return value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def add_artifact(self, path, kind):
        entry = {"path": str(path), "kind": kind}
        self.artifacts.append(entry)
        return entry

    def path(self, *parts):
        target = self.workdir.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def _lookup(self, dotted):
        node = self.data
        for part in re.split(r"\.|\[|\]", dotted):
            if part == "":
                continue
            if isinstance(node, list):
                node = node[int(part)]
            elif isinstance(node, dict):
                node = node.get(part)
            else:
                return None
            if node is None:
                return None
        return node

    def render(self, value):
        if isinstance(value, str):
            def _sub(match):
                resolved = self._lookup(match.group(1))
                return "" if resolved is None else str(resolved)

            rendered = _DATA_REF.sub(_sub, value)
            return self.secrets.resolve(rendered)
        if isinstance(value, dict):
            return {k: self.render(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.render(v) for v in value]
        return value
