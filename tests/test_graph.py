import json
import logging
from pathlib import Path

import pytest

<<<<<<< HEAD
from agentry.core.config import load_json, validate_workflow
from agentry.core.errors import WorkflowError
from agentry.core.loader import load_plugins
from agentry.core.registry import registry
from agentry.core.secrets import SecretResolver
from agentry.core.step import Step
from agentry.core.telemetry import Telemetry
from agentry.core.workflow import WorkflowRunner
=======
from src.core.config import load_json, validate_workflow
from src.core.errors import WorkflowError
from src.core.loader import load_plugins
from src.core.registry import registry
from src.core.secrets import SecretResolver
from src.core.step import Step
from src.core.telemetry import Telemetry
from src.core.workflow import WorkflowRunner
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0

load_plugins()

if "t_rec" not in registry.names("step"):
    @registry.register("step", "t_rec")
    class _Rec(Step):
        def run(self, ctx):
            log = ctx.get("_order", [])
            log.append(self.params.get("tag"))
            ctx.set("_order", log)
            if self.params.get("emit"):
                ctx.set(self.params["emit"], self.params.get("value", "1"))


def _run(nodes):
    wf = {"name": "g", "providers": {}, "nodes": nodes}
    return WorkflowRunner(wf, {}, SecretResolver(environ={}, lenient=True),
                          Telemetry(), "/tmp/wfs_g", True, logging.getLogger("t"))


def test_graph_topo_respects_needs():
    r = _run([
        {"id": "c", "type": "t_rec", "needs": ["b"], "params": {"tag": "c"}},
        {"id": "a", "type": "t_rec", "needs": [], "params": {"tag": "a"}},
        {"id": "b", "type": "t_rec", "needs": ["a"], "params": {"tag": "b"}},
    ])
    res = r.run()
    assert res["status"] == "ok" and res["mode"] == "graph"
    assert r.ctx.get("_order") == ["a", "b", "c"]


def test_graph_cycle_detected():
    r = _run([
        {"id": "x", "type": "t_rec", "needs": ["y"], "params": {"tag": "x"}},
        {"id": "y", "type": "t_rec", "needs": ["x"], "params": {"tag": "y"}},
    ])
    with pytest.raises(WorkflowError):
        r.run()


def test_graph_unknown_dependency():
    r = _run([{"id": "x", "type": "t_rec", "needs": ["ghost"], "params": {"tag": "x"}}])
    with pytest.raises(WorkflowError):
        r.run()


def test_graph_conditional_when_skips():
    r = _run([
        {"id": "gate", "type": "t_rec", "needs": [],
         "params": {"tag": "gate", "emit": "flag", "value": "false"}},
        {"id": "maybe", "type": "t_rec", "needs": ["gate"],
         "when": "{{ flag }}", "params": {"tag": "maybe"}},
    ])
    res = r.run()
    assert r.ctx.get("_order") == ["gate"]
    statuses = {s["id"]: s["status"] for s in res["steps"]}
    assert statuses["maybe"] == "skipped"


def test_example_graph_validates():
    wf = validate_workflow(load_json(
        str(Path(__file__).resolve().parent.parent / "workflows" / "example_graph.json")
    ))
    assert wf["nodes"] and wf["name"] == "example_graph"
