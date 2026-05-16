# YouTube reach strategy (2026), baked into the pipeline

These tactics are encoded directly in the workflow steps so every video ships
optimized. Tune them in `workflows/*.json` `params` — no code needed.

## What the algorithm rewards (Shorts, 2026)
- **Watch-through / replay rate**, not click-through. If viewers replay
  (~1.5×), the system treats it as "extraordinary value" and expands reach.
- **The first 2–5 seconds decide distribution.** A weak open is fatal.
- **Consistency > frequency**, but daily quality posting accelerates growth.
  This system posts 3×/day.
- Shorts surface in **YouTube and Google search**, so SEO still matters.

## How the pipeline applies it
| Tactic | Where it is enforced |
|---|---|
| Strong hook in first lines | `write_script` prompt (hook-first script) |
| Primary keyword in first **40 chars** of title | `optimize_metadata` prompt |
| Title < 70 chars, ≤1 emoji, no fake clickbait | `optimize_metadata` prompt |
| **3–5 niche hashtags + `#Shorts`**, never >5 | `optimize_metadata` prompt |
| Keyword-rich description + first 3 hashtags shown above title | `optimize_metadata` |
| ≤15 lowercase search tags | `optimize_metadata` `max_tags` param |
| Short runtime, high completion | `video.max_duration_sec` (60), tight scenes |
| Safe + COPPA correct | `made_for_kids: true` in publisher options |
| 3 posts/day cadence | Action cron `06/12/18 UTC` |

## Levers you can tune in config
- `research_trends.params.theme` / `.audience` — niche focus (a tight niche
  trains the algorithm faster than random topics).
- `write_script.params.scene_count` / `words_target` — pacing; keep Shorts
  punchy (≤140 words for ~45–55s).
- `optimize_metadata.params.keyword_seed` — seed your niche's search terms.
- `build_visual_prompts.params.style` — a **consistent** visual identity
  improves channel recognition and retention.
- `video.max_duration_sec` — sub-30s maximizes completion rate; 50–60s
  maximizes total view time. A/B by cloning the workflow JSON.

## Beyond automation (manual, optional, high-leverage)
- Add a custom channel banner + recognizable thumbnail style.
- Reply to early comments fast (engagement signal).
- Cluster content into series/playlists so binge sessions lift session time.
- Don't expect monetization before community + watch-time thresholds; focus
  the first months purely on retention and consistency.

## Sources
- [YouTube Shorts Best Practices 2026 — JoinBrands](https://joinbrands.com/blog/youtube-shorts-best-practices/)
- [How to Optimise YouTube Shorts for SEO 2026 — CRKLR](https://crklr.com/news/how-to-optimise-youtube-shorts-for-seo/)
- [YouTube Shorts Hashtags 2026 — Hashtag Tools](https://hashtagtools.io/blog/youtube-shorts-hashtags-title-vs-description-2026)
- [How to Optimize YouTube Shorts for SEO: 2026 Blueprint — 12AM Agency](https://12amagency.com/blog/how-to-optimize-youtube-shorts-for-seo/)
- [From Zero to Viral: Hashtag Formula — Minvo](https://minvo.pro/blog/from-zero-to-viral-the-hashtag-formula-for-youtube-shorts)
