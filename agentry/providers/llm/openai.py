import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from .base import LLMProvider, LLMResult

ENDPOINT = "https://api.openai.com/v1/chat/completions"


@provider("llm", "openai")
class OpenAIProvider(LLMProvider):
    def _complete(self, prompt, system, **kwargs):
        api_key = self.options.get("api_key") or self.ctx.secrets.get("OPENAI_API_KEY")
        model = self.model or "gpt-4o-mini"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = {
            "model": model,
            "messages": messages,
            "temperature": self.options.get("temperature", 0.9),
            "max_tokens": self.options.get("max_tokens", 2048),
        }
        base = self.options.get("base_url", "https://api.openai.com/v1")
        resp = requests.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=self.options.get("timeout", 120),
        )
        if resp.status_code >= 400:
            raise ProviderError(f"openai {resp.status_code}: {resp.text[:300]}")
        payload = resp.json()
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"openai empty response: {payload}") from exc
        usage = payload.get("usage", {})
        return LLMResult(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model=model,
        )
