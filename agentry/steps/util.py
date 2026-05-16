import json
import shutil
import subprocess

from ..core.errors import StepError


def ffprobe_duration(path):
    binary = shutil.which("ffprobe")
    if not binary:
        raise StepError("ffprobe not found on PATH")
    proc = subprocess.run(
        [
            binary,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise StepError(f"ffprobe failed: {proc.stderr[:200]}")
    return float(json.loads(proc.stdout)["format"]["duration"])


def concat_audio(parts, out_path):
    binary = shutil.which("ffmpeg")
    if not binary:
        raise StepError("ffmpeg not found on PATH")
    list_file = out_path.parent / "audio_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p}'" for p in parts), encoding="utf-8"
    )
    proc = subprocess.run(
        [
            binary, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        proc = subprocess.run(
            [
                binary, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c:a", "libmp3lame",
                str(out_path),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise StepError(f"audio concat failed: {proc.stderr[:200]}")
    return out_path
