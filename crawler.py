"""
crawler.py — GitHub SKILL.md crawler
Strategy (minimum API hits):
  1. Pinned repos  → 1 API call each  (get tree, find SKILL.md paths)
  2. Official orgs → 1 search call per org  (code search: filename:SKILL.md org:X)
  3. Broad search  → paginated code search  (filename:SKILL.md)
  4. ETag cache    → skip unchanged responses (304 = 0 quota used)
  5. Batch tree    → 1 tree call per repo, not 1 call per file
"""

import asyncio
import hashlib
import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("crawler")

GITHUB_API   = "https://api.github.com"
ETAG_CACHE   = {}          # url -> {"etag": str, "data": any}
SEEN_REPOS   = set()       # avoid double-crawling same repo
SKILL_BUFFER = []          # raw skill dicts before normalisation


# ── HTTP client (shared, keep-alive) ─────────────────────────────────────────

def make_client() -> httpx.AsyncClient:
    token = config.GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "AgentSkillsBoard-crawler/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.AsyncClient(headers=headers, timeout=20, http2=True)


# ── Rate-limit-aware GET with ETag caching ────────────────────────────────────

@retry(stop=stop_after_attempt(4),
       wait=wait_exponential(multiplier=1, min=2, max=30))
async def gh_get(client: httpx.AsyncClient, url: str,
                 params: dict | None = None) -> Any | None:
    """
    Single GitHub API GET.
    Returns parsed JSON or None on 404/empty.
    Uses ETag: if server returns 304, returns cached data (costs 0 rate-limit quota).
    """
    await asyncio.sleep(config.RATE_LIMIT_DELAY)

    cache_key = url + str(sorted((params or {}).items()))
    req_headers = {}
    if cache_key in ETAG_CACHE:
        req_headers["If-None-Match"] = ETAG_CACHE[cache_key]["etag"]

    r = await client.get(url, params=params, headers=req_headers)

    if r.status_code == 304:                     # not modified — free hit
        log.debug("304 cache hit: %s", url)
        return ETAG_CACHE[cache_key]["data"]

    if r.status_code == 403:
        reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait  = max(reset - int(time.time()), 5)
        log.warning("Rate limited. Sleeping %ds", wait)
        await asyncio.sleep(wait)
        raise Exception("rate limited — retry")

    if r.status_code in (404, 422):
        return None

    r.raise_for_status()
    data = r.json()

    if "ETag" in r.headers:
        ETAG_CACHE[cache_key] = {"etag": r.headers["ETag"], "data": data}

    return data


# ── Repo tree: 1 call → all paths in repo ─────────────────────────────────────

async def get_skill_paths(client: httpx.AsyncClient,
                           owner: str, repo: str) -> list[str]:
    """
    Fetch entire repo tree in ONE API call.
    Returns list of paths that end with SKILL.md (case-insensitive).
    """
    url  = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/HEAD"
    data = await gh_get(client, url, params={"recursive": "1"})
    if not data or "tree" not in data:
        return []
    return [
        item["path"] for item in data["tree"]
        if item["type"] == "blob"
        and item["path"].lower().endswith("skill.md")
    ]


# ── Fetch raw SKILL.md content ────────────────────────────────────────────────

async def fetch_skill_content(client: httpx.AsyncClient,
                               owner: str, repo: str, path: str) -> str:
    """Download raw SKILL.md — uses raw.githubusercontent.com (no API quota)."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
    try:
        r = await client.get(url)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        log.warning("Failed to fetch %s/%s/%s: %s", owner, repo, path, e)
    return ""


# ── Repo metadata: stars, last commit, CI presence ────────────────────────────

async def get_repo_meta(client: httpx.AsyncClient,
                         owner: str, repo: str) -> dict:
    """1 API call → stars, pushed_at, default_branch, topics."""
    data = await gh_get(client, f"{GITHUB_API}/repos/{owner}/{repo}")
    if not data:
        return {}
    return {
        "stars":        data.get("stargazers_count", 0),
        "forks":        data.get("forks_count", 0),
        "pushed_at":    data.get("pushed_at", ""),
        "description":  data.get("description", ""),
        "topics":       data.get("topics", []),
        "html_url":     data.get("html_url", ""),
        "language":     data.get("language", ""),
        "license":      (data.get("license") or {}).get("spdx_id", ""),
    }


async def has_ci(client: httpx.AsyncClient, owner: str, repo: str) -> bool:
    """Check if .github/workflows exists — 1 API call."""
    data = await gh_get(client, f"{GITHUB_API}/repos/{owner}/{repo}/contents/.github/workflows")
    return bool(data)


# ── Build a skill record from repo + path ─────────────────────────────────────

async def build_skill_record(client: httpx.AsyncClient,
                              owner: str, repo: str,
                              path: str, meta: dict,
                              ci: bool) -> dict:
    content = await fetch_skill_content(client, owner, repo, path)

    # Parse YAML frontmatter manually (avoid dependency on python-frontmatter for speed)
    name, description, fm_tags = _parse_frontmatter(content, path, repo)

    # Derive roles from name + description + tags
    roles = _detect_roles(f"{name} {description} {' '.join(fm_tags)}")

    # Detect official status
    is_official = owner.lower() in [o.lower() for o in config.OFFICIAL_ORGS]

    uid = hashlib.md5(f"{owner}/{repo}/{path}".encode()).hexdigest()[:12]

    return {
        "id":           uid,
        "name":         name,
        "org":          owner,
        "repo":         repo,
        "path":         path,
        "raw_url":      f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}",
        "github_url":   f"https://github.com/{owner}/{repo}/blob/HEAD/{path}",
        "description":  description,
        "tags":         fm_tags,
        "roles":        roles,
        "stars":        meta.get("stars", 0),
        "forks":        meta.get("forks", 0),
        "pushed_at":    meta.get("pushed_at", ""),
        "language":     meta.get("language", ""),
        "license":      meta.get("license", ""),
        "topics":       meta.get("topics", []),
        "repo_desc":    meta.get("description", ""),
        "is_official":  is_official,
        "has_ci":       ci,
        "format":       "SKILL.md",
        "score":        0,      # filled by normaliser
        "crawled_at":   datetime.now(timezone.utc).isoformat(),
    }


# ── Frontmatter parser (no extra deps, fast) ──────────────────────────────────

def _parse_frontmatter(content: str, path: str, repo: str):
    """Extract name, description, tags from SKILL.md YAML frontmatter."""
    name        = Path(path).parent.name or repo
    description = ""
    tags        = []

    if not content.startswith("---"):
        # No frontmatter — grab first non-empty line as description
        for line in content.splitlines():
            line = line.strip().lstrip("#").strip()
            if line:
                description = line[:200]
                break
        return name, description, tags

    try:
        end = content.index("---", 3)
        fm  = content[3:end].strip()
    except ValueError:
        return name, description, tags

    for line in fm.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "name" and v:
            name = v
        elif k == "description" and v:
            description = v[:300]
        elif k in ("tags", "keywords", "tools"):
            # handle both inline list and single value
            tags = [t.strip().strip("-").strip() for t in v.split(",") if t.strip()]

    # fallback description from first content paragraph
    if not description:
        in_fm = False
        for line in content.splitlines():
            if line.strip() == "---":
                in_fm = not in_fm
                continue
            if not in_fm and line.strip():
                l = line.strip().lstrip("#").strip()
                if l:
                    description = l[:300]
                    break

    return name, description, tags


def _detect_roles(text: str) -> list[str]:
    text_lower = text.lower()
    return [
        role for role, keywords in config.ROLE_KEYWORDS.items()
        if any(kw in text_lower for kw in keywords)
    ] or ["general"]


# ── Crawl a single repo ────────────────────────────────────────────────────────

async def crawl_repo(client: httpx.AsyncClient,
                      owner: str, repo: str) -> list[dict]:
    key = f"{owner}/{repo}"
    if key in SEEN_REPOS:
        return []
    SEEN_REPOS.add(key)

    log.info("Crawling %s", key)

    paths, meta, ci = await asyncio.gather(
        get_skill_paths(client, owner, repo),
        get_repo_meta(client, owner, repo),
        has_ci(client, owner, repo),
    )

    if not paths:
        return []

    records = await asyncio.gather(*[
        build_skill_record(client, owner, repo, p, meta, ci)
        for p in paths
    ])
    log.info("  found %d skill(s) in %s", len(records), key)
    return list(records)


# ── GitHub code search: filename:SKILL.md ─────────────────────────────────────

async def search_skills(client: httpx.AsyncClient,
                         query: str = "filename:SKILL.md",
                         max_pages: int = config.MAX_SEARCH_PAGES) -> list[dict]:
    """
    Code search API — returns list of {owner, repo} dicts.
    1 API call per page (100 results each).
    """
    repos_found = []
    for page in range(1, max_pages + 1):
        data = await gh_get(client, f"{GITHUB_API}/search/code", params={
            "q":        query,
            "per_page": 100,
            "page":     page,
        })
        if not data or not data.get("items"):
            break
        for item in data["items"]:
            repos_found.append({
                "owner": item["repository"]["owner"]["login"],
                "repo":  item["repository"]["name"],
            })
        if len(data["items"]) < 100:
            break
        log.info("Search page %d: %d results", page, len(data["items"]))

    # deduplicate
    seen = set()
    unique = []
    for r in repos_found:
        k = f"{r['owner']}/{r['repo']}"
        if k not in seen:
            seen.add(k)
            unique.append(r)
    return unique


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_crawl() -> list[dict]:
    all_skills = []

    async with make_client() as client:
        # ── Phase 1: Pinned repos (highest priority, ~10 API calls) ──────────
        log.info("=== Phase 1: Pinned repos ===")
        pinned_tasks = []
        for slug in config.PINNED_REPOS:
            owner, repo = slug.split("/", 1)
            pinned_tasks.append(crawl_repo(client, owner, repo))
        results = await asyncio.gather(*pinned_tasks)
        for r in results:
            all_skills.extend(r)

        # ── Phase 2: Official org searches (1 search call per org) ───────────
        log.info("=== Phase 2: Official org searches ===")
        for org in config.OFFICIAL_ORGS:
            query = f"filename:SKILL.md org:{org}"
            repo_hits = await search_skills(client, query, max_pages=2)
            repo_tasks = [crawl_repo(client, h["owner"], h["repo"]) for h in repo_hits]
            org_results = await asyncio.gather(*repo_tasks)
            for r in org_results:
                all_skills.extend(r)

        # ── Phase 3: Broad search (remaining pages) ───────────────────────────
        log.info("=== Phase 3: Broad GitHub search ===")
        broad_hits = await search_skills(client, "filename:SKILL.md",
                                          max_pages=config.MAX_SEARCH_PAGES)
        broad_tasks = [crawl_repo(client, h["owner"], h["repo"]) for h in broad_hits]
        broad_results = await asyncio.gather(*broad_tasks)
        for r in broad_results:
            all_skills.extend(r)

    # Deduplicate by id
    seen_ids = set()
    unique = []
    for s in all_skills:
        if s["id"] not in seen_ids:
            seen_ids.add(s["id"])
            unique.append(s)

    log.info("Total unique skills crawled: %d", len(unique))
    return unique


if __name__ == "__main__":
    skills = asyncio.run(run_crawl())
    out = Path("data/raw_skills.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(skills, indent=2))
    log.info("Saved %d skills to %s", len(skills), out)
