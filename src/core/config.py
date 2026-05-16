import json
import os
from pathlib import Path

import yaml

from .errors import ConfigError


def deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml(path):
    path = Path(path)
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def load_json(path):
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"workflow file not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid workflow json {path}: {exc}") from exc


def env_overrides(prefix="WFS_"):
    overrides = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix):].lower().split("__")
        node = overrides
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = _coerce(value)
    return overrides


def _coerce(value):
    low = value.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def build_settings(settings_path, workflow):
    defaults = {
        "telemetry": {"pricing": {}},
        "publishing": {"default_publisher": "local"},
        "runtime": {"retries": 1, "retry_backoff_sec": 5},
    }
    settings = deep_merge(defaults, load_yaml(settings_path))
    settings = deep_merge(settings, workflow.get("settings", {}))
    settings = deep_merge(settings, env_overrides())
    return settings


def validate_workflow(workflow):
    for field in ("name", "steps"):
        if field not in workflow:
            raise ConfigError(f"workflow missing required field: {field}")
    if not isinstance(workflow["steps"], list) or not workflow["steps"]:
        raise ConfigError("workflow.steps must be a non-empty list")
    for index, spec in enumerate(workflow["steps"]):
        if "type" not in spec:
            raise ConfigError(f"step[{index}] missing 'type'")
    return workflow
