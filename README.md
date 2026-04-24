# Agent Skills Board — Agent Skill Registry

**Agent Skills Board** is the product name for this repository (clone path is often `agentskillsboard/`).

A crawler-first registry for SKILL.md files across GitHub.
No registration required — the crawler finds skills automatically.

## Quick Start

```bash
export GITHUB_TOKEN=ghp_your_token_here   # get from github.com/settings/tokens
bash run.sh
```

Open http://localhost:8000

## Architecture

```
GitHub API (code search + repo tree)
        ↓
  crawler.py          ← finds SKILL.md files, fetches content
        ↓
  normalizer.py       ← parses frontmatter, scores skills
        ↓
  data/skills.json    ← TinyDB flat file store
        ↓
  api.py              ← FastAPI: search, filter, stats
        ↓
  dashboard/          ← HTML/CSS/JS UI, zero build step
```

## API rate limit strategy (minimum hits)

| Phase | Strategy | API calls |
|-------|----------|-----------|
| Pinned repos | 1 tree call/repo = all SKILL.md paths | ~10 |
| Official orgs | 1 code search/org | ~20 |
| Broad search | paginated code search, 100 results/page | ~5 pages |
| Content fetch | raw.githubusercontent.com (NO API quota) | unlimited |
| ETag cache | 304 = 0 quota used on re-crawl | — |

With GITHUB_TOKEN: 5,000 requests/hour. Full crawl uses ~200-400 calls.
Without token: 60/hour — use `RATE_LIMIT_DELAY = 2.0` in config.py.

## Scoring formula

| Signal | Weight | Notes |
|--------|--------|-------|
| Official org | 35 | org in OFFICIAL_ORGS list |
| Stars | 25 | log10-normalised, cap 1000+ |
| Downloads | 15 | PyPI/npm if available |
| Recency | 15 | exp decay, half-life 90 days |
| Has CI | 5 | .github/workflows present |
| Has tests | 5 | inferred from tags/description |

## 2-Day Build Plan

### Day 1 — Data pipeline
- [ ] Set GITHUB_TOKEN
- [ ] Run `python3 crawler.py` → watch logs, check data/raw_skills.json
- [ ] Run `python3 normalizer.py` → check top 10 output
- [ ] Add any missing orgs to OFFICIAL_ORGS in config.py
- [ ] Add any pinned repos to PINNED_REPOS in config.py

### Day 2 — Dashboard + polish
- [ ] Run `bash run.sh` → open http://localhost:8000
- [ ] Verify search, filter, sort all work
- [ ] Click a skill card → verify detail panel
- [ ] Click "Re-crawl" → verify background crawl starts
- [ ] Tune SCORE_WEIGHTS in config.py if scoring feels off

## Extend: add MCP servers

To also index MCP servers from pulsemcp.com:

```python
# In crawler.py, add after Phase 3:
async def crawl_pulsemcp(client):
    r = await client.get("https://www.pulsemcp.com/api/servers")
    for server in r.json()["servers"]:
        yield {
            "name": server["name"],
            "format": "MCP server",
            "org": server.get("author",""),
            ...
        }
```

## File structure

```
agentskillsboard/
├── config.py           ← all org lists, score weights, settings
├── crawler.py          ← GitHub crawler (async, ETag-cached)
├── normalizer.py       ← scoring + role detection
├── api.py              ← FastAPI server
├── run.sh              ← one-command start
├── requirements.txt
├── data/
│   ├── raw_skills.json ← crawler output
│   └── skills.json     ← normalised, scored, sorted
└── dashboard/
    └── static/
        └── index.html  ← full UI, zero build step
```
