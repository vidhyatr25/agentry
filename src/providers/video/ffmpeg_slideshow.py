import tempfile
from pathlib import Path

from ...core.registry import provider
from ..media import VideoProvider, run_ffmpeg


def _srt_timestamp(seconds):
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write_srt(scenes, path):
    lines = []
    clock = 0.0
    for index, scene in enumerate(scenes, start=1):
        duration = float(scene.get("duration", 4))
        caption = (scene.get("caption") or "").strip()
        if caption:
            lines.append(str(index))
            lines.append(
                f"{_srt_timestamp(clock)} --> {_srt_timestamp(clock + duration)}"
            )
            lines.append(caption)
            lines.append("")
        clock += duration
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@provider("video", "ffmpeg_slideshow")
class FfmpegSlideshow(VideoProvider):
    def _assemble(self, plan, out_path):
        scenes = plan["scenes"]
        width, height = plan.get("resolution", [1080, 1920])
        fps = plan.get("fps", 30)
        workdir = Path(tempfile.mkdtemp(prefix="wfs_video_"))
        segments = []
        for index, scene in enumerate(scenes):
            duration = float(scene.get("duration", 4))
            seg = workdir / f"seg_{index:03d}.mp4"
            zoom = self.options.get("zoom", 0.0012)
            total_frames = max(1, int(duration * fps))
            vf = (
                f"scale={width*2}:-2,"
                f"zoompan=z='min(zoom+{zoom},1.5)':d={total_frames}"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":s={width}x{height}:fps={fps},"
                f"setsar=1"
            )
            run_ffmpeg(
                [
                    "-loop", "1",
                    "-i", str(scene["image"]),
                    "-t", f"{duration}",
                    "-vf", vf,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", str(fps),
                    str(seg),
                ]
            )
            segments.append(seg)

        concat_file = workdir / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{seg}'" for seg in segments), encoding="utf-8"
        )
        silent_video = workdir / "video.mp4"
        run_ffmpeg(
            [
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(silent_video),
            ]
        )

        audio_inputs = ["-i", str(plan["audio"])]
        filter_complex = None
        audio_map = "1:a"
        music = plan.get("music")
        if music and Path(music).exists():
            audio_inputs += ["-i", str(music)]
            volume = self.options.get("music_volume", 0.12)
            filter_complex = (
                f"[2:a]volume={volume}[bg];"
                f"[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            audio_map = "[aout]"

        final_args = ["-i", str(silent_video), *audio_inputs]
        if plan.get("subtitles"):
            srt = _write_srt(scenes, workdir / "captions.srt")
            style = self.options.get(
                "subtitle_style",
                "FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
                "BorderStyle=3,Alignment=2,MarginV=90",
            )
            sub_filter = f"subtitles={srt}:force_style='{style}'"
            if filter_complex:
                filter_complex = f"[0:v]{sub_filter}[v];" + filter_complex
                final_args += ["-filter_complex", filter_complex, "-map", "[v]", "-map", audio_map]
            else:
                final_args += ["-vf", sub_filter, "-map", "0:v", "-map", audio_map]
        else:
            if filter_complex:
                final_args += ["-filter_complex", filter_complex, "-map", "0:v", "-map", audio_map]
            else:
                final_args += ["-map", "0:v", "-map", audio_map]

        final_args += [
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_path),
        ]
        run_ffmpeg(final_args)
        return out_path
