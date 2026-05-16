import logging
import shutil

import pytest

from src.core.loader import load_plugins
from src.core.secrets import SecretResolver
from src.core.telemetry import Telemetry
from src.core.tool import build_tool, tools_manifest
from src.core.workflow import WorkflowRunner

load_plugins()

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def test_tools_manifest_has_audio_pack():
    names = {t["name"] for t in tools_manifest()}
    assert {"audio.silence", "audio.normalize", "audio.mix", "audio.concat"} <= names
    sil = next(t for t in tools_manifest() if t["name"] == "audio.silence")
    assert "seconds" in sil["inputs"] and sil["cost"] == "free"


def _agent_runner(allowed):
    wf = {
        "name": "agent_t",
        "providers": {
            "llm_default": {"kind": "llm", "provider": "gemini",
                            "model": "m", "options": {}}
        },
        "steps": [{
            "type": "agent",
            "params": {"llm": "llm_default", "goal": "make audio",
                       "allowed_tools": allowed, "max_steps": 4},
        }],
    }
    tel = Telemetry()
    sec = SecretResolver(environ={}, lenient=True)
    log = logging.getLogger("t")
    return WorkflowRunner(wf, {}, sec, tel, "/tmp/wfs_agent_test", True, log)


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg required for audio tools")
def test_agent_dry_run_plans_and_executes():
    runner = _agent_runner(["audio.silence", "audio.normalize"])
    res = runner.run()
    assert res["status"] == "ok"
    trace = runner.ctx.get("agent_trace")
    assert trace and trace[0]["tool"] == "audio.silence"
    assert "path" in trace[0]["result"]


def test_agent_rejects_disallowed_tool():
    runner = _agent_runner(["audio.normalize"])
    res = runner.run()
    assert res["status"] == "ok"
    assert runner.ctx.get("agent_trace") == []


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg required")
def test_audio_silence_tool_direct(tmp_path):
    from src.core.context import Context

    ctx = Context({"name": "x", "steps": []}, {}, SecretResolver(environ={}),
                  Telemetry(), str(tmp_path), True, logging.getLogger("t"))
    out = build_tool(ctx, "audio.silence").run(seconds=1)
    assert out["path"].endswith(".mp3")
