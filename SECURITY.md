# Security model

## Where secrets live
All credentials (LLM keys, YouTube OAuth, Replicate token) live in **GitHub
Encrypted Secrets** (repo → Settings → Secrets and variables → Actions).
GitHub encrypts them at rest and only decrypts them into the runner's
environment for your workflow. They are not in the repo, not in the code.

## How the engine handles them
- `src/core/secrets.py` reads secrets **only** from environment variables.
- Workflow JSON never contains a key — it contains `${GEMINI_API_KEY}` style
  references that are resolved at runtime, in memory, just before a provider
  call.
- `state/`, `site/data/`, telemetry, and the published registry contain **no
  secret values** — only token counts, costs, titles, and public video URLs.
- Every error/log line is passed through `SecretResolver.mask()`, which
  replaces any known secret value with `***NAME***` before it is printed, so a
  stack trace cannot leak a key into Action logs.
- Dry-run mode runs with a *lenient* resolver: missing secrets become inert
  placeholders so you can test offline without ever creating real keys.

## Hardening checklist
- [ ] Use a **fine-grained** GitHub PAT (only if you use the dashboard commit
      feature): Contents read/write on this repo only, short expiry.
- [ ] Scope LLM keys to the minimum (separate key per project; set budget caps
      in the provider console).
- [ ] YouTube OAuth client: keep it in *Testing* or limit scopes to
      `youtube.upload` only (the helper already requests just that).
- [ ] Enable branch protection on `main`; the Action commits stats with the
      built-in `GITHUB_TOKEN` (no PAT needed for that).
- [ ] Restrict the `production` environment (Settings → Environments) with
      required reviewers if you want a manual gate before live publishing.
- [ ] Rotate `YOUTUBE_REFRESH_TOKEN` / API keys periodically; revoke instantly
      if a runner log is ever exposed.
- [ ] Keep the repo private if you do not want your config/state public
      (Pages still works on private repos for the owner; for a fully public
      dashboard, keep only `site/` derived data public).

## What an attacker cannot get
- Reading the repo or the Pages site reveals no credentials.
- A failing step cannot print a key (masked).
- The dashboard PAT (optional feature) never touches the server — it is used
  client-side against `api.github.com` over HTTPS and is not persisted.

## Reporting
This is your private automation repo; if you find a logic flaw that could leak
a secret (e.g. a new provider printing `self.options`), fix it by routing the
value through `ctx.secrets` and never logging `self.options` directly.
