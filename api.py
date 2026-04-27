"""
api.py — FastAPI backend
Endpoints:
  GET /api/skills          — full list with optional ?q=&category=&role=&sort=
  GET /api/skills/{id}     — single skill detail
  GET /api/stats           — summary counts
  POST /api/crawl          — trigger manual re-crawl
  GET /                    — serve dashboard HTML
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from crawler import run_crawl
from normalizer import normalize

log = logging.getLogger("api")
app = FastAPI(title="Agent Skills Board", version="1.0")

# Task 6.4: CORS setup (allow all for local tool)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH   = Path(config.DB_PATH)
_skills   = []          # in-memory cache
_crawling = False
_last_crawl = None


def _load_db():
    global _skills
    if DB_PATH.exists():
        _skills = json.loads(DB_PATH.read_text())
        log.info("Loaded %d skills from DB", len(_skills))


def _save_db(skills):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(skills, indent=2))


async def _do_crawl():
    global _skills, _crawling, _last_crawl
    if _crawling:
        log.info("Crawl already running, skipping")
        return
    _crawling = True
    log.info("Starting crawl…")
    start_time = time.time()
    try:
        raw    = await run_crawl()
        normed = normalize(raw)
        _save_db(normed)
        _skills = normed
        _last_crawl = datetime.now(timezone.utc).isoformat()
        duration = time.time() - start_time
        log.info("Crawl complete: %d skills in %.1fs", len(_skills), duration)
    except Exception as e:
        log.error("Crawl failed: %s", e)
    finally:
        _crawling = False


# ── Scheduler: re-crawl every 24h ─────────────────────────────────────────────

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    _load_db()
    scheduler.add_job(_do_crawl, "interval", hours=24, id="crawl")
    scheduler.start()
    # If DB is empty, kick off first crawl immediately
    if not _skills:
        asyncio.create_task(_do_crawl())


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/skills")
def list_skills(
    q:        Optional[str] = Query(None, description="Full-text search"),
    category: Optional[str] = Query(None),
    role:     Optional[str] = Query(None),
    sort:     Optional[str] = Query("score"),  # score|stars|recency|new
    official: Optional[bool]= Query(None),
    limit:    int           = Query(100, le=500),
    offset:   int           = Query(0),
):
    results = list(_skills)

    if q:
        ql = q.lower()
        results = [
            s for s in results
            if ql in (s.get("name","") + s.get("description","") +
                      s.get("org","") + " ".join(s.get("tags",[])) +
                      " ".join(s.get("topics",[]))).lower()
        ]

    if category:
        results = [s for s in results if s.get("category") == category]

    if role:
        results = [s for s in results if role in s.get("roles", [])]

    if official is not None:
        results = [s for s in results if s.get("is_official") == official]

    sort_key = {
        "score":   lambda s: s.get("score", 0),
        "stars":   lambda s: s.get("stars", 0),
        "recency": lambda s: s.get("pushed_at", ""),
        "new":     lambda s: s.get("crawled_at", ""),
    }.get(sort, lambda s: s.get("score", 0))

    results.sort(key=sort_key, reverse=True)

    return {
        "total":   len(results),
        "offset":  offset,
        "limit":   limit,
        "skills":  results[offset:offset + limit],
    }


@app.get("/api/skills/{skill_id}")
def get_skill(skill_id: str):
    for s in _skills:
        if s.get("id") == skill_id:
            return s
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/api/stats")
def stats():
    cats  = {}
    roles = {}
    orgs  = {}
    for s in _skills:
        c = s.get("category", "general")
        cats[c] = cats.get(c, 0) + 1
        for r in s.get("roles", []):
            roles[r] = roles.get(r, 0) + 1
        org = s.get("org", "unknown")
        orgs[org] = orgs.get(org, 0) + 1

    # Top 10 orgs by skill count
    top_orgs = sorted(orgs.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total":      len(_skills),
        "official":   sum(1 for s in _skills if s.get("is_official")),
        "community":  sum(1 for s in _skills if not s.get("is_official")),
        "categories": cats,
        "roles":      roles,
        "top_orgs":   [{"org": org, "count": count} for org, count in top_orgs],
        "crawling":   _crawling,
        "last_crawl": _last_crawl,
    }


@app.post("/api/crawl")
async def trigger_crawl(background_tasks: BackgroundTasks):
    if _crawling:
        return {"status": "already_running"}
    background_tasks.add_task(_do_crawl)
    return {"status": "started"}


# ── Static + SPA fallback ─────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "dashboard" / "static"

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
