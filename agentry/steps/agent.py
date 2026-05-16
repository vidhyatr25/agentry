from ..core.errors import BudgetError, StepError
from ..core.factory import build_provider
from ..core.prompt import resolve_prompt
from ..core.registry import registry, step
from ..core.step import Step
from ..core.tool import build_tool, tools_manifest

DEFAULT_AGENT_SYSTEM = (
    "You are an automation planner. Given a goal and a list of available tools "
    "with input schemas, output a minimal ordered plan of tool calls. Use only "
    "listed tools. Prefer free tools. Output strictly JSON."
)
DEFAULT_AGENT_PROMPT = (
    "Goal: {{goal}}\n\nAvailable tools:\n{{tools}}\n\n"
    "Context keys already available: {{context_keys}}\n"
    "Return JSON: a 'plan' list of steps, each {\"tool\": name, "
    "\"args\": {..}, \"save_as\": key}. Keep it as short as possible."
)


@step("agent")
class AgentStep(Step):
    def run(self, ctx):
        llm = build_provider(ctx, self.params["llm"])
        goal = self.param(ctx, "goal", "Accomplish the workflow objective.")
        max_steps = int(self.param(ctx, "max_steps", 8))
        allowed = self.param(ctx, "allowed_tools", None)
        registered = registry.names("tool")
        allowed = [t for t in (allowed or registered) if t in registered]
        manifest = [m for m in tools_manifest() if m["name"] in allowed]

        variables = {
            "goal": goal,
            "tools": manifest,
            "context_keys": sorted(ctx.data.keys()),
        }
        prompt = resolve_prompt(self, ctx, "prompt", DEFAULT_AGENT_PROMPT, variables)
        system = resolve_prompt(self, ctx, "system", DEFAULT_AGENT_SYSTEM, variables)
        if "audio.silence" in allowed:
            dry_default = {"plan": [
                {"tool": "audio.silence", "args": {"seconds": 2}, "save_as": "agent_audio"}
            ]}
        else:
            dry_default = {"plan": []}
        plan_doc = llm.complete_json(
            prompt,
            {"plan": [{"tool": "str", "args": {}, "save_as": "str"}]},
            dry_default,
            system=system,
            step="agent",
        )
        plan = plan_doc.get("plan", [])
        if not isinstance(plan, list):
            raise StepError("agent plan is not a list")
        if len(plan) > max_steps:
            raise StepError(f"agent plan has {len(plan)} steps, max is {max_steps}")

        budget = ctx.settings.get("budget", {})
        max_cost = float(budget.get("max_cost_usd", 0) or 0)
        max_tokens = int(budget.get("max_tokens", 0) or 0)

        trace = []
        for i, call in enumerate(plan):
            name = call.get("tool")
            if name not in allowed:
                raise StepError(f"agent tried disallowed/unknown tool: {name}")
            args = ctx.render(call.get("args", {}) or {})
            ctx.logger.info(f"agent[{i}] -> {name} {list(args)}")
            if ctx.dry_run and name not in ("audio.silence",):
                result = {"dry_run": True, "tool": name}
            else:
                try:
                    result = build_tool(ctx, name).run(**args)
                except BudgetError:
                    raise
                except Exception as exc:
                    raise StepError(
                        f"agent tool '{name}' failed: {ctx.secrets.mask(str(exc))}"
                    ) from exc
            save_as = call.get("save_as") or name.replace(".", "_")
            ctx.set(save_as, result)
            trace.append({"tool": name, "save_as": save_as, "result": result})
            breach = ctx.telemetry.over_budget(max_cost, max_tokens)
            if breach:
                ctx.set("agent_trace", trace)
                raise BudgetError(f"agent aborted: {breach}")

        ctx.set("agent_trace", trace)
        ctx.logger.info(f"agent completed {len(trace)} tool call(s)")
