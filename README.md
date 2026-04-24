# Agent Skills Board

**Agent Skills Board** is a crawler-first registry and local dashboard for discovering public **Agent Skills**—folders built around `SKILL.md` on GitHub—then indexing them for search, filters, scoring, and detail views (`data/skills.json` + API + static UI).

## Getting started

```bash
export GITHUB_TOKEN=ghp_your_token_here   # https://github.com/settings/tokens
bash run.sh
```

Open **http://localhost:8000**

For why the project exists, scope boundaries, and north-star direction, see **[VISION.md](VISION.md)**.

## Ecosystem

| Resource | Role |
| -------- | ---- |
| **[Agent Skills (spec & docs)](https://github.com/agentskills/agentskills)** | Open format maintained by Anthropic and the community—what a skill *is*. |
| **[agentskills.io](https://agentskills.io)** | Documentation and tutorials for the format. |
| **Agent Skills Board (this repo)** | **Discovery layer**—finds `SKILL.md` in the wild, normalizes metadata, scores signals, and serves API + static UI. |

## What’s in this repository

- **Crawler** — GitHub code search, repo trees, and raw fetches with ETag-friendly caching.
- **Normalizer** — Front matter parsing, role hints, and transparent scoring.
- **Index** — `data/skills.json` (and raw crawl output) as a portable, diffable artifact.
- **API + dashboard** — FastAPI backend and a zero-build-step HTML/CSS/JS UI.

## How it fits together

```
GitHub API (code search + repo tree)
        ↓
  crawler.py          ← finds SKILL.md paths, fetches content
        ↓
  normalizer.py       ← parses frontmatter, scores skills
        ↓
  data/skills.json    ← flat index
        ↓
  api.py              ← search, filter, stats
        ↓
  dashboard/          ← static UI
```

## API usage (summary)

| Phase | Strategy | API calls (order of magnitude) |
| ----- | -------- | ------------------------------ |
| Pinned repos | One tree per repo | ~10 |
| Official orgs | One code search per org | ~20 |
| Broad search | Paginated code search | a few pages |
| Content | `raw.githubusercontent.com` | no REST quota |
| Re-crawl | ETag → `304` saves quota | — |

With `GITHUB_TOKEN`: 5,000 REST requests/hour; a full crawl is typically on the order of **hundreds** of calls. Without a token, stay within unauthenticated limits (for example tune `RATE_LIMIT_DELAY` in `config.py`).

## Scoring (at a glance)

Signals include official-org allowlists, stars (log-scaled), package downloads where available, recency, and light CI/tests heuristics. Weights live in **`config.py`** (`SCORE_WEIGHTS`) so you can tune discovery for your org.

## Repository layout

```
agentskillsboard/
├── config.py           ← org lists, score weights, crawler settings
├── crawler.py
├── normalizer.py
├── api.py
├── run.sh
├── requirements.txt
├── VISION.md           ← intent, scope, roadmap
├── data/
│   ├── raw_skills.json
│   └── skills.json
└── dashboard/static/index.html
```

## Extending the board

Pinned repos, org allowlists, and score weights are the main knobs today. To index **other** capability shapes (for example MCP server directories), treat them as **explicit** schema and scope—see the “federation” notes in `VISION.md` rather than bolting on undocumented scrapers.

---

*Agent Skills Board focuses on **transparent, local-first discovery** for one family of artifacts (`SKILL.md` skills). The [agentskills](https://github.com/agentskills/agentskills) repository defines the portable format those artifacts follow.*
