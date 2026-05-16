import shutil
import subprocess
from abc import ABC, abstractmethod

from ..core.errors import ProviderError


def ffmpeg_bin():
    found = shutil.which("ffmpeg")
    if not found:
        raise ProviderError("ffmpeg not found on PATH")
    return found


def run_ffmpeg(args, cwd=None):
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 0:
        raise ProviderError(f"ffmpeg failed: {proc.stderr[:400]}")


class MediaProvider(ABC):
    kind = "media"

    def __init__(self, spec, ctx):
        self.spec = spec
        self.ctx = ctx
        self.options = spec.get("options", {})
        self.provider_name = spec.get("provider", "")


class TTSProvider(MediaProvider):
    kind = "tts"

    def synthesize(self, text, out_path):
        if self.ctx.dry_run:
            seconds = max(2, int(len(text.split()) / 2.6))
            run_ffmpeg(
                [
                    "-f", "lavfi",
                    "-i", f"anullsrc=r=24000:cl=mono",
                    "-t", str(seconds),
                    "-q:a", "9",
                    str(out_path),
                ]
            )
            self.ctx.telemetry.record_usage("tts", self.provider_name, units=len(text))
            return out_path
        result = self._synthesize(text, out_path)
        self.ctx.telemetry.record_usage("tts", self.provider_name, units=len(text))
        return result

    @abstractmethod
    def _synthesize(self, text, out_path):
        raise NotImplementedError


class ImageProvider(MediaProvider):
    kind = "image"

    def generate(self, prompt, out_path, size=(1080, 1920)):
        if self.ctx.dry_run:
            _placeholder_image(prompt, out_path, size)
            self.ctx.telemetry.record_usage("image", self.provider_name, units=1)
            return out_path
        result = self._generate(prompt, out_path, size)
        self.ctx.telemetry.record_usage("image", self.provider_name, units=1)
        return result

    @abstractmethod
    def _generate(self, prompt, out_path, size):
        raise NotImplementedError


class VideoProvider(MediaProvider):
    kind = "video"

    def assemble(self, plan, out_path):
        result = self._assemble(plan, out_path)
        self.ctx.telemetry.record_usage(
            "video", self.provider_name, units=1, cost_usd=plan.get("cost_usd", 0.0)
        )
        return result

    @abstractmethod
    def _assemble(self, plan, out_path):
        raise NotImplementedError


class Publisher(MediaProvider):
    kind = "publisher"

    @abstractmethod
    def publish(self, video_path, metadata):
        raise NotImplementedError


def _placeholder_image(prompt, out_path, size):
    from PIL import Image, ImageDraw

    width, height = size
    img = Image.new("RGB", (width, height), (28, 32, 64))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        shade = int(40 + (y / height) * 90)
        draw.line([(0, y), (width, y)], fill=(shade // 2, shade // 3, shade))
    words = prompt.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) > 28:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    text = "\n".join(lines[:10])
    draw.multiline_text(
        (width * 0.08, height * 0.4), text, fill=(255, 255, 255), spacing=14
    )
    img.save(out_path)
    return out_path
