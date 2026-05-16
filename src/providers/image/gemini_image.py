import base64

import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import ImageProvider

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


@provider("image", "gemini_image")
class GeminiImage(ImageProvider):
    def _generate(self, prompt, out_path, size):
        api_key = self.options.get("api_key") or self.ctx.secrets.get("GEMINI_API_KEY")
        model = self.options.get("model", "gemini-2.0-flash-preview-image-generation")
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
        }
        resp = requests.post(
            ENDPOINT.format(model=model),
            params={"key": api_key},
            json=body,
            timeout=self.options.get("timeout", 180),
        )
        if resp.status_code >= 400:
            raise ProviderError(f"gemini_image {resp.status_code}: {resp.text[:300]}")
        payload = resp.json()
        for part in payload.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                with open(out_path, "wb") as handle:
                    handle.write(base64.b64decode(inline["data"]))
                return out_path
        raise ProviderError("gemini_image returned no image data")
