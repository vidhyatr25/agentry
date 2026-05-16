import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from .base import LLMProvider, LLMResult

ENDPOINT = "https://api.anthropic.com/v1/messages"


@provider("llm", "claude")
class ClaudeProvider(LLMProvider):
    def _complete(self, prompt, system, **kwargs):
        api_key = self.options.get("api_key") or self.ctx.secrets.get("ANTHROPIC_API_KEY")
        model = self.model or "claude-sonnet-4-6"
        body = {
            "model": model,
            "max_tokens": self.options.get("max_tokens", 2048),
            "temperature": self.options.get("temperature", 0.9),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        resp = requests.post(
            ENDPOINT,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
            timeout=self.options.get("timeout", 120),
        )
        if resp.status_code >= 400:
            raise ProviderError(f"claude {resp.status_code}: {resp.text[:300]}")
        payload = resp.json()
        try:
            text = "".join(
                block.get("text", "")
                for block in payload["content"]
                if block.get("type") == "text"
            )
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"claude empty response: {payload}") from exc
        usage = payload.get("usage", {})
        return LLMResult(
            text=text,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            model=model,
        )
