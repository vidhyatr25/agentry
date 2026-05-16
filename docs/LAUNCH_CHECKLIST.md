# Launch checklist — copy / paste / click

Everything below is on `https://github.com/vidhyatr25/agentry` and only
you can set it (GitHub doesn't expose these via a token-less API).
Do these in order — total time ~15 minutes — and the repo is launch-grade.

## 1) Set the repository **description** (one-liner under the repo name)

> Repo home → **gear ⚙ icon next to "About"** → Description.

Paste this (350-char max; this is ~210):

```
Config-driven agentic workflow engine with an n8n-style visual builder. Self-hosted free on GitHub Actions + Pages. Bring an LLM key, ship videos/posts on autopilot. Plugin-based: add a provider, tool or workflow in one file.
```

## 2) Set the **Website** field (same About dialog)

After you enable Pages (step 5), paste:

```
https://vidhyatr25.github.io/agentry/
```

(or your custom domain). Until then leave it empty — adding a 404 hurts.

## 3) Add **Topics** (drives GitHub discovery & "suggestions" feed)

Same About dialog → **Topics**. Paste these (GitHub allows up to 20):

```
agent
agents
agentic
agentic-ai
ai
ai-agents
automation
workflow
workflow-automation
llm
llm-agent
gemini
openai
anthropic-claude
n8n
n8n-alternative
self-hosted
low-code
no-code
python
```

Bonus list of strong runners-up — swap one in if a topic above feels off:
`github-actions`, `video-generation`, `youtube`, `youtube-automation`,
`content-automation`, `text-to-video`, `mcp`, `langchain-alternative`.

## 4) Upload the **social preview image** (huge for HN / X / LinkedIn previews)

A pre-made 1280×640 image is at
[`site/assets/shots/social-preview.svg`](../site/assets/shots/social-preview.svg).
GitHub wants PNG, so convert once:

```bash
# Option A: rsvg-convert (brew install librsvg)
rsvg-convert -w 1280 -h 640 site/assets/shots/social-preview.svg \
  -o site/assets/shots/social-preview.png

# Option B: open the SVG in any browser, screenshot at 1280×640, save as PNG.
```

Upload via: Repo → **Settings → General → Social preview → Upload an image**.

## 5) Enable **Pages**

Repo → **Settings → Pages → Source: GitHub Actions**. After the next CI run,
your dashboard is live at `https://vidhyatr25.github.io/agentry/`. Pop that
back into the About → Website (step 2).

## 6) Enable **Discussions** (community signal stars are correlated with)

Repo → **Settings → Features → Discussions** → ✅ on.

## 7) **Pin** the repo to your GitHub profile

Profile page → **Customize your pins** → tick `agentry`.

## 8) Create the first **Release** (showcases tags / version / changelog)

Repo → **Releases → Draft a new release**:
- Tag: `v0.1.0`
- Title: `v0.1.0 — Initial public release`
- Body: paste highlights from `CHANGELOG.md`.

## 9) Open 5–8 **"good first issue"** tickets

Pulls contributors. Examples (each is ~30 min):
- "Add `notify.slack` tool"
- "Add `notify.discord` tool"
- "Add `tts.openai` provider"
- "Add `publish.bluesky` publisher"
- "Add a `rss.fetch` reusable step"
- "Niche workflow JSON: weekly competitor digest"
- "Niche workflow JSON: podcast clip auto-publisher"

For each: open an issue, paste the description, apply labels
**`good first issue`** + **`help wanted`**.

## 10) Launch sequence (one focused week)

Plan in [docs/STAR_GROWTH.md](STAR_GROWTH.md) — TL;DR:

- **Day 1**: r/selfhosted post (lead with the visual builder screenshot + live demo URL)
- **Day 2 morning ET**: Show HN
- **Day 3**: Product Hunt
- **Day 4**: X / LinkedIn thread with the social-preview image
- **Day 5+**: niche subs (r/youtubers, r/ChatGPTCoding, r/n8n, r/Python)
- **Day 7**: blog post — "I built a free, agentic n8n on GitHub"

## Done = launch-grade

After these steps:
- ✅ Sharp 1-line description that says exactly what it is and the keywords
- ✅ Real GitHub topics → appears in Explore / topic feeds / "suggestions"
- ✅ Working live demo linked
- ✅ Social preview that doesn't look like a default GitHub icon
- ✅ Discussions on (alive-project signal)
- ✅ Pinned on your profile
- ✅ First tagged release
- ✅ Welcoming "good first issue" backlog

Then post to the launch channels. Reply to every comment in the first 4 hours.
