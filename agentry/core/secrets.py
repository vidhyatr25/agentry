import os
import re

from .errors import SecretError

_REF = re.compile(r"\$\{([A-Z0-9_]+)\}")


class SecretResolver:
    def __init__(self, environ=None, lenient=False):
        self._env = dict(os.environ if environ is None else environ)
        self._used = set()
        self.lenient = lenient

    def get(self, name, required=True):
        value = self._env.get(name)
        if value is None or value == "":
            if required:
                raise SecretError(f"missing required secret: {name}")
            return None
        self._used.add(name)
        return value

    def resolve(self, value):
        if isinstance(value, str):
            def _sub(match):
                key = match.group(1)
                if self.lenient:
                    resolved = self.get(key, required=False)
                    return resolved if resolved is not None else f"__MISSING_{key}__"
                return self.get(key, required=True)

            return _REF.sub(_sub, value)
        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(v) for v in value]
        return value

    def referenced_names(self, value, found=None):
        found = set() if found is None else found
        if isinstance(value, str):
            found.update(_REF.findall(value))
        elif isinstance(value, dict):
            for v in value.values():
                self.referenced_names(v, found)
        elif isinstance(value, list):
            for v in value:
                self.referenced_names(v, found)
        return found

    def require(self, names):
        missing = [n for n in names if not self._env.get(n)]
        if missing:
            raise SecretError("missing required secrets: " + ", ".join(sorted(missing)))

    def mask(self, text):
        out = str(text)
        for name in self._used:
            secret = self._env.get(name)
            if secret and len(secret) >= 4:
                out = out.replace(secret, f"***{name}***")
        return out

    @property
    def used(self):
        return sorted(self._used)
