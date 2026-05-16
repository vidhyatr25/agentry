import re

import requests

from ..core.factory import build_provider
from ..core.prompt import resolve_prompt
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


DEFAULT_RESEARCH_SYSTEM = "You are a kids content strategist focused on safety and curiosity."
DEFAULT_RESEARCH_PROMPT = (
    "You plan a children's video channel for {{audience}}. Theme: {{theme}}. "
    "{{news_context}}\n"
    "Propose {{count}} fresh, safe, highly clickable video topic ideas that teach "
    "something positive. Avoid anything scary, branded, or unsafe."
)


@step("research_trends")
class ResearchTrends(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        audience = self.param(ctx, "audience", "kids aged 4-8")
        count = int(self.param(ctx, "count", 5))
        theme = self.param(ctx, "theme", "fun educational stories")
        feed = self.param(ctx, "news_feed")
        headlines = _fetch_headlines(feed, 8) if feed else []
        news_context = (
            "Recent safe headlines for inspiration: " + " | ".join(headlines)
            if headlines
            else "No external feed; use evergreen ideas."
        )
        variables = {
            "audience": audience,
            "theme": theme,
            "count": count,
            "news_context": news_context,
        }
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_RESEARCH_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_RESEARCH_SYSTEM, variables)
        dry_default = {
            "topics": [
                {
                    "title": f"Why the Sky Changes Colors (Idea {i+1})",
                    "why": "curiosity + science",
                    "keywords": ["sky", "colors", "science for kids"],
                }
                for i in range(count)
            ]
        }
        result = llm.complete_json(
            prompt,
            {"topics": [{"title": "str", "why": "str", "keywords": ["str"]}]},
            dry_default,
            system=system,
            step="research_trends",
        )
        ctx.set("topics", result.get("topics", dry_default["topics"]))
        ctx.logger.info(f"research_trends produced {len(ctx.get('topics'))} topics")


DEFAULT_SUBJECT_SYSTEM = "You are a children's storyteller and educator."
DEFAULT_SUBJECT_PROMPT = (
    "From these topics: {{topics}}\n"
    "Pick the single best one for {{audience}} and build a creative brief: a catchy "
    "working title, the core learning goal, the emotional hook, and a warm narration tone."
)


@step("pick_subject")
class PickSubject(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        topics = ctx.get("topics", [])
        audience = self.param(ctx, "audience", "kids aged 4-8")
        variables = {"topics": topics, "audience": audience}
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_SUBJECT_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_SUBJECT_SYSTEM, variables)
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
            system=system,
            step="pick_subject",
        )
        ctx.set("subject", brief)
        ctx.logger.info(f"pick_subject -> {brief.get('title')}")


DEFAULT_SCRIPT_SYSTEM = "You write safe, warm, age-appropriate kids scripts."
DEFAULT_SCRIPT_PROMPT = (
    "Write a narrated short video script for children.\n"
    "Title: {{subject.title}}\nLearning goal: {{subject.learning_goal}}\n"
    "Hook: {{subject.hook}}\nTone: {{subject.tone}}\n"
    "Total narration about {{words_target}} words across {{scene_count}} scenes. "
    "Each scene: one or two short spoken sentences and a vivid visual description. "
    "Open with the hook in the first sentence. End with a friendly call to subscribe."
)


@step("write_script")
class WriteScript(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        subject = ctx.get("subject", {})
        scene_count = int(self.param(ctx, "scene_count", 6))
        words_target = int(self.param(ctx, "words_target", 130))
        variables = {
            "subject": subject,
            "scene_count": scene_count,
            "words_target": words_target,
        }
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_SCRIPT_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_SCRIPT_SYSTEM, variables)
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
            system=system,
            step="write_script",
        )
        scenes = script.get("scenes") or dry_default["scenes"]
        ctx.set("scenes", [dict(s) for s in scenes])
        ctx.logger.info(f"write_script -> {len(ctx.get('scenes'))} scenes")


DEFAULT_VISUAL_SYSTEM = "You are a prompt engineer for consistent kids illustrations."
DEFAULT_VISUAL_PROMPT = (
    "Global art style: {{style}}. Keep characters and palette consistent.\n"
    "For each scene visual below, write a detailed image-generation prompt and a very "
    "short on-screen caption (max 8 words).\nScenes: {{scene_descriptions}}"
)


@step("build_visual_prompts")
class BuildVisualPrompts(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        scenes = ctx.get("scenes", [])
        style = self.param(
            ctx, "style", "bright 3D Pixar-style cartoon, soft lighting, kid friendly"
        )
        descriptions = [s.get("visual", s.get("narration", "")) for s in scenes]
        variables = {"style": style, "scene_descriptions": descriptions}
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_VISUAL_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_VISUAL_SYSTEM, variables)
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
            system=system,
            step="build_visual_prompts",
        )
        items = result.get("items") or dry_default["items"]
        for index, scene in enumerate(scenes):
            item = items[index] if index < len(items) else dry_default["items"][index]
            scene["image_prompt"] = item.get("image_prompt", f"{style}")
            scene["caption"] = item.get("caption", scene.get("narration", "")[:60])
        ctx.set("scenes", scenes)
        ctx.logger.info("build_visual_prompts attached prompts to scenes")
