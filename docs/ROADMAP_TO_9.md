# Plan: from 7.5 to 9.0 commercial

Today's bottlenecks (from `docs/ASSESSMENT.md`): scalability 5.5, security 6.5,
sellable 7.5. To reach 9.0 overall these three rows must each move into the
8.5–9.0 band, and the product must look launch-grade. This is the build plan.

## Phase P3 — Scale & Reliability
**Lifts:** scalability 5.5 → 8.5 · prod-readiness 7.5 → 9.0
1. **Pluggable `StateStore`** interface (`file` default, `sqlite`, `s3`/`r2`).
   Engine never hard-depends on `git push` to persist run state.
2. **Off-repo artifact store**: `assets://` URI scheme; default GitHub
   *Releases* (free), pluggable S3/R2/B2 for scale. Stops git media bloat.
3. **Provider resilience**: shared HTTP client with exponential backoff +
   jitter, 429/5xx aware, retry-after honored, idempotency keys for YouTube,
   resumable-resume on partial upload.
4. **Parallel graph fan-out**: bounded worker pool executes independent
   branches concurrently while respecting `needs`. Budget breaker still per
   step. Big wins for n8n-style DAGs.
5. **Observability**: structured JSON logs, optional OTLP tracing,
   `state/errors.json` ring-buffer fed into the dashboard.
6. **`notify` tool pack**: Slack/Discord/Telegram/email — single tool the
   runner can call on error/budget-abort.

## Phase P4 — Security & Compliance
**Lifts:** security 6.5 → 8.5
1. **Real auth path** alongside the static one: a Cloudflare Workers free-tier
   serverless auth recipe (script + docs), GitHub OAuth login for the dashboard
   editor. Keeps zero-cost option; adds production-grade option.
2. **Supply chain**: Dependabot, `pip-audit` in CI, **SBOM** (CycloneDX) as a
   release artifact, gitleaks pre-commit + CI scan.
3. **Disclosure**: tighten `SECURITY.md` with contact/PGP, response SLA, scope.
4. **Per-workflow scoped credentials**: multiple YouTube/IG accounts, isolated
   secret namespaces per workflow.
5. **Audit log**: signed JSON line per run committed to `state/audit/` for
   tamper-evident history.

## Phase P5 — Quality depth
**Lifts:** code 8.0 → 9.0 · prod-readiness +0.5
1. **Coverage gate** in CI (target 80%); coverage badge on README.
2. **Provider integration tests** using `responses`/`pytest-httpx` mocks for
   LLM/YouTube/Replicate — verifies real API contracts without spending.
3. **Nightly real-API smoke** (separate workflow, against a sandbox channel) —
   detects upstream breakage early.
4. **Type hints + mypy --strict** for core, ruff lint gate.
5. **Pre-commit** hooks (ruff/black-equivalent/mypy) — clean PRs.
6. **Docs site** (mkdocs-material) served on the same Pages domain — Quickstart,
   Workflows, Tools, Agent, Graph, Selling.

## Phase P6 — Launch polish (the visible part buyers see)
**Lifts:** sellable 7.5 → 9.0
1. **Hero README**: 1-line wedge, 90-sec demo GIF, screenshots (dashboard,
   Studio, Visual Builder), badges (CI, license, stars, version, coverage).
2. **Feature matrix** vs n8n/Make/Zapier highlighting where this wins:
   *config-driven · free self-hosted · agentic native · video/audio native ·
   one-file plugin model*.
3. **Live demo**: your deployed Pages dashboard URL on the README + a public
   `demo` workflow with safe stub output.
4. **Niche template gallery**: 4–6 polished workflows beyond kids-videos
   (e.g., AI tech-news Shorts, podcast-clip auto-publisher, newsletter→IG card,
   weekly trend digest). Lifts universality story; sidesteps COPPA optics.
5. **Three example *plugins* published as separate repos** (one provider, one
   tool, one publisher) — proves the ecosystem story.
6. **Open-core split**: keep this repo MIT for stars; a private "Pro" repo for
   paid (premium publishers, richer React canvas, priority support).
7. **Launch sequence**: Show HN, r/selfhosted, Product Hunt, X — single
   coordinated drop with the demo link.

## Phase P7 — The moat (do at least one)
**Lifts:** sellable to a defensible 9.0+
1. **YouTube/IG analytics feedback loop**: ingest retention/CTR per past
   video, feed into the planner so the agent learns what reach-tactics actually
   worked *on your channel*. n8n/Make do not do this. **Strongest wedge.**
2. **Cost-router tool**: deterministic cheap-first model routing (draft on
   Flash, finalize on Sonnet/Opus) + cross-run prompt cache. Genuine cost-
   aware agentic — rare in the market.
3. **One-click niche packs**: each pack = pre-tuned workflow + prompts +
   safety policy. Sell as the Pro tier inventory.

## Effort & ordering
Each phase is independently shippable. Suggested order: **P3 → P5 → P4 →
P6 → P7**. Reason: P3 unlocks real-world reliability that P6 buyers will
test; P5 keeps you fast as the surface grows; P4 is needed before you
seriously charge; P6 is the launch; P7 is the moat earned in production.

## Definition of done (9.0)
- Coverage ≥ 80% green in CI; mypy strict clean.
- A graph workflow with parallel fan-out runs reliably with bounded
  concurrency on free GitHub Actions.
- State + artifacts survive a wipe of the repo (off-repo store works).
- 1-click GitHub OAuth login on the dashboard editor.
- README with demo GIF + screenshots + live demo URL + feature matrix.
- Open-core split announced; first 3 example plugin repos live.
- One P7 differentiator shipped (analytics loop or cost router).
