from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import TTSProvider


@provider("tts", "gtts")
class GoogleTTS(TTSProvider):
    def _synthesize(self, text, out_path):
        try:
            from gtts import gTTS
        except ImportError as exc:
            raise ProviderError("gTTS not installed") from exc

        tts = gTTS(
            text=text,
            lang=self.options.get("lang", "en"),
            tld=self.options.get("tld", "com"),
            slow=self.options.get("slow", False),
        )
        tts.save(str(out_path))
        return out_path
