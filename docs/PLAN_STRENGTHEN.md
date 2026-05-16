# Plan: make Agentry stronger and more universal

This is the "skills & tools" expansion plan that turns Agentry from a
content-automation engine with one strong pipeline into a **universal
agentic automation platform**. Each item is a one-file plugin on the
existing registry — no rewrites.

## North star
> Every category of automation that n8n / Make / Zapier cover, plus the
> things they don't (agentic planning, video/audio native, cost discipline,
> self-hosted free) — all reachable by writing ONE file per capability.

## 1. Universal primitives (P1.5 — highest leverage)
These are the bricks every workflow rebuilds. Get them right and the whole
ecosystem benefits.

- `http.request` — generic GET/POST/PUT/DELETE with auth header injection,
  exponential backoff, retry-after, **idempotency keys**, JSON body & response.
- `http.webhook` — emit an outbound webhook with HMAC signing.
- `json.transform` — JSONPath / jq-style transforms on ctx data.
- `data.template` — render any string with `{{ }}` over ctx + secrets.
- `data.filter` / `data.map` — first-class list operators on the graph.
- `wait.delay` / `wait.until` — polling with budget.
- `code.eval` — sandboxed expression eval (AST allow-list only, no exec).
- `branch` — explicit conditional fan-out node (`switch` on a value).

## 2. AI skills (turns the engine into an "agent platform")
- `llm.classify` (boolean / category) — cheaper than a full prompt.
- `llm.extract` — structured extraction with JSON schema.
- `llm.summarize`, `llm.translate`, `llm.rewrite`.
- `vision.classify`, `vision.ocr`, `vision.describe`.
- `audio.transcribe` (Whisper API or whisper.cpp local).
- `embedding.create` + `vector.search` (local FAISS-style; chromadb optional).
- `memory.get/set` — persistent cross-run agent memory (state-backed).
- `agent.reflect` — re-plan after a tool failure using error context.
- `model.router` — automatic cheap→strong escalation based on confidence.
- `prompt.cache` — deterministic prompt cache keyed by (model+messages).

## 3. Data sources / sinks
- `rss.fetch` (extend existing), `atom.fetch`.
- `web.scrape` — fetch + CSS/XPath select + cleanup.
- `sheets.read/write` (Google Sheets).
- `airtable.read/write`.
- `notion.read/append`.
- `csv.read/write`, `xlsx.read`.
- `email.fetch` (IMAP), `email.send` (SMTP).
- `s3.put/get`, `r2.put/get`, `gcs.put/get`.
- `gh.repo`, `gh.issue`, `gh.commit` (GitHub API as a tool, not just UI).

## 4. Notify channels
- `notify.slack`, `notify.discord`, `notify.telegram`, `notify.email`.
- `sms.twilio`. The runner can use these on error / budget breach.

## 5. Social/content publishers (productize)
- `publish.instagram` (real, replace stub).
- `publish.tiktok`, `publish.x`, `publish.linkedin`, `publish.reddit`,
  `publish.bluesky`, `publish.threads`, `publish.medium`,
  `publish.wordpress`, `publish.ghost`.
- Each is one file with the same `Publisher.publish()` interface.

## 6. Media expansion (the video-native moat)
- `video.broll` — pull stock from Pexels/Pixabay (both free APIs).
- `video.transitions` — crossfade/zoom between scenes.
- `video.captions.auto` — Whisper-based auto-caption.
- `image.bg_remove` (rembg), `image.upscale` (Real-ESRGAN optional).
- `music.search` — query free CC music libraries.
- `tts.eleven`, `tts.openai`, `tts.azure` — premium voices, all pluggable.

## 7. Analytics feedback loop (the moat)
- `youtube.analytics` — pull retention & CTR per video, store in state.
- `instagram.insights`, `tiktok.analytics`, `x.analytics`.
- `analytics.summarize` — feed past performance into the planner so the
  agent **learns** which titles/hooks/styles convert on YOUR channel.
- This is the one thing n8n/Make cannot do natively. **Build this.**

## 8. Triggers (beyond cron)
- HTTP webhook → triggers a workflow.
- File watcher (drop a file → run a workflow).
- Email-arrived trigger.
- RSS-changed trigger.
- GitHub issue label trigger.

## 9. Workflow primitives (n8n parity)
- `subworkflow` — call another workflow as a node (composition).
- `map_over` — fan out a node across a list, gather results (parallel-bound).
- `branch` / `switch` — first-class conditional edges.
- `try/catch` — error-handler nodes.
- Sticky-notes on the canvas for documentation.

## 10. Production / infra (P3 hardening)
- Pluggable **StateStore** (file / SQLite / Postgres / S3).
- Off-repo **artifact store** (GitHub Releases free / S3 / R2).
- **Bounded parallel** executor in the graph runner.
- **Plugin manifest** versioning + a `tool.compose` to chain tools without
  Python.
- **Plugin marketplace index** (a JSON list of community plugins users can
  install with `agentry plugin add owner/repo`).
- **OpenTelemetry** export for runs (drop-in for Honeycomb/Grafana).

## 11. Developer experience
- `agentry init` scaffolder + `agentry plugin new <kind> <name>` template.
- VS Code extension: JSON schema for workflows, autocompletion of registered
  tools/providers/steps, "run this workflow" command.
- Local dev mode with hot-reload of plugins (`agentry dev`).
- `agentry test <workflow>` runs the workflow with stubbed providers.

## 12. Safety & policy
- `policy.gate` — generic policy engine (any rule), not just kids-content.
- `pii.detect` — strip/flag PII before sending to LLMs.
- `secrets.audit` — verifies a workflow JSON references only declared secrets.
- `cost.cap` per workflow (richer than the global runtime breaker).
- Allow-listed tool sets per workflow (already in agent step; extend).

## Build order (sequenced for maximum impact)
1. **P1.5 — Universal primitives** (`http.request`, `data.transform`, `branch`,
   `wait.*`, `code.eval`). Unblocks ~80% of n8n-style workflows.
2. **P1.6 — Notify pack + sub-workflow + memory tool** (gets agents and
   alerts into every workflow).
3. **Analytics feedback loop** (the moat — start with `youtube.analytics`).
4. **Publisher pack** (instagram/tiktok/x real). Each ships independently.
5. **DX: VS Code + scaffolder** — drives adoption and contributions.
6. **P3 production: state store + off-repo artifacts + bounded parallel.**

## Definition of "stronger product"
- 30+ registered tools across primitives / AI / data / notify / publish.
- Two non-content example workflows shipped (e.g. "new-issue triager",
  "weekly competitor digest").
- Plugin index README + 3 community-style example plugin repos.
- The agent's planner cites the analytics feedback loop to choose actions.
- `pip install agentry` works (publish to PyPI as `agentry`).
- A 90-second video demo of the visual builder wiring a real workflow.

Each item is a one-PR, one-file addition. Nothing in this plan requires
breaking the engine, the dashboard, the visual builder, or the Docker stack.
