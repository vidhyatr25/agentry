import asyncio

from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import TTSProvider


@provider("tts", "edge_tts")
class EdgeTTS(TTSProvider):
    def _synthesize(self, text, out_path):
        try:
            import edge_tts
        except ImportError as exc:
            raise ProviderError("edge-tts not installed") from exc

        voice = self.options.get("voice", "en-US-AnaNeural")
        rate = self.options.get("rate", "+0%")
        pitch = self.options.get("pitch", "+0Hz")

        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(str(out_path))

        asyncio.run(_run())
        return out_path
