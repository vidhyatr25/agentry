# Adding workflows & providers

## A workflow is one JSON file
Drop it in `workflows/`. No code. Schema:

```jsonc
{
  "name": "unique_name",
  "description": "human summary",
  "schedule": "cron (documentation only; real cron is in .github/workflows/run.yml)",
  "video": {
    "format": "shorts|reel|long",
    "aspect_ratio": "9:16",
    "resolution": [1080, 1920],
    "fps": 30,
    "max_duration_sec": 60
  },
  "providers": {
    "<role>": { "kind": "llm|tts|image|video|publisher",
                "provider": "<registered name>",
                "model": "<optional>",
                "options": { "api_key": "${SECRET_NAME}", "...": "..." } }
  },
  "steps": [
    { "type": "<registered step>", "params": { "<role refs and tuning>": "..." } }
  ],
  "settings": { "optional per-workflow overrides of config/settings.yaml" }
}
```

### Rules
- `providers.<role>` is referenced by steps via that role name
  (`"llm": "llm_default"`). Change the model once, everywhere updates.
- Secrets are always `${UPPER_SNAKE}` and must exist as GitHub Secrets.
- Params support templating: `{{ data.key }}` injects a previous step's output;
  `${SECRET}` injects a secret.
- Validate before committing: `python -m agentry.cli validate workflows/yours.json`.

## Built-in steps (the reusable library)
`research_trends` → `pick_subject` → `write_script` → `build_visual_prompts`
→ `synthesize_voice` → `generate_images` → `assemble_video`
→ `optimize_metadata` → `publish` → `record_stats`

Reorder, drop, or repeat them freely. Each reads/writes the shared context
(`topics`, `subject`, `scenes`, `audio_path`, `video_path`, `metadata`,
`published`).

## Registered providers
- llm: `gemini`, `claude`, `openai`
- tts: `edge_tts` (free), `gtts` (free)
- image: `pollinations` (free), `gemini_image`
- video: `ffmpeg_slideshow` (free), `replicate` (premium, paid)
- publisher: `local` (safe default), `youtube`, `instagram`/`facebook`/`tiktok`
  (registered stubs — implement when you build those workflows)

`python -m agentry.cli providers` prints the live catalog (also at
`site/data/providers.json` for the dashboard).

## Add a new step
```python
# src/steps/my_step.py
from ..core.registry import step
from ..core.step import Step

@step("my_step")
class MyStep(Step):
    def run(self, ctx):
        value = self.param(ctx, "some_param", "default")
        ctx.set("my_output", value)
```
Auto-registered on import. Reference `{ "type": "my_step", "params": {...} }`.

## Add a new platform publisher
Implement `publish()` on a `Publisher` subclass (see
`src/providers/publisher/youtube.py`), register with
`@provider("publisher", "instagram")`, swap the stub. The kids workflow becomes
an Instagram workflow by changing one provider block — that is the whole point
of the design.

## Multiple daily workflows
The Action's `workflow_dispatch` takes a `workflow_file` input. To run several
on schedule, add more cron-triggered jobs or a matrix in
`.github/workflows/run.yml`, each pointing at a different JSON.
