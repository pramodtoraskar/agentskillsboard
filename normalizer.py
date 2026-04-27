"""
normalizer.py — Score and enrich raw crawled skills.
Scoring formula (weights defined in config.py):
  is_official  35  — org in OFFICIAL_ORGS
  stars        25  — log10-normalised, cap at 10k stars = 1.0
  downloads    15  — log10-normalised (PyPI/npm), 0 if unknown
  recency      15  — exponential decay: full score if commit < 7 days ago
  has_ci        5  — binary
  has_tests     5  — binary
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import config


def _score_official(skill: dict) -> float:
    return 1.0 if skill.get("is_official") else 0.0


def _score_stars(skill: dict) -> float:
    stars = max(skill.get("stars", 0), 0)
    if stars == 0:
        return 0.0
    # log10 normalised: 10 stars→0.33, 100→0.67, 1000→1.0, cap at 1000+
    return min(math.log10(stars + 1) / math.log10(1001), 1.0)


def _score_downloads(skill: dict) -> float:
    dl = max(skill.get("downloads", 0), 0)
    if dl == 0:
        return 0.0
    return min(math.log10(dl + 1) / math.log10(100001), 1.0)


def _score_recency(skill: dict) -> float:
    pushed = skill.get("pushed_at", "")
    if not pushed:
        return 0.0
    try:
        dt  = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - dt).days
        # full score ≤7 days, halves every 90 days
        return math.exp(-0.693 * age / 90)
    except Exception:
        return 0.0


def _score_has_ci(skill: dict) -> float:
    return 1.0 if skill.get("has_ci") else 0.0


def _score_has_tests(skill: dict) -> float:
    # inferred: if topics or tags contain "test" or description mentions it
    text = (skill.get("description", "") + " " + " ".join(skill.get("tags", []))).lower()
    return 1.0 if "test" in text else 0.0


SCORERS = {
    "is_official": _score_official,
    "stars":       _score_stars,
    "downloads":   _score_downloads,
    "recency":     _score_recency,
    "has_ci":      _score_has_ci,
    "has_tests":   _score_has_tests,
}


def compute_score(skill: dict) -> int:
    total = 0.0
    for key, weight in config.SCORE_WEIGHTS.items():
        scorer = SCORERS.get(key)
        if scorer:
            total += scorer(skill) * weight
    return round(total)


def _canonical_category(skill: dict) -> str:
    roles = skill.get("roles", [])
    priority = ["security", "mlops", "data", "devops", "developer",
                "tester", "analyst", "designer", "architect", "general"]
    for p in priority:
        if p in roles:
            return p
    return roles[0] if roles else "general"


def normalize(skills: list[dict]) -> list[dict]:
    # Task 5.5: Pre-normalize dedupe by id; log duplicate count
    seen_ids = set()
    unique_skills = []
    duplicates = 0

    for s in skills:
        skill_id = s.get("id")
        if skill_id in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(skill_id)
        unique_skills.append(s)

    if duplicates > 0:
        print(f"Removed {duplicates} duplicate skills")

    out = []
    for s in unique_skills:
        s = dict(s)  # copy
        s["score"]    = compute_score(s)
        s["category"] = _canonical_category(s)
        # clean up name — strip path noise
        if "/" in s.get("name", ""):
            s["name"] = s["name"].split("/")[-1]
        out.append(s)
    # sort by score descending
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


if __name__ == "__main__":
    raw = Path("data/raw_skills.json")
    if not raw.exists():
        print("Run crawler.py first.")
        raise SystemExit(1)
    skills = json.loads(raw.read_text())
    normed = normalize(skills)
    out = Path("data/skills.json")
    out.write_text(json.dumps(normed, indent=2))
    print(f"Normalised {len(normed)} skills → {out}")
    # Print top 10
    print("\nTop 10 skills:")
    for s in normed[:10]:
        print(f"  [{s['score']:3d}] {s['org']}/{s['name']}  ({s['category']})")
