from ..core.errors import SafetyError
from ..core.factory import build_provider
from ..core.prompt import resolve_prompt
from ..core.registry import step
from ..core.step import Step

DEFAULT_BLOCKLIST = [
    "violence", "weapon", "gun", "blood", "kill", "drug", "alcohol",
    "gambling", "sexual", "nudity", "suicide", "self-harm", "hate",
]
DEFAULT_SAFETY_SYSTEM = "You are a strict child-safety content reviewer."
DEFAULT_SAFETY_PROMPT = (
    "Audience: {{audience}}. Review this content for safety, age-appropriateness, "
    "and brand risk.\nTitle: {{title}}\nScript: {{script}}\n"
    "Reject anything scary, violent, sexual, hateful, unsafe, deceptive, or that "
    "impersonates real brands/people. Respond strictly as JSON."
)


@step("safety_gate")
class SafetyGate(Step):
    def run(self, ctx):
        scenes = ctx.get("scenes", [])
        meta = ctx.get("metadata", {})
        subject = ctx.get("subject", {})
        script = " ".join(s.get("narration", "") for s in scenes)
        haystack = " ".join(
            [script, meta.get("title", ""), meta.get("description", ""),
             subject.get("title", "")]
        ).lower()

        blocklist = self.param(ctx, "blocklist", DEFAULT_BLOCKLIST)
        hits = [w for w in blocklist if w in haystack]
        if hits:
            raise SafetyError(f"blocked by keyword policy: {', '.join(sorted(hits))}")

        if not self.params.get("llm") or ctx.dry_run:
            ctx.set("safety", {"safe": True, "method": "keyword", "checked": True})
            ctx.logger.info("safety_gate: keyword check passed")
            return

        llm = build_provider(ctx, self.params["llm"])
        audience = self.param(ctx, "audience", "children")
        variables = {
            "audience": audience,
            "title": meta.get("title") or subject.get("title", ""),
            "script": script[:2000],
        }
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_SAFETY_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_SAFETY_SYSTEM, variables)
        verdict = llm.complete_json(
            prompt,
            {"safe": "bool", "reasons": ["str"]},
            {"safe": True, "reasons": []},
            system=system,
            step="safety_gate",
        )
        if not verdict.get("safe", False):
            raise SafetyError(
                "LLM safety review failed: " + "; ".join(verdict.get("reasons", []))
            )
        ctx.set("safety", {"safe": True, "method": "llm", "checked": True})
        ctx.logger.info("safety_gate: LLM review passed")
