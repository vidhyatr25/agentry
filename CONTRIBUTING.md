# Contributing to Agentry

Thanks for considering a contribution! Agentry is designed to be the
**easiest agentic workflow engine to extend** — one file per plugin, no
core changes. Anything you add benefits everyone.

## Three ways to contribute (5 → 60 minutes)

### 🧩 1. Add a provider (5–15 min)
LLM, TTS, image, video, or publisher. One file, one decorator:

```python
# agentry/providers/llm/myprovider.py
from agentry.core.registry import provider
from agentry.providers.llm.base import LLMProvider, LLMResult

@provider("llm", "myprovider")
class MyProvider(LLMProvider):
    def _complete(self, prompt, system, **_):
        ...
        return LLMResult(text=..., prompt_tokens=..., completion_tokens=..., model=self.model)
```

Reference `"provider": "myprovider"` from any workflow JSON. Done.

### 🛠 2. Add a tool (10–30 min)
Tools are agent-callable capabilities. See `agentry/tools/audio.py` for examples.

```python
# agentry/tools/notify.py
from agentry.core.registry import tool
from agentry.core.tool import Tool

@tool("notify.slack")
class SlackNotify(Tool):
    name = "notify.slack"
    description = "Post a message to a Slack channel via webhook."
    cost = "free"
    inputs = {"webhook_url": "string", "text": "string"}
    outputs = {"ok": "bool"}

    def run(self, webhook_url, text, **_):
        import requests
        r = requests.post(webhook_url, json={"text": text}, timeout=20)
        return {"ok": r.ok}
```

### 🎬 3. Add a workflow (5 min, no code)
One JSON file in `workflows/`. See `workflows/example_*.json` for templates.
We feature great community workflows in the README.

## Development setup

```bash
git clone https://github.com/vidhyatr25/agentry && cd agentry
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
brew install ffmpeg                       # or: sudo apt install ffmpeg
python -m agentry.cli doctor              # preflight
python -m pytest tests/ -q                # 18 tests should pass
python -m agentry.cli run workflows/kids_video_youtube.json --dry-run
```

## PR checklist
- [ ] `python -m pytest tests/ -q` green.
- [ ] If you added a provider/tool/step, include a test (see `tests/test_tools_agent.py`).
- [ ] If you added a workflow, run `python -m agentry.cli validate workflows/your.json`.
- [ ] No code comments (intentional — names should be self-explanatory).
- [ ] No secrets in the diff. Use `${ENV_NAME}` references and document required env vars.
- [ ] Update `CHANGELOG.md` under an *Unreleased* section.

## Code style
- Black-style formatting (no enforcement yet; PRs with mixed styles still merge).
- Type hints encouraged in `agentry/core/`.
- Prefer one file per provider/tool/step.

## Good first issues
Check the [good first issue](../../labels/good%20first%20issue) label —
typically: add a new TTS voice, port a notify channel, write a niche
workflow JSON, port a publisher.

## Community
- 💬 Open a [Discussion](../../discussions) for ideas/questions.
- 🐛 [Open an issue](../../issues/new/choose) for bugs and proposals.
- ⭐ If this saves you time, **star the repo** — it really helps others find it.

## License
By contributing you agree your changes are released under the MIT License.
