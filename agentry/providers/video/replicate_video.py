import time

import requests

from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import VideoProvider

CREATE = "https://api.replicate.com/v1/predictions"


@provider("video", "replicate")
class ReplicateVideo(VideoProvider):
    def _assemble(self, plan, out_path):
        token = self.options.get("api_key") or self.ctx.secrets.get("REPLICATE_API_TOKEN")
        version = self.options.get("model_version")
        if not version:
            raise ProviderError("replicate provider requires options.model_version")
        prompt = plan.get("video_prompt") or " ".join(
            s.get("caption", "") for s in plan["scenes"]
        )
        body = {
            "version": version,
            "input": {
                "prompt": prompt,
                **self.options.get("input", {}),
            },
        }
        resp = requests.post(
            CREATE,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=120,
        )
        if resp.status_code >= 400:
            raise ProviderError(f"replicate {resp.status_code}: {resp.text[:300]}")
        prediction = resp.json()
        poll_url = prediction["urls"]["get"]
        deadline = time.time() + self.options.get("max_wait_sec", 900)
        while time.time() < deadline:
            poll = requests.get(
                poll_url, headers={"Authorization": f"Bearer {token}"}, timeout=60
            ).json()
            status = poll.get("status")
            if status == "succeeded":
                output = poll.get("output")
                url = output[-1] if isinstance(output, list) else output
                data = requests.get(url, timeout=300).content
                with open(out_path, "wb") as handle:
                    handle.write(data)
                plan["cost_usd"] = self.options.get("cost_per_video", 0.0)
                return out_path
            if status in ("failed", "canceled"):
                raise ProviderError(f"replicate prediction {status}: {poll.get('error')}")
            time.sleep(self.options.get("poll_interval_sec", 8))
        raise ProviderError("replicate prediction timed out")
