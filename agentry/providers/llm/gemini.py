import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from .base import LLMProvider, LLMResult

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


@provider("llm", "gemini")
class GeminiProvider(LLMProvider):
    def _complete(self, prompt, system, **kwargs):
        api_key = self.options.get("api_key") or self.ctx.secrets.get("GEMINI_API_KEY")
        model = self.model or "gemini-2.0-flash"
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.options.get("temperature", 0.9),
                "maxOutputTokens": self.options.get("max_tokens", 2048),
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        resp = requests.post(
            ENDPOINT.format(model=model),
            params={"key": api_key},
            json=body,
            timeout=self.options.get("timeout", 120),
        )
        if resp.status_code >= 400:
            raise ProviderError(f"gemini {resp.status_code}: {resp.text[:300]}")
        payload = resp.json()
        try:
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"gemini empty response: {payload}") from exc
        usage = payload.get("usageMetadata", {})
        return LLMResult(
            text=text,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            model=model,
        )
