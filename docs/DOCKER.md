# Docker — self-host the two apps

Agentry runs as a tiny two-service Compose stack on any host:

| Service  | What it does                                | Port |
|----------|---------------------------------------------|------|
| `web`    | Serves the dashboard, Studio, Visual Builder | 8000 |
| `worker` | Scheduler dispatcher loop (runs due workflows) | —    |

Both use the **same image**; only the command differs, so the image stays
lean and there's nothing duplicated. They share two host folders:

- `./state` — cumulative run/usage/published stats (the engine writes here)
- `./site/data` — what the dashboard reads (synced by the engine)

## 1. Configure
```bash
cp .env.example .env
$EDITOR .env            # paste your real keys
```
Required at minimum: `GEMINI_API_KEY` (plus YouTube secrets if you publish).
`ADMIN_USERNAME/PASSWORD` are optional — set them to lock the Studio editor.

## 2. Build & run
```bash
docker compose build
docker compose up -d
```

- Dashboard → http://localhost:8000
- Agentry → http://localhost:8000/studio.html
- Visual Builder → http://localhost:8000/graph.html
- Get Started → http://localhost:8000/start.html

## 3. Common commands
```bash
docker compose ps                       # status
docker compose logs -f worker           # tail scheduler logs
docker compose logs -f web              # tail web logs
docker compose restart worker           # reload after editing config/
docker compose exec worker python -m agentry.cli doctor
docker compose exec worker python -m agentry.cli run workflows/kids_video_youtube.json --dry-run
docker compose down                     # stop everything (data persists on host)
```

## 4. Trigger a workflow manually (any time)
```bash
docker compose exec worker \
  python -m agentry.cli run workflows/kids_video_youtube.json
```

## 5. Change the tick interval
By default the worker calls the scheduler every **1800s (30 min)**.
Override via `.env`: `WFS_TICK_SECONDS=600`.

## 6. Production hardening checklist
- Put a reverse proxy (Caddy/nginx/Traefik) in front for **TLS** and to
  restrict access to `/studio.html` / `/graph.html`.
- Mount `./state` and `./site/data` to a backed-up host path.
- Run on a small VPS, a Raspberry Pi, or any container host — the image has
  no GPU or DB requirements.
- Rotate `.env` regularly and never commit it (already in `.gitignore` and
  `.dockerignore`).

## 7. Image details
- Base: `python:3.12-slim`
- System: `ffmpeg`, `libass9`, `ca-certificates`, `curl`
- Python deps: `requirements.txt` only (lean)
- Final size: ~250 MB
- No secrets baked in: `.env` is mounted at runtime via `env_file`.

## 8. One-container alternative (no Compose)
If you don't want Compose, run web and worker as two `docker run` commands
from the same image:
```bash
docker build -t agentry .
docker run -d --name wfs-web -p 8000:8000 \
  -v "$PWD/state:/app/state" -v "$PWD/site/data:/app/site/data" \
  agentry

docker run -d --name wfs-worker --env-file .env \
  -v "$PWD/state:/app/state" -v "$PWD/site/data:/app/site/data" \
  -v "$PWD/runs:/app/runs" agentry \
  sh -c 'while true; do python -m agentry.cli scheduler --window 35; sleep 1800; done'
```
