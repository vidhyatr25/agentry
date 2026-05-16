# Star growth playbook (honest, proven tactics)

Stars on GitHub are a function of **(1) being genuinely useful, (2) being
findable, (3) reducing friction to value**. Nothing else moves the needle long
term. Below is a concrete plan in order of leverage.

## Before you announce anything — make the repo deserve clicks
1. **GitHub Topics** on the repo page: `automation`, `ai`, `agent`, `youtube`,
   `workflow`, `n8n`, `agentic`, `low-code`, `self-hosted`, `video-generation`,
   `python`. These power discoverability and the "Explore" page.
2. **Repo description** (the one-liner under the name): copy the README hook.
3. **Social preview image** (Settings → Social preview): use a 1280×640 PNG of
   the dashboard or builder. Without this, link previews look like the default
   GitHub logo — kills clickthrough.
4. **Pinned repo** on your GitHub profile.
5. **Enable Discussions** (Settings → Features). Stars + Discussions signal an
   alive project.
6. **One real live demo URL** in the README (your Pages dashboard) — the single
   most converting element.
7. **A 30–60s screen recording** committed as a GIF or hosted on YouTube,
   embedded in the README. Demos convert better than features lists.

## Launch sequence (one coordinated week)
- **Day 0:** Repo polish done (above). Tag `v0.5.0`, write a clean GitHub
  Release with the changelog highlights.
- **Day 1 — r/selfhosted** post: title "I built a free, self-hosted, agentic
  content-automation engine that runs on GitHub Actions". Lead with the live
  demo URL and the visual builder screenshot. Be candid about scope.
<<<<<<< HEAD
- **Day 2 — Hacker News (Show HN)**: title "Show HN: Agentry – n8n-style
=======
- **Day 2 — Hacker News (Show HN)**: title "Show HN: Workflow Studio – n8n-style
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0
  agentic engine that runs free on GitHub". Post in the morning ET. Reply to
  every comment in the first 4 hours; the engagement bump matters.
- **Day 3 — Product Hunt**: schedule for a Tuesday/Wednesday launch.
- **Day 4 — X / LinkedIn**: short threads with the GIF, tagging adjacent
  builders.
- **Day 5+ — niche subs**: r/youtubers, r/PassiveIncome (carefully — no income
  claims), r/ChatGPTCoding, r/n8n, r/Python.
- **Day 7 — write a blog post**: "How I built an agentic n8n on GitHub for
  zero $/month" — link from README; this becomes evergreen SEO.

## What to put in the README (you have most of these — keep them)
- 1-line wedge at the very top.
- Badges (CI, tests, license, hosted-on-GitHub, cost).
- Screenshots/GIF *immediately* (now done with committed SVG mockups; replace
  with real PNGs from your live deploy).
- Honest comparison table vs n8n/Make/Zapier (already in place).
- 60-second quickstart that runs without keys (already wired via `--dry-run`).
- Plugin "add a provider in one file" example (present).
- "Built by Y; sponsor / contribute" footer with a clear ask.

## Friction killers (each one is worth ~10% of stars)
- `pip install` works out of the box (yes).
- A `--dry-run` path that produces real output without keys (yes — leans into
  trust).
- A `doctor` preflight command (yes).
- One-command deploy guide (`DEPLOY.md` — yes; mirror the steps on the static
  `site/start.html`).
- A live demo dashboard URL (you must deploy and add it).

## Community loop (compounds over months)
1. **Reply within 24h** to every issue and PR for the first 3 months. Stars
   correlate with maintainer responsiveness, visible in the issue tracker.
2. **"Good first issue"** labels on ~10 tiny tasks (doc fix, new provider,
   new tool). First-time contributors return as evangelists.
3. **Examples directory** — every accepted niche workflow becomes a "Featured
   workflow" with credit + a backlink to the contributor.
4. **Plugin ecosystem** — publish three example plugin repos (one provider,
   one tool, one publisher) under your account. Each pulls clicks back to the
   core.
5. **Monthly devlog** as GitHub Releases + blog. Compounds.

## What *not* to do
- Don't beg for stars. It works once; the second time it sours.
- Don't fake content (auto-generated kids slop on YouTube is a brand risk
  even though the engine supports it). Showcase polished, non-kids examples.
- Don't ship without a demo URL. The README will read like vapor without it.
- Don't oversell income — the LICENSE already disclaims; behave accordingly.

## Quick targets
- Week 1 after launch: 100 stars (achievable with a HN front page and a tight
  demo).
- Month 1: 500 stars and 5 external contributors via "good first issues".
- Month 3: 1.5–3k stars if a niche template lands viral on X/LinkedIn.

Stars are a *result*, not a tactic. The leading indicators are: live demo URL,
demo GIF, response time on issues, and at least one niche people *forward*
the link for.
