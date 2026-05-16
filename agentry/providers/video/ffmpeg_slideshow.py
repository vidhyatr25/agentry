import tempfile
from pathlib import Path

from ...core.errors import ProviderError
from ...core.registry import provider
from ..media import VideoProvider, run_ffmpeg


def _ass_ts(seconds):
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def _write_ass(scenes, path, width, height, options):
    fontsize = int(options.get("subtitle_fontsize", max(36, height // 28)))
    margin_v = int(options.get("subtitle_margin_v", max(80, height // 12)))
    font = options.get("subtitle_font", "DejaVu Sans")
    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 2",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font},{fontsize},&H00FFFFFF,&H00000000,&H96000000,"
        f"-1,0,0,0,100,100,0,0,3,2,1,2,60,60,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    clock = 0.0
    for scene in scenes:
        duration = float(scene.get("duration", 4))
        caption = (scene.get("caption") or "").strip()
        if caption:
            header.append(
                f"Dialogue: 0,{_ass_ts(clock)},{_ass_ts(clock + duration)},"
                f"Default,,0,0,0,,{_ass_escape(caption)}"
            )
        clock += duration
    path.write_text("\n".join(header), encoding="utf-8")
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
                f"scale={width * 2}:-2,"
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
            "\n".join(f"file '{seg.name}'" for seg in segments), encoding="utf-8"
        )
        silent_video = workdir / "video.mp4"
        try:
            run_ffmpeg(
                ["-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "video.mp4"],
                cwd=str(workdir),
            )
        except ProviderError:
            run_ffmpeg(
                ["-f", "concat", "-safe", "0", "-i", "concat.txt",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), "video.mp4"],
                cwd=str(workdir),
            )

        audio_inputs = ["-i", str(plan["audio"])]
        audio_map = "1:a"
        music = plan.get("music")
        mix = None
        if music and Path(music).exists():
            audio_inputs += ["-i", str(music)]
            volume = self.options.get("music_volume", 0.12)
            mix = (
                f"[2:a]volume={volume}[bg];"
                f"[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            audio_map = "[aout]"

        tail = [
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_path),
        ]

        def build(with_subs):
            args = ["-i", "video.mp4", *audio_inputs]
            if with_subs:
                if mix:
                    args += ["-filter_complex", f"[0:v]ass=captions.ass[v];{mix}",
                             "-map", "[v]", "-map", audio_map]
                else:
                    args += ["-vf", "ass=captions.ass", "-map", "0:v", "-map", audio_map]
            else:
                if mix:
                    args += ["-filter_complex", mix, "-map", "0:v", "-map", audio_map]
                else:
                    args += ["-map", "0:v", "-map", audio_map]
            return args + tail

        want_subs = bool(plan.get("subtitles"))
        if want_subs:
            _write_ass(scenes, workdir / "captions.ass", width, height, self.options)
        try:
            run_ffmpeg(build(want_subs), cwd=str(workdir))
        except ProviderError:
            if not want_subs:
                raise
            self.ctx.logger.info(
                "assemble_video: caption burn unavailable (ffmpeg without libass?); "
                "producing video without burned captions"
            )
            run_ffmpeg(build(False), cwd=str(workdir))
        return out_path
