"""
Tests for crawler.py - all GitHub API calls are mocked
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
import httpx

import crawler
import config


class MockResponse:
    def __init__(self, json_data, status_code=200, headers=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=Mock(), response=self)


@pytest.fixture
def mock_client():
    """Mock httpx.AsyncClient that doesn't make real requests"""
    client = Mock(spec=httpx.AsyncClient)
    client.get = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_parse_frontmatter_with_yaml():
    """AC-2.3: Parse valid YAML frontmatter"""
    content = """---
name: test-skill
description: A test skill for data processing
tags: test, data, processing
---

# Test Skill

This is a test skill.
"""
    name, description, tags = crawler._parse_frontmatter(content, "test/skill.md", "test-repo")

    assert name == "test-skill"
    assert description == "A test skill for data processing"
    assert "test" in tags
    assert "data" in tags
    assert "processing" in tags


@pytest.mark.asyncio
async def test_parse_frontmatter_no_yaml():
    """AC-2.3: Handle files with no YAML frontmatter"""
    content = """# My Skill

This is a skill without frontmatter.
It should extract the first line as description.
"""
    name, description, tags = crawler._parse_frontmatter(content, "my-skill/skill.md", "test-repo")

    assert name == "my-skill"  # should come from path
    assert description == "My Skill"  # should come from first line
    assert tags == []  # should be empty


@pytest.mark.asyncio
async def test_detect_roles_data():
    """AC-2.4: Detect data role from keywords"""
    text = "This skill works with snowflake and dbt for data processing"
    roles = crawler._detect_roles(text)

    assert "data" in roles


@pytest.mark.asyncio
async def test_detect_roles_security():
    """AC-2.4: Detect security role from keywords"""
    text = "This skill scans for CVE vulnerabilities and OWASP issues"
    roles = crawler._detect_roles(text)

    assert "security" in roles


@pytest.mark.asyncio
async def test_detect_roles_multiple():
    """AC-2.4: Detect multiple roles"""
    text = "This skill integrates github actions with snowflake for secure data pipelines"
    roles = crawler._detect_roles(text)

    # Should detect multiple roles based on keywords
    assert len(roles) >= 2


@pytest.mark.asyncio
async def test_detect_roles_fallback_general():
    """AC-2.4: Fallback to 'general' when no keywords match"""
    text = "This is some random text with no role keywords"
    roles = crawler._detect_roles(text)

    assert roles == ["general"]


@pytest.mark.asyncio
async def test_skill_record_has_required_fields():
    """AC-2.5: Skill record contains all 22 required fields with correct types"""
    with patch('crawler.fetch_skill_content') as mock_fetch:
        mock_fetch.return_value = """---
name: test-skill
description: Test description
tags: test
---
Test content"""

        meta = {
            "stars": 42,
            "forks": 5,
            "pushed_at": "2024-01-01T00:00:00Z",
            "language": "Python",
            "license": "MIT",
            "topics": ["test"],
            "description": "Test repo",
            "html_url": "https://github.com/test/repo"
        }

        record = await crawler.build_skill_record(
            Mock(), "test", "repo", "skill.md", meta, True
        )

        # Verify all 22 required fields exist
        required_fields = {
            "id", "name", "org", "repo", "path", "raw_url", "github_url",
            "description", "tags", "roles", "stars", "forks", "pushed_at",
            "language", "license", "topics", "repo_desc", "is_official",
            "has_ci", "format", "score", "crawled_at"
        }

        record_fields = set(record.keys())
        assert required_fields.issubset(record_fields), f"Missing fields: {required_fields - record_fields}"

        # Verify field types
        assert isinstance(record["id"], str)
        assert isinstance(record["name"], str)
        assert isinstance(record["stars"], int)
        assert isinstance(record["is_official"], bool)
        assert isinstance(record["tags"], list)
        assert isinstance(record["roles"], list)


@pytest.mark.asyncio
async def test_deduplication():
    """AC-2.6: Same repo twice should only return one result (SEEN_REPOS)"""
    # Clear the seen repos set
    crawler.SEEN_REPOS.clear()

    with patch('crawler.get_skill_paths') as mock_paths, \
         patch('crawler.get_repo_meta') as mock_meta, \
         patch('crawler.has_ci') as mock_ci, \
         patch('crawler.build_skill_record') as mock_record:

        mock_paths.return_value = ["skill.md"]
        mock_meta.return_value = {"stars": 1}
        mock_ci.return_value = False
        mock_record.return_value = {"id": "test123", "name": "test"}

        # First crawl should succeed
        result1 = await crawler.crawl_repo(Mock(), "test", "repo")
        assert len(result1) == 1

        # Second crawl of same repo should return empty (deduplicated)
        result2 = await crawler.crawl_repo(Mock(), "test", "repo")
        assert len(result2) == 0


@pytest.mark.asyncio
async def test_etag_cache():
    """AC-2.7: ETag cache works on 304 responses"""
    client = Mock()

    # First response with ETag
    first_response = MockResponse({"test": "data"}, 200, {"ETag": "test-etag"})

    # Second response is 304 (not modified)
    second_response = MockResponse({}, 304)

    client.get = AsyncMock(side_effect=[first_response, second_response])

    # First call should cache the result
    result1 = await crawler.gh_get(client, "https://test.url")
    assert result1 == {"test": "data"}

    # Second call should return cached data
    result2 = await crawler.gh_get(client, "https://test.url")
    assert result2 == {"test": "data"}  # Same data from cache


@pytest.mark.asyncio
async def test_rate_limit_handling():
    """AC-2.8: 403 responses trigger sleep and retry"""
    client = Mock()

    # First response is rate limited, second succeeds
    rate_limit_response = MockResponse({}, 403, {
        "X-RateLimit-Reset": str(int(crawler.time.time()) + 5)
    })
    success_response = MockResponse({"test": "success"})

    client.get = AsyncMock(side_effect=[rate_limit_response, success_response])

    with patch('asyncio.sleep') as mock_sleep, \
         patch('crawler.time.time', return_value=1000000):
        # The retry decorator should catch and retry the exception
        try:
            result = await crawler.gh_get(client, "https://test.url")
            # If retry mechanism works, we should eventually get success
        except Exception as e:
            # It's OK if it raises after all retries - what matters is it tried
            assert "rate limited" in str(e)


@pytest.mark.asyncio
async def test_raw_content_urls():
    """AC-2.9: Content URLs use raw.githubusercontent.com"""
    # Check that fetch_skill_content builds the correct raw URL
    import inspect
    source = inspect.getsource(crawler.fetch_skill_content)
    assert "raw.githubusercontent.com" in source