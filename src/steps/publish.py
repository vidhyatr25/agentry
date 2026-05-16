import json
import time
from pathlib import Path

from ..core.factory import build_provider
from ..core.prompt import resolve_prompt
from ..core.registry import step
from ..core.step import Step

DEFAULT_META_SYSTEM = "You are a YouTube growth and SEO specialist for kids channels."
DEFAULT_META_PROMPT = (
    "Create {{platform}} SEO metadata for a kids short video.\n"
    "Working title: {{title}}\nSummary: {{summary}}\nSeed keywords: {{keyword_seed}}\n"
    "Rules (2026 Shorts best practice): the primary search keyword MUST be in the first "
    "40 characters of the title; title under 70 chars, curiosity-driven, max 1 emoji, no "
    "false clickbait. Description: a strong 1-line hook, a 3-5 sentence keyword-rich "
    "summary, then exactly 3-5 niche hashtags plus #Shorts (never more than 5 total "
    "hashtags). Provide {{max_tags}} lowercase search tags. hashtags list: the same 3-5 "
    "niche tags plus #Shorts, each starting with #. Strictly family-safe."
)


@step("optimize_metadata")
class OptimizeMetadata(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        subject = ctx.get("subject", {})
        scenes = ctx.get("scenes", [])
        platform = self.param(ctx, "platform", "youtube")
        max_tags = int(self.param(ctx, "max_tags", 15))
        keyword_seed = self.param(ctx, "keyword_seed", [])
        summary = " ".join(s.get("narration", "") for s in scenes)[:800]
        variables = {
            "platform": platform,
            "title": subject.get("title"),
            "summary": summary,
            "keyword_seed": keyword_seed,
            "max_tags": max_tags,
        }
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_META_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_META_SYSTEM, variables)
        dry_default = {
            "title": (subject.get("title") or "A Tiny Seed's Big Adventure") + " 🌱",
            "description": "A gentle story for curious kids.\n\n#kids #learning #story",
            "tags": ["kids", "learning", "story", "education", "cartoon"][:max_tags],
            "hashtags": ["#kids", "#learning", "#kidsvideo", "#story", "#education"],
        }
        meta = llm.complete_json(
            prompt,
            {"title": "str", "description": "str", "tags": ["str"], "hashtags": ["str"]},
            dry_default,
            system=system,
            step="optimize_metadata",
        )
        meta.setdefault("tags", dry_default["tags"])
        meta.setdefault("hashtags", dry_default["hashtags"])
        meta["tags"] = meta["tags"][:max_tags]
        ctx.set("metadata", meta)
        ctx.logger.info(f"optimize_metadata -> {meta.get('title')}")


@step("publish")
class Publish(Step):
    def run(self, ctx):
        ref = self.params["publisher"]
        if ctx.dry_run:
            spec = ctx.workflow.get("providers", {}).get(ref, ref)
            real = spec.get("provider") if isinstance(spec, dict) else spec
            if real not in ("local",):
                ctx.logger.info(f"dry-run: routing publisher '{real}' -> local")
                ref = {"kind": "publisher", "provider": "local",
                       "options": {"output_dir": str(ctx.path("published"))}}
        publisher = build_provider(ctx, ref)
        metadata = ctx.get("metadata", {"title": "Untitled", "description": ""})
        video_path = ctx.get("video_path")
        result = publisher.publish(video_path, metadata)
        result["title"] = metadata.get("title")
        result["published_at"] = time.time()
        result["workflow"] = ctx.workflow.get("name")
        ctx.set("published", result)
        ctx.logger.info(f"publish -> {result.get('platform')} {result.get('url')}")


@step("record_stats")
class RecordStats(Step):
    def run(self, ctx):
        state_dir = Path(self.param(ctx, "state_dir", "state"))
        state_dir.mkdir(parents=True, exist_ok=True)
        published_file = state_dir / "published.json"
        published = []
        if published_file.exists():
            try:
                published = json.loads(published_file.read_text())
            except json.JSONDecodeError:
                published = []
        entry = dict(ctx.get("published") or {})
        entry["totals"] = ctx.telemetry.totals()
        entry["video_cost_usd"] = ctx.get("video_cost_usd", 0.0)
        published.append(entry)
        published = published[-1000:]
        published_file.write_text(json.dumps(published, indent=2))

        totals_cost = sum(
            p.get("totals", {}).get("cost_usd", 0.0) + p.get("video_cost_usd", 0.0)
            for p in published
        )
        totals_tokens = sum(
            p.get("totals", {}).get("total_tokens", 0) for p in published
        )
        stats = {
            "updated_at": time.time(),
            "videos_published": len(
                [p for p in published if p.get("status") in ("published", "saved")]
            ),
            "total_runs": len(published),
            "total_tokens": totals_tokens,
            "total_cost_usd": round(totals_cost, 4),
            "last": published[-1] if published else None,
            "recent": published[-20:][::-1],
        }
        (state_dir / "stats.json").write_text(json.dumps(stats, indent=2))
        ctx.logger.info(
            f"record_stats -> {stats['videos_published']} videos, "
            f"{stats['total_tokens']} tokens, ${stats['total_cost_usd']}"
        )
