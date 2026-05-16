import re

import requests

from ..core.factory import build_provider
from ..core.registry import step
from ..core.step import Step


def _fetch_headlines(url, limit):
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "workflow-studio"})
        titles = re.findall(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
        cleaned = [
            re.sub(r"<!\[CDATA\[|\]\]>", "", t).strip()
            for t in titles
            if t.strip()
        ]
        return cleaned[1 : limit + 1]
    except requests.RequestException:
        return []


@step("research_trends")
class ResearchTrends(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        audience = self.param(ctx, "audience", "kids aged 4-8")
        count = int(self.param(ctx, "count", 5))
        theme = self.param(ctx, "theme", "fun educational stories")
        feed = self.param(ctx, "news_feed")
        headlines = _fetch_headlines(feed, 8) if feed else []
        context_block = (
            "Recent safe headlines for inspiration: " + " | ".join(headlines)
            if headlines
            else "No external feed; use evergreen ideas."
        )
        prompt = (
            f"You plan a children's YouTube channel for {audience}. Theme: {theme}. "
            f"{context_block}\n"
            f"Propose {count} fresh, safe, highly clickable video topic ideas that "
            f"teach something positive. Avoid anything scary, branded, or unsafe."
        )
        dry_default = {
            "topics": [
                {"title": f"Why the Sky Changes Colors (Idea {i+1})",
                 "why": "curiosity + science", "keywords": ["sky", "colors", "science for kids"]}
                for i in range(count)
            ]
        }
        result = llm.complete_json(
            prompt,
            {"topics": [{"title": "str", "why": "str", "keywords": ["str"]}]},
            dry_default,
            system="You are a kids content strategist focused on safety and curiosity.",
            step="research_trends",
        )
        ctx.set("topics", result.get("topics", dry_default["topics"]))
        ctx.logger.info(f"research_trends produced {len(ctx.get('topics'))} topics")


@step("pick_subject")
class PickSubject(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        topics = ctx.get("topics", [])
        audience = self.param(ctx, "audience", "kids aged 4-8")
        prompt = (
            f"From these topics: {topics}\n"
            f"Pick the single best one for {audience} and build a creative brief: "
            f"a catchy working title, the core learning goal, the emotional hook, "
            f"and a warm narration tone."
        )
        dry_default = {
            "title": topics[0]["title"] if topics else "A Tiny Seed's Big Adventure",
            "learning_goal": "how plants grow",
            "hook": "a seed dreams of touching the sky",
            "tone": "gentle, playful, encouraging",
        }
        brief = llm.complete_json(
            prompt,
            {"title": "str", "learning_goal": "str", "hook": "str", "tone": "str"},
            dry_default,
            system="You are a children's storyteller and educator.",
            step="pick_subject",
        )
        ctx.set("subject", brief)
        ctx.logger.info(f"pick_subject -> {brief.get('title')}")


@step("write_script")
class WriteScript(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        subject = ctx.get("subject", {})
        scene_count = int(self.param(ctx, "scene_count", 6))
        words_target = int(self.param(ctx, "words_target", 130))
        prompt = (
            f"Write a narrated short video script for children.\n"
            f"Title: {subject.get('title')}\nLearning goal: {subject.get('learning_goal')}\n"
            f"Hook: {subject.get('hook')}\nTone: {subject.get('tone')}\n"
            f"Total narration about {words_target} words across {scene_count} scenes. "
            f"Each scene: one or two short spoken sentences and a vivid visual description. "
            f"End with a friendly call to subscribe."
        )
        dry_default = {
            "scenes": [
                {
                    "narration": f"Scene {i+1}: A little seed wakes up and looks around with wonder.",
                    "visual": "a smiling cartoon seed in soft morning light, bright and cozy",
                }
                for i in range(scene_count)
            ]
        }
        script = llm.complete_json(
            prompt,
            {"scenes": [{"narration": "str", "visual": "str"}]},
            dry_default,
            system="You write safe, warm, age-appropriate kids scripts.",
            step="write_script",
        )
        scenes = script.get("scenes") or dry_default["scenes"]
        ctx.set("scenes", [dict(s) for s in scenes])
        ctx.logger.info(f"write_script -> {len(ctx.get('scenes'))} scenes")


@step("build_visual_prompts")
class BuildVisualPrompts(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        scenes = ctx.get("scenes", [])
        style = self.param(
            ctx, "style", "bright 3D Pixar-style cartoon, soft lighting, kid friendly"
        )
        descriptions = [s.get("visual", s.get("narration", "")) for s in scenes]
        prompt = (
            f"Global art style: {style}. Keep characters and palette consistent.\n"
            f"For each scene visual below, write a detailed image-generation prompt and "
            f"a very short on-screen caption (max 8 words).\nScenes: {descriptions}"
        )
        dry_default = {
            "items": [
                {
                    "image_prompt": f"{style}, {d}",
                    "caption": (scenes[i].get("narration", "")[:40] if i < len(scenes) else ""),
                }
                for i, d in enumerate(descriptions)
            ]
        }
        result = llm.complete_json(
            prompt,
            {"items": [{"image_prompt": "str", "caption": "str"}]},
            dry_default,
            system="You are a prompt engineer for consistent kids illustrations.",
            step="build_visual_prompts",
        )
        items = result.get("items") or dry_default["items"]
        for index, scene in enumerate(scenes):
            item = items[index] if index < len(items) else dry_default["items"][index]
            scene["image_prompt"] = item.get("image_prompt", f"{style}")
            scene["caption"] = item.get("caption", scene.get("narration", "")[:60])
        ctx.set("scenes", scenes)
        ctx.logger.info("build_visual_prompts attached prompts to scenes")
