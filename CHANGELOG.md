# Changelog

All notable changes to Workflow Studio.

## [0.3.0] - 2026-05-16
### Added
- Runtime budget circuit-breaker (`budget.max_cost_usd` / `max_tokens`) — runs
  abort cleanly with status `aborted_budget` instead of overspending.
- `safety_gate` step: free keyword policy + optional LLM child-safety review;
  blocks unsafe content before publishing.
- pytest suite (engine, registry, prompt, scheduler, secrets, telemetry,
  budget breaker) and a CI workflow running tests + an end-to-end dry-run.
- MIT LICENSE, CHANGELOG, selling guidance.

## [0.2.0] - 2026-05-16
### Added
- All LLM prompts externalized into workflow JSON (editable from the UI).
- Schedule registry + 30-min dispatcher Action with exactly-once dedupe.
- Deploy-time admin auth (PBKDF2 from GitHub Secrets, no plaintext).
- Redesigned professional dashboard + Workflow Studio editor.
- Agentic + n8n-style architecture roadmap; honest product assessment.

## [0.1.0] - 2026-05-16
### Added
- Config-driven workflow engine: registry, factory, pipeline, context.
- LLM (Gemini/Claude/OpenAI), TTS, image, video, publisher providers.
- ffmpeg video assembly (verified producing valid MP4), YouTube publisher.
- GitHub Actions hosting, Pages dashboard, telemetry/cost tracking.
