# Workflow Studio

A config-driven automation engine that researches a topic, writes a script,
generates a voiceover, generates images, assembles a video, optimizes it for
reach, and publishes it — on a schedule, for free, hosted entirely on GitHub.

The first workflow ships ready: **AI kids videos → YouTube, 3× per day.**
The same engine runs any future workflow (Instagram, Facebook, TikTok, …) by
adding one JSON file — no code changes.

---

## How it stays free

| Component        | Cost                                              |
|------------------|---------------------------------------------------|
| Scheduling/host  | GitHub Actions (free minutes)                     |
| Dashboard        | GitHub Pages (free)                               |
| Voiceover        | `edge_tts` / `gtts` (free, no key)                |
| Images           | `pollinations` (free, no key)                     |
| Video assembly   | `ffmpeg` (free, runs on the Action runner)        |
| Publishing       | YouTube Data API (free quota)                     |
| Secrets          | GitHub Encrypted Secrets (free)                   |
| **LLM tokens**   | **The only paid part** — you bring the API key    |

A premium video model (`replicate`) is also wired in if you ever want higher
quality — it costs money per video and is opt-in per workflow via config.

### Honest expectations
- The system **publishes autonomously** day one. **Revenue is not automatic**:
  YouTube monetization needs ~1,000 subs + 4,000 watch hours (or 10M Shorts
  views/90 days), and "made for kids" videos (COPPA) get no personalized ads =
  lower RPM. Treat reach growth as a multi-month effort; this tool removes the
  manual labor, not the algorithm's patience requirement.
- Free image/TTS quality is good, not Pixar. Swap providers in config anytime.

---

## Architecture (why it is reusable)

```
workflow JSON  ──►  WorkflowRunner  ──►  Steps (pipeline)
                          │                  │
                     Context (data,      build_provider()
                     secrets, telemetry)      │
                                          Registry  ──►  Providers
                                                         llm / tts / image /
                                                         video / publisher
```

- **Registry + decorator pattern** — every provider and step self-registers
  (`@provider("llm","gemini")`, `@step("write_script")`). The loader
  auto-imports them; nothing is hardcoded.
- **Strategy pattern** — providers share one interface; swap them by editing
  JSON, never code.
- **Pipeline pattern** — a workflow is just an ordered list of steps that pass
  data through a shared `Context`.
- **Factory + roles** — `workflow.providers` maps a role (`llm_default`) to a
  concrete provider/model; steps reference the role. Change the model for the
  whole workflow in one place (or from the dashboard UI).

### Repo layout
```
src/core/        engine: registry, context, workflow, config, secrets, telemetry
src/providers/   llm/, tts/, image/, video/, publisher/
src/steps/       research → script → prompts → voice → images → assemble → seo → publish → stats
workflows/       *.json   one file = one workflow (the unit of reuse)
config/          settings.yaml (pricing table, retries — editable)
site/            GitHub Pages dashboard (live stats + config editor)
.github/         scheduled Action
scripts/         youtube_auth.py (one-time token helper)
```

---

## Quick start (local, no keys, no cost)

```bash
cd workflow-studio
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt          # ffmpeg also required: brew install ffmpeg
python -m src.cli validate workflows/kids_video_youtube.json
python -m src.cli run workflows/kids_video_youtube.json --dry-run
python -m src.cli providers               # list everything registered
```

Dry-run produces a real `.mp4` with placeholder images + silent audio and
routes publishing to local files — proving the whole pipeline before you spend
a cent or expose a key.

---

## Deploy (free, autonomous, 3 videos/day)

1. **Create a GitHub repo** and push this folder to it.
2. **Add Secrets** — repo → Settings → Secrets and variables → Actions →
   *New repository secret*. Add only what your chosen providers need:

   | Secret | Needed for |
   |---|---|
   | `GEMINI_API_KEY` | default LLM (and `gemini_image`) |
   | `ANTHROPIC_API_KEY` | if you switch LLM to `claude` |
   | `OPENAI_API_KEY` | if you switch LLM to `openai` |
   | `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` / `YOUTUBE_REFRESH_TOKEN` | YouTube publishing |
   | `REPLICATE_API_TOKEN` | only if you use the premium video provider |

3. **Get the YouTube refresh token** (one-time, local):
   - Google Cloud Console → enable *YouTube Data API v3* → create OAuth client
     (Desktop) → download `client_secret.json`.
   - `pip install google-auth-oauthlib`
   - `python scripts/youtube_auth.py client_secret.json`
   - Copy the three printed values into the GitHub secrets above.
4. **Enable Pages** — Settings → Pages → Source: *GitHub Actions*.
5. Done. The Action runs at 06:00, 12:00, 18:00 UTC (3 videos/day) and you can
   also trigger it manually (Actions → video-workflow → *Run workflow*, with an
   optional dry-run toggle). The dashboard publishes to your Pages URL.

---

## Change anything from config or the UI

- **Swap LLM provider/model**: edit `workflows/kids_video_youtube.json` →
  `providers.llm_default.provider` / `.model`. Same for tts/image/video/publisher.
- **Change the base prompts / style / audience**: edit the `params` of
  `research_trends`, `write_script`, `build_visual_prompts`, `optimize_metadata`.
- **From the dashboard**: open `config.html`, pick a workflow, edit JSON, and
  either Download it (commit to `workflows/`) or paste a fine-grained PAT to
  commit directly. Next scheduled run uses the new config automatically.
- **New workflow, zero code**: drop another `*.json` in `workflows/` (see
  `example_instagram_reel.json`) and point the Action input at it.

## Add a new provider (minimal code, one file)

```python
# src/providers/llm/myprovider.py
from ...core.registry import provider
from .base import LLMProvider, LLMResult

@provider("llm", "myprovider")
class MyProvider(LLMProvider):
    def _complete(self, prompt, system, **kw):
        ...
        return LLMResult(text=text, prompt_tokens=p, completion_tokens=c, model=self.model)
```
It auto-registers — reference `"provider": "myprovider"` in any workflow. Same
pattern for `tts` / `image` / `video` / `publisher` (subclass the base in
`src/providers/media.py`) and for new `@step(...)` types.

---

## Token & cost tracking

Every LLM call is metered (prompt/completion tokens) and priced from the
editable table in `config/settings.yaml`. Per-run and cumulative totals are
written to `state/usage.json` and shown live on the dashboard, broken down by
provider. Video/TTS/image usage is also counted.

## Security model

- Secrets are **only** read from environment variables populated by GitHub
  Encrypted Secrets. They are never written to `state/`, artifacts, or logs.
- Config references secrets as `${NAME}` and resolves them at runtime only.
- Logs and errors are passed through a masker that redacts known secret values.
- The dashboard is static; the optional "commit to repo" feature keeps your PAT
  in the browser and sends it only to `api.github.com`.
- See `SECURITY.md` for the full threat model and hardening checklist.

## Docs
- `SECURITY.md` — secret handling, threat model, hardening.
- `docs/YOUTUBE_REACH.md` — 2026 reach/SEO strategy baked into the pipeline.
- `docs/ADDING_WORKFLOWS.md` — schema reference + recipes.
