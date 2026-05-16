import json
import shutil
from pathlib import Path

from ...core.registry import provider
from ..media import Publisher


@provider("publisher", "local")
class LocalPublisher(Publisher):
    def publish(self, video_path, metadata):
        out_dir = Path(self.options.get("output_dir", "runs/published"))
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(video_path).stem
        dest = out_dir / f"{stem}.mp4"
        shutil.copy2(video_path, dest)
        meta_path = out_dir / f"{stem}.json"
        meta_path.write_text(json.dumps(metadata, indent=2))
        return {
            "platform": "local",
            "video_id": stem,
            "url": str(dest),
            "status": "saved",
        }
