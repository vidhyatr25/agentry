import urllib.parse

import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import ImageProvider

ENDPOINT = "https://image.pollinations.ai/prompt/"


@provider("image", "pollinations")
class PollinationsImage(ImageProvider):
    def _generate(self, prompt, out_path, size):
        width, height = size
        encoded = urllib.parse.quote(prompt)
        params = {
            "width": width,
            "height": height,
            "nologo": "true",
            "model": self.options.get("model", "flux"),
            "seed": self.options.get("seed", 0) or None,
        }
        params = {k: v for k, v in params.items() if v is not None}
        resp = requests.get(
            ENDPOINT + encoded,
            params=params,
            timeout=self.options.get("timeout", 180),
        )
        if resp.status_code >= 400 or not resp.content:
            raise ProviderError(f"pollinations {resp.status_code}")
        with open(out_path, "wb") as handle:
            handle.write(resp.content)
        return out_path
