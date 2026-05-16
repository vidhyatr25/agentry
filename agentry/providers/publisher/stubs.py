from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import Publisher


class _NotImplementedPublisher(Publisher):
    platform = "unknown"

    def publish(self, video_path, metadata):
        if self.ctx.dry_run:
            return {
                "platform": self.platform,
                "video_id": "dry",
                "url": "",
                "status": "skipped_dry_run",
            }
        raise ProviderError(
            f"{self.platform} publisher not implemented yet. "
            f"Register an implementation under src/providers/publisher/."
        )


@provider("publisher", "instagram")
class InstagramPublisher(_NotImplementedPublisher):
    platform = "instagram"


@provider("publisher", "facebook")
class FacebookPublisher(_NotImplementedPublisher):
    platform = "facebook"


@provider("publisher", "tiktok")
class TikTokPublisher(_NotImplementedPublisher):
    platform = "tiktok"
