# Changelog

<<<<<<< HEAD
All notable changes to Agentry.
=======
All notable changes to Workflow Studio.
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0

## [0.5.0] - 2026-05-16
### Added (P2 — n8n-style universal builder)
- DAG **graph runner**: workflows may use `nodes` (with `id`, `needs`, `when`)
  instead of (or alongside) linear `steps`. Topological order, cycle detection,
  conditional edges. Fully backward-compatible with existing pipelines.
- **Visual workflow builder** (`site/graph.html`): zero-build SVG canvas with
  drag, connect, branch, inspector, and "save to GitHub" — exports the graph
  JSON the engine runs natively.
- `workflows/example_graph.json` demonstrating the same kids pipeline as a DAG.
- Tests for topo order, cycle detection, conditional skip, backward compat.

## [0.4.0] - 2026-05-16
### Added (P1 — agentic core)
- **Tool abstraction** (`@tool`) + registry namespace + `tools.json` manifest.
- **Free audio tool pack**: `audio.silence`, `audio.normalize` (EBU R128),
  `audio.concat`, `audio.mix` (sidechain ducking — music auto-dips under speech).
- **`agent` step**: LLM planner -> budgeted executor with guardrails
  (allow-list, max-steps, per-tool budget breaker, dry-run safe, secrets masked).
- Tests for tool manifest, agent planning/execution, disallowed-tool rejection.

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
<<<<<<< HEAD
- Redesigned professional dashboard + Agentry editor.
=======
- Redesigned professional dashboard + Workflow Studio editor.
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0
- Agentic + n8n-style architecture roadmap; honest product assessment.

## [0.1.0] - 2026-05-16
### Added
- Config-driven workflow engine: registry, factory, pipeline, context.
- LLM (Gemini/Claude/OpenAI), TTS, image, video, publisher providers.
- ffmpeg video assembly (verified producing valid MP4), YouTube publisher.
- GitHub Actions hosting, Pages dashboard, telemetry/cost tracking.
