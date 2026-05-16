import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str


class LLMProvider(ABC):
    def __init__(self, spec, ctx):
        self.spec = spec
        self.ctx = ctx
        self.options = spec.get("options", {})
        self.model = spec.get("model", "")
        self.provider_name = spec.get("provider", "")

    def complete(self, prompt, system=None, step=None, **kwargs):
        if self.ctx.dry_run:
            result = LLMResult(
                text=self._dry_text(prompt),
                prompt_tokens=max(1, len(prompt.split())),
                completion_tokens=48,
                model=self.model or "dry",
            )
        else:
            result = self._complete(prompt, system, **kwargs)
        self.ctx.telemetry.record_llm(
            self.provider_name,
            result.model,
            result.prompt_tokens,
            result.completion_tokens,
            step=step,
        )
        return result

    def complete_json(self, prompt, schema_hint, dry_default, system=None, step=None):
        if self.ctx.dry_run:
            self.ctx.telemetry.record_llm(
                self.provider_name, self.model or "dry", max(1, len(prompt.split())), 64, step=step
            )
            return dry_default
        guided = (
            f"{prompt}\n\nReturn ONLY valid minified JSON matching this shape:\n"
            f"{json.dumps(schema_hint)}\nNo prose, no markdown fences."
        )
        result = self.complete(guided, system=system, step=step)
        return self._parse_json(result.text, dry_default)

    @staticmethod
    def _parse_json(text, fallback):
        cleaned = text.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"[\{\[].*[\}\]]", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return fallback

    def _dry_text(self, prompt):
        return f"[dry-run:{self.provider_name}:{self.model}] {prompt[:60]}"

    @abstractmethod
    def _complete(self, prompt, system, **kwargs):
        raise NotImplementedError
