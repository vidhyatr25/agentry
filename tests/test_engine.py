import datetime as dt
import logging

import pytest

<<<<<<< HEAD
from agentry.core.config import deep_merge, validate_workflow
from agentry.core.errors import BudgetError, ConfigError, SecretError
from agentry.core.prompt import render_prompt
from agentry.core.registry import Registry, RegistryError
from agentry.core.scheduler import cron_match, due_in_window
from agentry.core.secrets import SecretResolver
from agentry.core.telemetry import Telemetry
=======
from src.core.config import deep_merge, validate_workflow
from src.core.errors import BudgetError, ConfigError, SecretError
from src.core.prompt import render_prompt
from src.core.registry import Registry, RegistryError
from src.core.scheduler import cron_match, due_in_window
from src.core.secrets import SecretResolver
from src.core.telemetry import Telemetry
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0


def test_registry_register_get_and_duplicate():
    r = Registry()
    r.register("step", "a")(lambda: 1)
    assert r.get("step", "a")() == 1
    with pytest.raises(RegistryError):
        r.get("step", "missing")
    with pytest.raises(RegistryError):
        r.register("step", "a")(lambda: 2)


def test_prompt_render_flat_nested_and_missing():
    assert render_prompt("hi {{a}} {{b.c}}", {"a": "X", "b": {"c": "Y"}}) == "hi X Y"
    assert render_prompt("v={{missing}}", {}) == "v="
    assert render_prompt("list={{xs}}", {"xs": [1, 2]}) == "list=[1, 2]"


def test_deep_merge_is_recursive_and_non_destructive():
    base = {"a": {"x": 1, "y": 2}, "k": 1}
    over = {"a": {"y": 9, "z": 3}}
    merged = deep_merge(base, over)
    assert merged == {"a": {"x": 1, "y": 9, "z": 3}, "k": 1}
    assert base["a"]["y"] == 2


def test_secret_resolver_masks_and_requires():
    s = SecretResolver(environ={"TOK": "supersecretvalue"})
    assert s.resolve("Bearer ${TOK}") == "Bearer supersecretvalue"
    assert "***TOK***" in s.mask("leak supersecretvalue here")
    with pytest.raises(SecretError):
        s.resolve("${NOPE}")
    lenient = SecretResolver(environ={}, lenient=True)
    assert "__MISSING_NOPE__" in lenient.resolve("${NOPE}")


def test_telemetry_cost_and_budget():
    t = Telemetry(pricing={"gemini": {"m": {"in": 1.0, "out": 2.0}}})
    t.record_llm("gemini", "m", 1000, 1000)
    totals = t.totals()
    assert totals["total_tokens"] == 2000
    assert round(totals["cost_usd"], 4) == 3.0
    assert t.over_budget(max_cost_usd=1.0)
    assert t.over_budget(max_tokens=100)
    assert t.over_budget(max_cost_usd=10.0, max_tokens=0) is None


def test_cron_match_and_due_window_dedup():
    assert cron_match("0 6,12,18 * * *", dt.datetime(2026, 5, 16, 12, 0))
    assert not cron_match("0 6,12,18 * * *", dt.datetime(2026, 5, 16, 12, 5))
    assert cron_match("*/15 * * * *", dt.datetime(2026, 5, 16, 9, 30))
    now = dt.datetime(2026, 5, 16, 12, 10)
    due, hit = due_in_window("0 12 * * *", now, 35, None)
    assert due and hit
    again, _ = due_in_window("0 12 * * *", now, 35, hit)
    assert not again


def test_validate_workflow_rules():
    with pytest.raises(ConfigError):
        validate_workflow({"name": "x"})
    with pytest.raises(ConfigError):
        validate_workflow({"name": "x", "steps": []})
    ok = validate_workflow({"name": "x", "steps": [{"type": "noop"}]})
    assert ok["name"] == "x"


def _runner(steps, settings=None):
<<<<<<< HEAD
    from agentry.core.context import Context
    from agentry.core.registry import registry, step
    from agentry.core.workflow import WorkflowRunner
=======
    from src.core.context import Context
    from src.core.registry import registry, step
    from src.core.workflow import WorkflowRunner
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0

    wf = {"name": "t", "steps": steps, "providers": {}}
    pricing = (settings or {}).get("telemetry", {}).get("pricing", {})
    tel = Telemetry(pricing=pricing)
    sec = SecretResolver(environ={}, lenient=True)
    log = logging.getLogger("test")
    return WorkflowRunner(wf, settings or {}, sec, tel, "/tmp/wfs_test", True, log), registry, step


def test_pipeline_runs_steps_and_passes_context(tmp_path):
<<<<<<< HEAD
    from agentry.core.registry import registry
    from agentry.core.step import Step
=======
    from src.core.registry import registry
    from src.core.step import Step
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0

    if "t_set" not in registry.names("step"):
        @registry.register("step", "t_set")
        class _Set(Step):
            def run(self, ctx):
                ctx.set("hello", self.params.get("v", 1))

    runner, _, _ = _runner([{"type": "t_set", "params": {"v": 42}}])
    res = runner.run()
    assert res["status"] == "ok"
    assert runner.ctx.get("hello") == 42


def test_budget_breaker_aborts(tmp_path):
<<<<<<< HEAD
    from agentry.core.registry import registry
    from agentry.core.step import Step
=======
    from src.core.registry import registry
    from src.core.step import Step
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0

    if "t_burn" not in registry.names("step"):
        @registry.register("step", "t_burn")
        class _Burn(Step):
            def run(self, ctx):
                ctx.telemetry.record_llm("gemini", "m", 100000, 100000)

    runner, _, _ = _runner(
        [{"type": "t_burn"}],
        settings={"telemetry": {"pricing": {"gemini": {"m": {"in": 1, "out": 1}}}},
                  "budget": {"max_cost_usd": 0.01}},
    )
    with pytest.raises(BudgetError):
        runner.run()
