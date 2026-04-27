"""
Tests for api.py - FastAPI endpoints with mocked data
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

import api


# Test data
TEST_SKILLS = [
    {
        "id": "skill1",
        "name": "data-skill",
        "org": "anthropics",
        "repo": "skills",
        "description": "A skill for data processing",
        "tags": ["data", "etl"],
        "roles": ["data"],
        "stars": 150,
        "category": "data",
        "is_official": True,
        "pushed_at": "2024-01-15T00:00:00Z",
        "score": 75
    },
    {
        "id": "skill2",
        "name": "github-skill",
        "org": "openai",
        "repo": "skills",
        "description": "GitHub automation skill",
        "tags": ["github", "automation"],
        "roles": ["developer"],
        "stars": 50,
        "category": "developer",
        "is_official": True,
        "pushed_at": "2024-02-01T00:00:00Z",
        "score": 65
    },
    {
        "id": "skill3",
        "name": "community-skill",
        "org": "community",
        "repo": "tools",
        "description": "Community built skill",
        "tags": ["community"],
        "roles": ["general"],
        "stars": 10,
        "category": "general",
        "is_official": False,
        "pushed_at": "2024-03-01T00:00:00Z",
        "score": 25
    }
]


@pytest.fixture
def client():
    """Test client with mocked skills data"""
    # Mock the _load_db function to prevent loading real data
    with patch.object(api, '_load_db'):
        # Set the test data directly
        api._skills = TEST_SKILLS

        # Create the test client
        with TestClient(api.app) as test_client:
            yield test_client


def test_list_skills_basic(client):
    """Test basic skills listing"""
    response = client.get("/api/skills")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    assert "skills" in data
    assert data["total"] == 3
    assert len(data["skills"]) == 3


def test_search_skills(client):
    """Test search functionality with ?q= parameter"""
    # Search for "data"
    response = client.get("/api/skills?q=data")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1  # Only data-skill should match
    assert data["skills"][0]["name"] == "data-skill"

    # Search for "github"
    response = client.get("/api/skills?q=github")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["skills"][0]["name"] == "github-skill"


def test_official_filter(client):
    """Test official filter"""
    # Get only official skills
    response = client.get("/api/skills?official=true")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2  # Only official skills
    for skill in data["skills"]:
        assert skill["is_official"] == True

    # Get only community skills
    response = client.get("/api/skills?official=false")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1  # Only community skills
    assert data["skills"][0]["is_official"] == False


def test_sort_by_stars(client):
    """Test sorting by stars"""
    response = client.get("/api/skills?sort=stars")
    assert response.status_code == 200

    data = response.json()
    skills = data["skills"]

    # Should be sorted by stars descending
    stars = [skill["stars"] for skill in skills]
    assert stars == sorted(stars, reverse=True)
    assert skills[0]["stars"] == 150  # data-skill has most stars


def test_get_skill_by_id(client):
    """Test getting single skill by ID"""
    response = client.get("/api/skills/skill1")
    assert response.status_code == 200

    skill = response.json()
    assert skill["id"] == "skill1"
    assert skill["name"] == "data-skill"


def test_get_skill_404(client):
    """Test 404 for non-existent skill ID"""
    response = client.get("/api/skills/nonexistent")
    assert response.status_code == 404

    data = response.json()
    assert "error" in data


def test_stats_endpoint(client):
    """Test stats endpoint returns correct shape"""
    response = client.get("/api/stats")
    assert response.status_code == 200

    stats = response.json()

    # Check required fields
    required_fields = ["total", "official", "community", "categories", "roles", "top_orgs", "crawling", "last_crawl"]
    for field in required_fields:
        assert field in stats

    # Check values make sense
    assert stats["total"] == 3
    assert stats["official"] == 2  # anthropics and openai skills
    assert stats["community"] == 1  # community skill
    assert isinstance(stats["categories"], dict)
    assert isinstance(stats["roles"], dict)
    assert isinstance(stats["top_orgs"], list)
    assert isinstance(stats["crawling"], bool)


def test_trigger_crawl(client):
    """Test POST /api/crawl endpoint"""
    with patch.object(api, '_crawling', False):
        response = client.post("/api/crawl")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "started"

    # Test when already crawling
    with patch.object(api, '_crawling', True):
        response = client.post("/api/crawl")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "already_running"


def test_category_and_role_filters(client):
    """Test category and role filters"""
    # Test category filter
    response = client.get("/api/skills?category=data")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["skills"][0]["category"] == "data"

    # Test role filter
    response = client.get("/api/skills?role=developer")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert "developer" in data["skills"][0]["roles"]


def test_limit_and_offset(client):
    """Test pagination with limit and offset"""
    # Test limit
    response = client.get("/api/skills?limit=2")
    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 2
    assert len(data["skills"]) == 2
    assert data["total"] == 3  # Total should still be 3

    # Test offset
    response = client.get("/api/skills?limit=1&offset=1")
    assert response.status_code == 200

    data = response.json()
    assert data["offset"] == 1
    assert len(data["skills"]) == 1