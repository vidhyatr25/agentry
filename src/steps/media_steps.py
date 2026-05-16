from ..core.factory import build_provider
from ..core.registry import step
from ..core.step import Step
from .util import concat_audio, ffprobe_duration


@step("synthesize_voice")
class SynthesizeVoice(Step):
    def run(self, ctx):
        tts = build_provider(ctx, self.params["tts"])
        scenes = ctx.get("scenes", [])
        parts = []
        for index, scene in enumerate(scenes):
            text = scene.get("narration", "").strip() or scene.get("caption", "")
            part_path = ctx.path("audio", f"scene_{index:03d}.mp3")
            tts.synthesize(text, part_path)
            duration = ffprobe_duration(part_path)
            scene["duration"] = round(max(1.5, duration + 0.4), 2)
            parts.append(part_path)
        narration = ctx.path("audio", "narration.mp3")
        concat_audio(parts, narration)
        ctx.set("audio_path", str(narration))
        ctx.set("scenes", scenes)
        total = round(sum(s["duration"] for s in scenes), 2)
        ctx.logger.info(f"synthesize_voice -> {narration} ({total}s)")


@step("generate_images")
class GenerateImages(Step):
    def run(self, ctx):
        image = build_provider(ctx, self.params["image"])
        scenes = ctx.get("scenes", [])
        video_cfg = ctx.workflow.get("video", {})
        size = tuple(video_cfg.get("resolution", [1080, 1920]))
        for index, scene in enumerate(scenes):
            out_path = ctx.path("images", f"scene_{index:03d}.png")
            prompt = scene.get("image_prompt") or scene.get("visual", "")
            image.generate(prompt, out_path, size=size)
            scene["image"] = str(out_path)
        ctx.set("scenes", scenes)
        ctx.logger.info(f"generate_images -> {len(scenes)} images")


@step("assemble_video")
class AssembleVideo(Step):
    def run(self, ctx):
        video = build_provider(ctx, self.params["video"])
        scenes = ctx.get("scenes", [])
        video_cfg = ctx.workflow.get("video", {})
        music = self.param(ctx, "music")
        plan = {
            "scenes": [
                {
                    "image": s.get("image"),
                    "duration": s.get("duration", 4),
                    "caption": s.get("caption", ""),
                }
                for s in scenes
            ],
            "audio": ctx.get("audio_path"),
            "music": music,
            "resolution": video_cfg.get("resolution", [1080, 1920]),
            "fps": video_cfg.get("fps", 30),
            "subtitles": bool(self.param(ctx, "subtitles", True)),
            "video_prompt": " ".join(s.get("image_prompt", "") for s in scenes)[:1500],
        }
        out_path = ctx.path("video", "final.mp4")
        video.assemble(plan, out_path)
        ctx.set("video_path", str(out_path))
        ctx.set("video_cost_usd", plan.get("cost_usd", 0.0))
        ctx.logger.info(f"assemble_video -> {out_path}")
