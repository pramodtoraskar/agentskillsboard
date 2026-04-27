"""
Tests for normalizer.py - score computation and normalization
"""

import pytest
from datetime import datetime, timezone, timedelta

import normalizer
import config


def test_official_vs_non_official_scores():
    """Official org skills should score higher than community"""
    official_skill = {
        "is_official": True,
        "stars": 100,
        "downloads": 0,
        "pushed_at": "2024-01-01T00:00:00Z",
        "has_ci": False,
        "description": "",
        "tags": []
    }

    non_official_skill = {
        "is_official": False,
        "stars": 100,
        "downloads": 0,
        "pushed_at": "2024-01-01T00:00:00Z",
        "has_ci": False,
        "description": "",
        "tags": []
    }

    official_score = normalizer.compute_score(official_skill)
    non_official_score = normalizer.compute_score(non_official_skill)

    assert official_score > non_official_score
    # Official boost should be 35 points (the weight for is_official)
    assert official_score - non_official_score >= 30  # allowing some variance


def test_high_stars_score():
    """Skills with more stars should score higher"""
    low_stars_skill = {
        "is_official": False,
        "stars": 10,
        "downloads": 0,
        "pushed_at": "2024-01-01T00:00:00Z",
        "has_ci": False,
        "description": "",
        "tags": []
    }

    high_stars_skill = {
        "is_official": False,
        "stars": 1000,
        "downloads": 0,
        "pushed_at": "2024-01-01T00:00:00Z",
        "has_ci": False,
        "description": "",
        "tags": []
    }

    low_score = normalizer.compute_score(low_stars_skill)
    high_score = normalizer.compute_score(high_stars_skill)

    assert high_score > low_score


def test_recent_vs_stale_recency():
    """Recent skills should score higher than stale ones"""
    # Recent skill (1 day ago)
    recent_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    recent_skill = {
        "is_official": False,
        "stars": 100,
        "downloads": 0,
        "pushed_at": recent_date,
        "has_ci": False,
        "description": "",
        "tags": []
    }

    # Stale skill (2 years ago)
    stale_date = (datetime.now(timezone.utc) - timedelta(days=730)).isoformat()
    stale_skill = {
        "is_official": False,
        "stars": 100,
        "downloads": 0,
        "pushed_at": stale_date,
        "has_ci": False,
        "description": "",
        "tags": []
    }

    recent_score = normalizer.compute_score(recent_skill)
    stale_score = normalizer.compute_score(stale_skill)

    assert recent_score > stale_score


def test_canonical_category_priority():
    """Category should follow priority order: security > mlops > data > devops > ..."""
    # Test security takes priority over data
    security_data_skill = {
        "roles": ["data", "security"]  # security should win
    }
    category = normalizer._canonical_category(security_data_skill)
    assert category == "security"

    # Test mlops takes priority over devops
    mlops_devops_skill = {
        "roles": ["devops", "mlops"]  # mlops should win
    }
    category = normalizer._canonical_category(mlops_devops_skill)
    assert category == "mlops"

    # Test fallback to general
    empty_roles_skill = {
        "roles": []
    }
    category = normalizer._canonical_category(empty_roles_skill)
    assert category == "general"


def test_normalize_sorts_by_score():
    """Normalize function should sort skills by score descending"""
    skills = [
        {
            "id": "skill1",
            "name": "low-score",
            "is_official": False,
            "stars": 1,
            "downloads": 0,
            "pushed_at": "2020-01-01T00:00:00Z",
            "has_ci": False,
            "description": "",
            "tags": [],
            "roles": ["general"]
        },
        {
            "id": "skill2",
            "name": "high-score",
            "is_official": True,
            "stars": 1000,
            "downloads": 100000,
            "pushed_at": datetime.now(timezone.utc).isoformat(),
            "has_ci": True,
            "description": "test framework",
            "tags": ["test"],
            "roles": ["security"]
        }
    ]

    normalized = normalizer.normalize(skills)

    # Should be sorted by score descending
    assert len(normalized) == 2
    assert normalized[0]["score"] >= normalized[1]["score"]
    # High score skill should be first
    assert normalized[0]["name"] == "high-score"


def test_weights_sum_to_100():
    """Score weights should sum exactly to 100"""
    total = sum(config.SCORE_WEIGHTS.values())
    assert total == 100


def test_score_range_0_to_100():
    """Computed scores should be in range 0-100"""
    # Perfect score skill
    perfect_skill = {
        "is_official": True,
        "stars": 10000,
        "downloads": 1000000,
        "pushed_at": datetime.now(timezone.utc).isoformat(),
        "has_ci": True,
        "description": "comprehensive testing framework",
        "tags": ["test", "framework"]
    }

    # Zero score skill
    zero_skill = {
        "is_official": False,
        "stars": 0,
        "downloads": 0,
        "pushed_at": "",
        "has_ci": False,
        "description": "",
        "tags": []
    }

    perfect_score = normalizer.compute_score(perfect_skill)
    zero_score = normalizer.compute_score(zero_skill)

    assert 0 <= zero_score <= 100
    assert 0 <= perfect_score <= 100
    assert perfect_score > zero_score


def test_deduplication():
    """Normalize should remove duplicate skills by ID"""
    skills = [
        {
            "id": "duplicate_id",
            "name": "first",
            "is_official": False,
            "stars": 1,
            "roles": ["general"]
        },
        {
            "id": "duplicate_id",  # Same ID
            "name": "second",
            "is_official": True,
            "stars": 1000,
            "roles": ["security"]
        },
        {
            "id": "unique_id",
            "name": "unique",
            "is_official": False,
            "stars": 50,
            "roles": ["data"]
        }
    ]

    # Should remove duplicate, keeping first occurrence
    normalized = normalizer.normalize(skills)

    assert len(normalized) == 2  # One duplicate removed
    skill_ids = [s["id"] for s in normalized]
    assert "duplicate_id" in skill_ids
    assert "unique_id" in skill_ids

    # First skill with duplicate ID should be kept
    duplicate_skill = next(s for s in normalized if s["id"] == "duplicate_id")
    assert duplicate_skill["name"] == "first"