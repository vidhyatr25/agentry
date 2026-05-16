from pathlib import Path

from ..core.registry import tool
from ..core.tool import Tool
from ..providers.media import run_ffmpeg


@tool("audio.silence")
class AudioSilence(Tool):
    name = "audio.silence"
    description = "Generate a silent audio track of N seconds (free, offline)."
    cost = "free"
    inputs = {"seconds": "float", "out": "string(optional)"}
    outputs = {"path": "string"}

    def run(self, seconds=3.0, out=None, **_):
        path = Path(out) if out else self.ctx.path("audio", "silence.mp3")
        run_ffmpeg(
            ["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
             "-t", str(float(seconds)), "-q:a", "9", str(path)]
        )
        return {"path": str(path)}


@tool("audio.normalize")
class AudioNormalize(Tool):
    name = "audio.normalize"
    description = "Loudness-normalize audio to broadcast level (EBU R128). Free."
    cost = "free"
    inputs = {"path": "string", "target_i": "float(optional,-16)"}
    outputs = {"path": "string"}

    def run(self, path, target_i=-16.0, **_):
        out = self.ctx.path("audio", Path(path).stem + "_norm.mp3")
        run_ffmpeg(
            ["-i", str(path),
             "-af", f"loudnorm=I={target_i}:TP=-1.5:LRA=11",
             "-ar", "44100", str(out)]
        )
        return {"path": str(out)}


@tool("audio.concat")
class AudioConcat(Tool):
    name = "audio.concat"
    description = "Concatenate a list of audio files into one track. Free."
    cost = "free"
    inputs = {"parts": "list[string]"}
    outputs = {"path": "string"}

    def run(self, parts, **_):
        out = self.ctx.path("audio", "concat.mp3")
        listing = self.ctx.path("audio", "concat_list.txt")
        Path(listing).write_text(
            "\n".join(f"file '{Path(p).resolve()}'" for p in parts), encoding="utf-8"
        )
        try:
            run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c", "copy", str(out)])
        except Exception:
            run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c:a", "libmp3lame", str(out)])
        return {"path": str(out)}


@tool("audio.mix")
class AudioMix(Tool):
    name = "audio.mix"
    description = (
        "Mix narration over background music with sidechain ducking "
        "(music dips automatically under speech). Free, ffmpeg."
    )
    cost = "free"
    inputs = {
        "narration": "string",
        "music": "string",
        "music_volume": "float(optional,0.35)",
    }
    outputs = {"path": "string"}

    def run(self, narration, music, music_volume=0.35, **_):
        out = self.ctx.path("audio", "mixed.mp3")
        fc = (
            f"[1:a]volume={music_volume}[m];"
            f"[m][0:a]sidechaincompress=threshold=0.03:ratio=12:attack=20:"
            f"release=350[duck];"
            f"[0:a][duck]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
        run_ffmpeg(
            ["-i", str(narration), "-i", str(music),
             "-filter_complex", fc, "-map", "[a]",
             "-c:a", "libmp3lame", "-q:a", "3", str(out)]
        )
        return {"path": str(out)}
