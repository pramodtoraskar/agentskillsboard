# Task list — AgentSkillsBoard (from `Claude.pdf`)

**Source:** `requirements/Claude.pdf` — *AgentSkillsBoard — Master Coding Agent Prompt* (v1.0).  
**Execution:** Complete phases in order; satisfy **all** acceptance criteria in a section before starting the next.

---

## Verification — run tests before marking work complete

**Rule:** Do not mark a phase (or a task row that changes code) **done** until the **commands for that phase** below exit **0**. If a phase has no dedicated test file yet, add the smallest pytest that locks the behavior you just implemented, then run the suite again.

| When you finish… | Run (must all pass) | Also run (regression) |
|-------------------|---------------------|------------------------|
| **Phase 1** (`config.py`) | `python3 -c "import config"` and every **AC-1.x** check | `pytest tests/ -q` if `tests/` exists (expect green; fix skips only with a documented reason) |
| **Phase 2** (`crawler.py`) | `pytest tests/test_crawler.py -v` | `pytest tests/ -q` |
| **Phase 3** (`normalizer.py`) | `pytest tests/test_normalizer.py -v` | `pytest tests/ -q` |
| **Phase 4** (`api.py`) | `pytest tests/test_api.py -v` | `pytest tests/ -q` |
| **Phase 5** (dashboard) | **AC-5.x** manual checklist in browser + **no console errors** | `pytest tests/ -q` (API contract must stay stable for the UI) |
| **Phase 6** (tests / coverage) | `pytest tests/ -v` (all tests) + coverage per **AC-6.3** | — |
| **Phase 7** (`run.sh`, deps) | `bash -n run.sh`; smoke: `python3 -c "import api, crawler, normalizer, config"` | `pytest tests/ -q` |
| **End-to-end (§7)** | **AC-7.x** against a real `GITHUB_TOKEN` on a branch machine | `pytest tests/ -q` first so unit tests still pass |

**After every commit that touches application code:** `pytest tests/ -v` (or `-q` in CI). Treat a failing test as a blocker for merge and for ticking any task checkbox.

---

## §11 — Agent rules (constraints)

1. Finish each phase fully before starting the next.
2. Run that phase’s acceptance checks **and** the **Verification** commands above before marking it done.
3. If an AC fails, fix and re-run; do not skip failures.
4. Do not add dependencies not listed in `requirements.txt` without documenting why.
5. No extra abstraction layers: no ORM, Redis, or Docker unless specified.
6. Fetch file content via `raw.githubusercontent.com` — not the GitHub API contents endpoint.
7. ETag cache is **in-memory only** (not persisted to disk).
8. **TinyDB** (flat file) is the permitted store; no SQLite/Postgres for this scope.
9. Dashboard is **one** HTML file: `dashboard/static/index.html` — no split bundles, no build step.
10. Never hardcode `GITHUB_TOKEN`; read from environment only.
11. Log start/end of each crawl phase and resulting skill counts.
12. If `GITHUB_TOKEN` is missing: crawl **only** `PINNED_REPOS` (crawl phase 1), log clearly.
13. Use `asyncio` for async work; do not use threading for crawl/API.
14. In `_do_crawl`, catch exceptions: log, set `_crawling = False`, do not crash the server.

---

## Goals (summary)

- **Agent Skills Board:** crawler-first discovery over public `SKILL.md` (agentskills.io-style folders).
- **Sources:** Canonical `anthropics/skills`, `openai/skills`; `OFFICIAL_ORGS`; broad `filename:SKILL.md` search.
- **Stack:** Python 3.11+, `httpx` (async, HTTP/2), FastAPI + uvicorn, TinyDB, `python-frontmatter`, APScheduler, vanilla HTML/CSS/JS dashboard.

---

## §3 — Phase 1: `config.py`

| ID | Task |
|----|------|
| 3.1 | `GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")`; if empty, **WARNING** log (60/hr vs 5000/hr). |
| 3.2 | `OFFICIAL_ORGS`: anthropics, openai; vendors (dbt-labs, Snowflake-Labs, DataDog, atlassian, salesforce, servicenow, hashicorp, grafana, apache, mlflow); platform (redhat-community-ai-tools, openclaw, datahub-project, agentskills); community (kubernetes, cncf). |
| 3.3 | `PINNED_REPOS`: anthropics/skills, openai/skills, anthropics/claude-code, agentskills/agentskills, VoltAgent/awesome-agent-skills, datahub-project/datahub-skills, redhat-community-ai-tools/jira-mcp-snowflake, Snowflake-Labs/mcp, wong2/awesome-mcp-servers. |
| 3.4 | `ROLE_KEYWORDS`: 9 roles — developer, data, mlops, security, devops, analyst, tester, designer, architect — **≥10 keywords each** (real tools; examples given for data & security in PDF). |
| 3.5 | `SCORE_WEIGHTS` summing **100**: is_official 35, stars 25, downloads 15, recency 15, has_ci 5, has_tests 5. |
| 3.6 | Constants: `RATE_LIMIT_DELAY = 0.5`, `CACHE_TTL_HOURS = 6`, `MAX_SEARCH_PAGES = 5`, `DB_PATH`, `RAW_PATH` as specified in PDF. |

### Phase 1 acceptance (§10)

- **AC-1.1** `python3 -c "import config"` succeeds.
- **AC-1.2** `OFFICIAL_ORGS` has ≥15 entries including `anthropics`, `openai`.
- **AC-1.3** `PINNED_REPOS` includes `anthropics/skills`, `openai/skills`.
- **AC-1.4** All 9 roles in `ROLE_KEYWORDS` with ≥10 keywords each.
- **AC-1.5** `sum(SCORE_WEIGHTS.values()) == 100`.
- **AC-1.6** Warning logged when `GITHUB_TOKEN` unset.

---

## §4 — Phase 2: `crawler.py`

| ID | Task |
|----|------|
| 4.1 | Single shared `httpx.AsyncClient` per crawl; HTTP/2; `Authorization` if token; 20s timeout. |
| 4.2 | `gh_get(client, url, params)`: sleep `RATE_LIMIT_DELAY`; in-memory ETag cache + 304 handling; 403 → read `X-RateLimit-Reset`, sleep, retry; 404/422 → `None`; **tenacity** retries (4 attempts, backoff 2–30s). |
| 4.3 | `get_skill_paths`: `GET /repos/{o}/{r}/git/trees/HEAD?recursive=1`; blobs ending with `skill.md` (case-insensitive). |
| 4.4 | `fetch_skill_content`: `GET https://raw.githubusercontent.com/{o}/{r}/HEAD/{path}` (no API quota). |
| 4.5 | `get_repo_meta`: `GET /repos/{o}/{r}` → stars, forks, pushed_at, description, topics, html_url, language, license. |
| 4.6 | `has_ci`: `GET /repos/{o}/{r}/contents/.github/workflows`. |
| 4.7 | `crawl_repo`: skip if in `SEEN_REPOS`; `asyncio.gather` paths + meta + has_ci; `build_skill_record` per path; return skill dicts. |
| 4.8 | `_parse_frontmatter`: YAML between `---`; name/description/tags; fallbacks from path dir name and first body line. |
| 4.9 | `_detect_roles`: lowercase concat of name+description+tags vs `ROLE_KEYWORDS`; else `["general"]`. |
| 4.10 | Skill record: **22 fields** — `id` (md5 owner/repo/path, 12 chars), `name`, `org`, `repo`, `path`, `raw_url`, `github_url`, `description`, `tags`, `roles`, `stars`, `forks`, `pushed_at`, `language`, `license`, `topics`, `repo_desc`, `is_official`, `has_ci`, `format` (`SKILL.md`), `score` (0 at crawl), `crawled_at` (ISO UTC). |
| 4.11 | Crawl strategy: (1) all `PINNED_REPOS` in parallel; (2) per-org `filename:SKILL.md org:{org}` max 2 pages; (3) broad `filename:SKILL.md` up to `MAX_SEARCH_PAGES`. |
| 4.12 | `search_skills(client, query, max_pages)`: `/search/code`; dedupe `owner/repo`; early stop if &lt;100 items. |
| 4.13 | `if __name__ == "__main__"`: `asyncio.run(run_crawl())`; write `RAW_PATH`; print summary (totals by org & role). |

### Phase 2 acceptance (§10)

- **AC-2.1** `import crawler` OK.
- **AC-2.2** `pytest tests/test_crawler.py -v` — **7** tests pass.
- **AC-2.3** `_parse_frontmatter`: valid YAML / no YAML / malformed — no crash.
- **AC-2.4** `_detect_roles` → `["general"]` when no match.
- **AC-2.5** Records contain all 22 fields with correct types.
- **AC-2.6** Same repo twice → one result (`SEEN_REPOS`).
- **AC-2.7** ETag: second identical request uses cache on 304.
- **AC-2.8** 403 → sleep + retry.
- **AC-2.9** Content URLs use `raw.githubusercontent.com` (no `/api/` for file body).
- **AC-2.10** `python3 crawler.py` completes; no token → warning, pinned only, `raw_skills.json` valid with ≥1 skill from `anthropics/skills`.

---

## §5 — Phase 3: `normalizer.py`

| ID | Task |
|----|------|
| 5.1 | Scorers: `_score_official`, `_score_stars` (log10 cap), `_score_downloads`, `_score_recency` (half-life 90d), `_score_has_ci`, `_score_has_tests` (tags/description). |
| 5.2 | `compute_score(skill) -> int` in 0–100 from weighted sum. |
| 5.3 | `canonical_category(skill)`: priority `security > mlops > data > devops > developer > tester > analyst > designer > architect > general`. |
| 5.4 | `normalize(skills)`: set score & category; clean names with `/`; sort by score desc. |
| 5.5 | Pre-normalize dedupe by `id`; log duplicate count. |
| 5.6 | Main: load `RAW_PATH` → normalize → save `DB_PATH`; print top 10 table (score, org, name, category). |

### Phase 3 acceptance (§10)

- **AC-3.1** `pytest tests/test_normalizer.py -v` — **8** tests pass.
- **AC-3.2** `python3 normalizer.py` completes.
- **AC-3.3** `skills.json` exists and is valid JSON.
- **AC-3.4** Every skill `score` int in 0–100.
- **AC-3.5** Sorted by score descending.
- **AC-3.6** No duplicate IDs.
- **AC-3.7** `category` never null/empty.
- **AC-3.8** Official-org skills average score ≥ 35.

---

## §6 — Phase 4: `api.py`

| ID | Task |
|----|------|
| 6.1 | Startup: load `skills.json` into `_skills`; start APScheduler **24h** → `_do_crawl`; if `_skills` empty, kick first crawl in background. |
| 6.2 | Endpoints: `GET /api/skills` (q, category, role, official, sort score\|stars\|recency\|new, limit default 50 max 500, offset); response `{total, offset, limit, skills}`; `GET /api/skills/{id}` (404); `GET /api/stats` (total, official, community, categories, roles, **top_orgs**, crawling, **last_crawl**); `POST /api/crawl` (`started` / `already_running`); `GET /` → `index.html`; mount `/static` → `dashboard/static/`. |
| 6.3 | `_do_crawl`: set flag → `crawler.run_crawl()` → `normalizer.normalize()` → persist → reload `_skills` → clear flag → `_last_crawl` + duration log. |
| 6.4 | CORS: allow all (local tool). |

### Phase 4 acceptance (§10)

- **AC-4.1** `pytest tests/test_api.py -v` — **8** tests pass.
- **AC-4.2** `python3 api.py` starts on port 8000.
- **AC-4.3**–**AC-4.12** As in PDF (search `q`, `official`, `sort=stars`, `limit`/`offset`, `/api/stats` keys incl. `top_orgs`, `POST /api/crawl` idempotency, `GET /` HTML).

---

## §7 — Phase 5: `dashboard/static/index.html`

| ID | Task |
|----|------|
| 7.0 | Vanilla JS/CSS only; data only from `/api/*`; single file. |
| 7.1 | Layout: fixed topbar; **220px** sidebar; scrollable main (stats + grid). |
| 7.2 | Topbar: monospace logo `agentskillsboard`; search debounced **300ms** → `/api/skills?q=`; Re-crawl → `POST /api/crawl` + “Crawling…”; last crawl poll **30s**. |
| 7.3 | Sidebar: sort (top score, stars, recency, new); source (all / official / community); role & category from `/api/stats` with counts. |
| 7.4 | Stats bar: four pills (total, official, community, categories). |
| 7.5 | Cards: grid min **300px**; name mono; org + green official dot; “new” if pushed &lt;14d; format badges SKILL.md / MCP / both; 2-line description; 4 tag pills; footer stars + role + score bar. |
| 7.6 | Detail modal: full meta, table, install block (`curl` to `~/.skills/...` or MCP JSON), GitHub + raw links; close ESC / outside / X. |
| 7.7 | Pagination: **50** per page, “Load more”, “Showing X of Y”. |
| 7.8 | Skeleton loading; empty state when no results. |
| 7.9 | Dark theme colors per PDF (`#0d0f12`, `#13161b`, `#1a1e25`, borders, text). |
| 7.10 | Fonts: **DM Mono** + **DM Sans** (Google Fonts); accents per PDF (`#4f8ef7`, `#3ecf8e`, `#f59e0b`, muted `#7a8090`). |

### Phase 5 acceptance (§10 + §11 on page 11)

- **AC-5.1** No JS console errors on open.
- **AC-5.2** Skills render within **3s** of load.
- **AC-5.3** Search “snowflake” filters cards.
- **AC-5.4** Role “data” filter works.
- **AC-5.5** “Official only” hides community.
- **AC-5.6** “Most starred” reorders by stars.
- **AC-5.7** Card click → full metadata panel.
- **AC-5.8** ESC closes modal.
- **AC-5.9** Install command correct for SKILL.md.
- **AC-5.10** “Load more” when &gt;50 results.
- **AC-5.11** Empty state on zero results.
- **AC-5.12** Re-crawl label → “Crawling…” while active.
- **AC-5.13** Stats total matches `/api/stats`.

---

## §8 — Phase 6: `tests/`

- Framework: **pytest**; API tests via **httpx** `AsyncClient` / TestClient; **mock all GitHub** (no real network in unit tests).

| File | Tests (names from PDF) |
|------|-------------------------|
| `test_crawler.py` | `test_parse_frontmatter_with_yaml`, `test_parse_frontmatter_no_yaml`, `test_detect_roles_data`, `test_detect_roles_security`, `test_detect_roles_multiple`, `test_skill_record_has_required_fields`, `test_deduplication` |
| `test_normalizer.py` | official vs non-official scores, high stars, recent vs stale recency, `test_canonical_category_priority`, `test_normalize_sorts_by_score`, `test_weights_sum_to_100` |
| `test_api.py` | list, search, official filter, sort stars, get by id, 404, stats shape, trigger crawl |

### Phase 6 acceptance (page 11)

- **AC-6.1** `pytest tests/ -v` — **23** tests pass.
- **AC-6.2** No network during tests; GitHub fully mocked.
- **AC-6.3** Coverage: `crawler.py` ≥70%, `normalizer.py` ≥85%, `api.py` ≥75% (`pytest-cov` as in PDF).

---

## §9 — Phase 7: `run.sh` & `requirements.txt`

**`run.sh`**

1. Require Python **≥3.11**.
2. Create/activate `.venv`.
3. `pip install -q -r requirements.txt`.
4. `mkdir -p data`; if missing `data/skills.json`, warn about token, run `crawler.py` then `normalizer.py`.
5. `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`.
6. Print dashboard URL `http://localhost:8000`.

**`.env.example`**

```env
GITHUB_TOKEN=ghp_your_token_here
```

**Pinned deps (from PDF)**

`httpx[http2]==0.27.0`, `aiofiles==23.2.1`, `apscheduler==3.10.4`, `fastapi==0.111.0`, `uvicorn[standard]==0.30.1`, `pydantic==2.7.1`, `tinydb==4.8.0`, `python-frontmatter==1.1.0`, `rich==13.7.1`, `tenacity==8.3.0`, `pytest==8.2.0` (add `pytest-asyncio` / `httpx` test extras if tests require — document any deviation).

---

## End-to-end acceptance (page 11, §7)

- **AC-7.1** `bash run.sh` completes setup and serves.
- **AC-7.2** Dashboard shows real skills after setup.
- **AC-7.3** ≥10 real skills from GitHub.
- **AC-7.4** ≥1 skill from `anthropics/skills`.
- **AC-7.5** ≥1 from `openai/skills` if public.
- **AC-7.6** All official-org rows have `is_official == true`.
- **AC-7.7** Search `dbt` returns ≥1.
- **AC-7.8** Re-crawl updates counts.
- **AC-7.9** Data persists in `data/skills.json` across restarts.
- **AC-7.10** `/api/skills` tolerates arbitrary filter combos without 500.

---

*Generated from PDF structure; reconcile with current repo if the implementation has intentionally diverged (e.g. JSON store vs TinyDB API).*
