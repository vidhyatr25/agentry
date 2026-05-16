# Deploy to GitHub (free hosting) — 6 steps

This runs entirely on GitHub: **Actions** schedules and produces the videos,
**Pages** hosts the live dashboard, **Encrypted Secrets** hold credentials.
No server, no paid host. Only LLM tokens cost money.

## 0. One-time: get the YouTube refresh token (local, ~5 min)
```bash
<<<<<<< HEAD
cd agentry
=======
cd workflow-studio
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-auth.txt
```
- Google Cloud Console → enable **YouTube Data API v3**
- Create **OAuth client → Desktop app** → download `client_secret.json`
- ```bash
  python scripts/youtube_auth.py client_secret.json
  ```
- It prints `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.
  Keep them for step 3. Delete `client_secret.json` afterwards.

## 1. Push this folder to a new GitHub repo
The repo is already initialized and committed. Create an empty repo on
github.com (no README), then:
```bash
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

## 2. Verify it's deployment-ready
```bash
<<<<<<< HEAD
python -m agentry.cli doctor
=======
python -m src.cli doctor
>>>>>>> 4f66566cb65003080ea71b565cf90c174c7c1ad0
```
Secrets/ffmpeg showing FAIL **locally is fine** — they are provided by GitHub.
The check that matters here is `workflow valid`.

## 3. Add Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add only what your configured providers use:

| Secret | Required? |
|---|---|
| `GEMINI_API_KEY` | Yes (default LLM) |
| `YOUTUBE_CLIENT_ID` | Yes (publishing) |
| `YOUTUBE_CLIENT_SECRET` | Yes |
| `YOUTUBE_REFRESH_TOKEN` | Yes |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Only if you switch LLM in config |
| `REPLICATE_API_TOKEN` | Only if you use premium video |

## 4. Enable the dashboard
Repo → **Settings → Pages → Source: GitHub Actions**.

## 5. First run = dry-run (safe, free, no upload)
Repo → **Actions → video-workflow → Run workflow** → set **dry_run = true**.
Confirm it goes green and the dashboard URL renders. This proves the full
pipeline (incl. ffmpeg video assembly) without spending tokens or uploading.

## 6. Go live
- Run it once with **dry_run = false**. The video uploads to YouTube as
  **`unlisted`** (the safe default in `workflows/kids_video_youtube.json`).
- Check the video on your channel. Once you've confirmed one good upload and
  your YouTube app/channel is in order, change `providers.publisher_default.
  options.privacy` from `"unlisted"` to `"public"` (edit the JSON directly or
  via the dashboard **Workflows & Config** page) and commit.
- From then on it runs automatically at **06:00 / 12:00 / 18:00 UTC** = 3
  videos/day, fully autonomous. Stats/tokens/cost update live on the dashboard.

---

### Why unlisted first (don't skip)
YouTube forces uploads from unverified API projects to private/unlisted anyway,
and a brand-new channel auto-posting public AI kids content risks strikes
before you've reviewed a single output. Verify one upload, then flip to public.

### Notes
- Cadence/cron lives in `.github/workflows/run.yml` (not the JSON). Change it
  there if you want a different schedule.
- `state/` is committed back by the Action each run so stats accumulate across
  runs — do not add it to `.gitignore`.
- If `main` is branch-protected, allow the `github-actions[bot]` to push, or
  the "Persist stats" step will fail (videos still upload).
- Switch any provider/model from the dashboard or by editing the workflow
  JSON; the next scheduled run picks it up. See `docs/ADDING_WORKFLOWS.md`.
