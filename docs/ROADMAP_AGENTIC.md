# Agentic + n8n-style roadmap (cost-aware)

<<<<<<< HEAD
This is the strategic plan for evolving Agentry from a config-driven
=======
This is the strategic plan for evolving Workflow Studio from a config-driven
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0
pipeline into a universal, agentic, low-cost automation platform — while staying
honest about what GitHub-only hosting can and cannot do.

## 1. Where we are today (foundation — done)
- Plugin **registry**: providers and steps self-register; nothing hardcoded.
- **Config-driven** workflows (JSON): providers, models, prompts, steps, video
  spec — all editable from the dashboard, no code.
- **Scheduler**: per-workflow cron, dispatcher Action, exactly-once dedupe.
- **Telemetry**: token + cost metering per provider, live on the dashboard.
- **Secrets**: env-only, masked, deploy-time-hashed admin auth, no DB.
- Free except LLM tokens; hosted entirely on GitHub.

This is already a solid "linear pipeline" engine. Agentic = adding a *brain*
that decides *which* tools to run, in what order, reacting to context — instead
of a fixed step list.

## 2. The three layers we are building toward

```
        ┌─────────────────────────────────────────────┐
  L3    │  AGENT  — plans, picks tools, reacts, retries │   (the "brain")
        ├─────────────────────────────────────────────┤
  L2    │  TOOLS  — universal, registered, MCP-style    │   (capabilities)
        ├─────────────────────────────────────────────┤
  L1    │  WORKFLOWS — graph of nodes (n8n-style)        │   (orchestration)
        └─────────────────────────────────────────────┘
```

### L1 — From step-list to node graph (n8n-style)
- Today: `steps: []` runs linearly.
- Target: a **DAG** — each node has `id`, `tool`, `inputs` (referencing other
  nodes' outputs via `{{ nodes.x.out }}`), `when` (conditional edges), and
  fan-out/fan-in (map over a list, e.g. 1 script → N scenes in parallel).
- The runner becomes a topological executor with branch/loop/parallel.
- The studio UI gains a **visual canvas** (draggable nodes, edges) that reads
  and writes the same JSON. n8n-like, but the graph is just config — so it
  still runs on a free GitHub Action.
- *Effort: medium. Cost: $0 (pure engine + UI).* Backward compatible: a linear
  `steps` list is just a straight-line graph.

### L2 — Universal Tool registry (the part you asked for)
Generalize "step" into **Tool**: a typed, self-describing capability the engine
*and* an agent can call. One file = one tool, auto-registered, reusable across
any workflow.

```python
@tool("audio.mix", inputs={"tracks":"list[path]","gains":"list[float]"},
      outputs={"path":"path"}, cost="free")
class AudioMix(Tool):
    def run(self, ctx, tracks, gains): ...
```

- A **tool manifest** (name, description, JSON-schema in/out, cost tier, side
  effects) is emitted to `site/data/tools.json` → the UI lists them and the
  agent can pick them. This is effectively an **MCP-compatible tool surface**;
  external MCP servers can be wrapped as tools too.
- Planned tool packs (all pluggable, no core changes):
  - **audio**: `audio.tts`, `audio.mix` (ducking/sidechain narration over music),
    `audio.normalize` (EBU R128 loudness), `audio.sfx`, `audio.music_select`.
  - **video**: `video.slideshow` (have), `video.broll`, `video.captions_burn`,
    `video.transitions`, premium `video.gen` (Veo/Replicate).
  - **research**: `web.search`, `rss.fetch`, `trends.fetch`, `competitor.scan`.
  - **publish**: youtube (have), `publish.instagram`, `publish.tiktok`,
    `publish.x`, `publish.shorts_thumbnail`.
  - **integrations**: `notify.slack`, `notify.telegram`, `sheets.append`,
    `http.request` (generic webhook = "connect anything").
- *Effort: low per tool (one file). Cost: $0; tools declare a cost tier so the
  agent/engine can prefer free ones.*

#### Audio source + mixing (your specific ask)
Concrete free path, as a tool chain:
`audio.tts` (edge-tts) → `audio.normalize` (ffmpeg loudnorm) →
`audio.mix` (ffmpeg `sidechaincompress` so music ducks under narration) →
`audio.sfx` (optional one-shots from a free CC0 pack in `assets/`).
All ffmpeg, all free, all on the Action runner. Music selection can be an
LLM/heuristic tool picking a track per mood from `assets/music/` metadata.

### L3 — The Agent (the "brain")
Add a `mode: "agent"` workflow type alongside `mode: "pipeline"`:

- **Planner**: given a goal + the tool manifest + current context, an LLM
  produces a plan (which tools, args, order). Plan is validated against tool
  schemas before anything runs (no blind execution).
- **Executor loop**: run tool → observe result → let the model decide next
  step / retry / branch, with a hard **step budget** and **$ budget** ceiling.
- **Memory**: prior runs, what performed well (views/retention from the stats
  the system already collects) feed back into planning → it learns what to make.
- **Guardrails**: allow-list of tools per workflow, dry-run gate, safety prompt
  for kids content, spend cap that aborts cleanly.
- *Effort: medium-high. Cost: controllable — see §3.*

## 3. Cost discipline (how to keep it cheap while agentic)
Agentic loops can burn tokens; these keep it tight:
1. **Model router tool**: cheap model (e.g. Gemini Flash) does drafting/routing;
   escalate to a strong model only for the final creative pass. Configurable in
   the providers block — already swappable.
2. **Prompt caching / dedupe**: hash (prompt+model); reuse identical results
   within a run and across runs (cache in `state/`). Free, big savings on
   retries.
3. **Plan-once, execute-deterministically**: the agent plans *once*; execution
   uses cheap deterministic tools. Avoid "think every step" unless a step fails.
4. **Budget ceilings**: per-run max tokens and max USD in `settings.yaml`;
   telemetry already tracks spend — the runner aborts on breach.
5. **Free-first tool selection**: tools carry a cost tier; planner instructed to
   prefer `free` unless quality gate fails.
6. **Batch + off-peak**: 3/day is tiny; batching research across workflows
   amortizes context tokens.

Estimated: a full agentic kids-Short can stay well under a few cents of tokens
with Flash-tier drafting + caching; premium video is the only thing that would
add real cost, and it stays opt-in per workflow.

## 4. Honest constraints (GitHub-only)
- A static dashboard cannot truly *enforce* auth or run server code. The login
  is a deterrent; the real boundary is the GitHub token + 2FA. A real
  multi-user control plane would need a tiny serverless backend (Cloudflare
  Workers free tier / a private API) — out of scope while "GitHub only".
- GitHub Actions cron granularity is ~ minutes and not guaranteed to the second;
  the 30-min dispatcher with dedupe is the right model. Sub-minute reactivity
  would need an always-on host.
- Long/parallel agent runs must fit Action time limits (6h max/job; we target
  minutes). Fan-out parallelism should stay bounded.
- Heavy GPU video gen cannot run free on the Action — it must be an external
  paid API tool (already the pattern with `replicate`).

## 5. Suggested build order
1. **Tool abstraction + manifest** (formalize step→tool, emit `tools.json`).
2. **Audio tool pack** (tts/normalize/mix/sfx) — immediate quality win, free.
3. **Graph runner + visual canvas** (n8n-style) — backward compatible.
4. **Agent mode** (planner + budgeted executor + guardrails).
5. **Feedback memory** (use collected view/retention stats to guide planning).
6. **Integration tools** (slack/telegram/sheets/http) for "connect anything".

Each phase ships independently, stays free except tokens, and needs no
re-architecture — because L1/L2/L3 all sit on the existing registry.
