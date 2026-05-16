import json
import re

_TOKEN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def _stringify(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def render_prompt(template, variables):
    if not template:
        return ""

    def _sub(match):
        node = variables
        for part in match.group(1).split("."):
            if isinstance(node, dict):
                node = node.get(part)
            else:
                node = None
            if node is None:
                break
        return _stringify(node)

    return _TOKEN.sub(_sub, template)


def resolve_prompt(step, ctx, key, default, variables):
    template = step.params.get(key, default)
    if isinstance(template, str):
        template = ctx.secrets.resolve(template) if "${" in template else template
    return render_prompt(template, variables)
