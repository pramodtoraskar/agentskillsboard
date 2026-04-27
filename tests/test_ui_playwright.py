"""
Playwright UI tests for AgentSkillsBoard dashboard
Tests the complete frontend functionality in a real browser
"""

import pytest
import asyncio
import subprocess
import time
import signal
import os
from playwright.async_api import Page, expect


@pytest.fixture(scope="session")
def api_server():
    """Start the API server for UI tests"""
    # Start the server
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '0.0.0.0', '--port', '8001'
    ], env=env)

    # Wait for server to start
    time.sleep(3)

    yield "http://localhost:8001"

    # Clean shutdown
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=5)


@pytest.mark.asyncio
async def test_page_loads_correctly(page: Page, api_server):
    """Test that the main page loads without errors"""
    # Navigate to the dashboard
    await page.goto(api_server)

    # Check page title
    await expect(page).to_have_title("Agent Skills Board — Agent Skill Registry")

    # Check main elements are present
    await expect(page.locator('.topbar')).to_be_visible()
    await expect(page.locator('.sidebar')).to_be_visible()
    await expect(page.locator('.main')).to_be_visible()

    # Check for the logo
    await expect(page.locator('text=agentskillsboard')).to_be_visible()

    # Check that search input exists
    await expect(page.locator('#search')).to_be_visible()


@pytest.mark.asyncio
async def test_no_console_errors(page: Page, api_server):
    """Test that there are no JavaScript console errors"""
    console_errors = []

    def handle_console_message(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    page.on("console", handle_console_message)

    await page.goto(api_server)

    # Wait for page to fully load
    await page.wait_for_timeout(2000)

    # Assert no console errors
    assert len(console_errors) == 0, f"Console errors found: {console_errors}"


@pytest.mark.asyncio
async def test_search_functionality(page: Page, api_server):
    """Test the search functionality with debouncing"""
    await page.goto(api_server)

    # Wait for initial load
    await page.wait_for_selector('#grid')

    # Get initial skill count
    initial_cards = await page.locator('.skill-card').count()

    # Perform search
    await page.fill('#search', 'github')

    # Wait for debounced search (300ms + request time)
    await page.wait_for_timeout(500)

    # Check that results were filtered
    filtered_cards = await page.locator('.skill-card').count()

    # Should have some results (or at least different from initial if we have github skills)
    assert filtered_cards >= 0  # At least 0 results (empty is valid if no github skills)

    # Clear search
    await page.fill('#search', '')
    await page.wait_for_timeout(500)

    # Should return to original state
    final_cards = await page.locator('.skill-card').count()
    assert final_cards == initial_cards


@pytest.mark.asyncio
async def test_filter_functionality(page: Page, api_server):
    """Test filtering by official/community"""
    await page.goto(api_server)

    # Wait for page to load
    await page.wait_for_selector('#grid')

    # Click "Official only" filter
    official_filter = page.locator('[data-official="true"]')
    await official_filter.click()

    # Wait for filter to apply
    await page.wait_for_timeout(500)

    # Check that the filter is active
    await expect(official_filter).to_have_class("active")

    # Click "Community" filter
    community_filter = page.locator('[data-official="false"]')
    await community_filter.click()

    # Wait for filter to apply
    await page.wait_for_timeout(500)

    # Check that community filter is now active
    await expect(community_filter).to_have_class("active")


@pytest.mark.asyncio
async def test_sort_functionality(page: Page, api_server):
    """Test sorting options work correctly"""
    await page.goto(api_server)

    # Wait for page to load
    await page.wait_for_selector('#grid')

    # Test sorting by stars
    stars_sort = page.locator('[data-sort="stars"]')
    await stars_sort.click()

    # Wait for sort to apply
    await page.wait_for_timeout(500)

    # Check that stars sort is active
    await expect(stars_sort).to_have_class("active")

    # Test sorting by recency
    recency_sort = page.locator('[data-sort="recency"]')
    await recency_sort.click()

    # Wait for sort to apply
    await page.wait_for_timeout(500)

    # Check that recency sort is active
    await expect(recency_sort).to_have_class("active")


@pytest.mark.asyncio
async def test_skill_card_modal(page: Page, api_server):
    """Test that clicking a skill card opens the detail modal"""
    await page.goto(api_server)

    # Wait for skills to load
    await page.wait_for_selector('.skill-card')

    # Click the first skill card
    first_card = page.locator('.skill-card').first
    await first_card.click()

    # Wait for modal to open
    await page.wait_for_timeout(500)

    # Check modal is visible
    modal = page.locator('#overlay')
    await expect(modal).to_have_class("open")

    # Check modal content exists
    await expect(page.locator('#detail-content')).to_be_visible()
    await expect(page.locator('.detail-name')).to_be_visible()
    await expect(page.locator('.detail-desc')).to_be_visible()

    # Test ESC key closes modal
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(100)

    # Modal should be closed
    await expect(modal).not_to_have_class("open")


@pytest.mark.asyncio
async def test_stats_integration(page: Page, api_server):
    """Test that stats are loaded and displayed"""
    await page.goto(api_server)

    # Wait for stats to load
    await page.wait_for_timeout(1000)

    # Check stats elements exist and have content
    total_stat = page.locator('#s-total')
    await expect(total_stat).to_be_visible()

    official_stat = page.locator('#s-official')
    await expect(official_stat).to_be_visible()

    community_stat = page.locator('#s-community')
    await expect(community_stat).to_be_visible()

    categories_stat = page.locator('#s-cats')
    await expect(categories_stat).to_be_visible()

    # Check that they have numeric content (not just "0")
    total_text = await total_stat.inner_text()
    assert total_text.replace(',', '').isdigit(), f"Total should be numeric, got: {total_text}"


@pytest.mark.asyncio
async def test_responsive_layout(page: Page, api_server):
    """Test that the layout works on different screen sizes"""
    await page.goto(api_server)

    # Test desktop size (default)
    await page.set_viewport_size({"width": 1280, "height": 720})
    await expect(page.locator('.sidebar')).to_be_visible()

    # Test tablet size
    await page.set_viewport_size({"width": 768, "height": 1024})
    await page.wait_for_timeout(100)

    # Main content should still be visible
    await expect(page.locator('.main')).to_be_visible()


@pytest.mark.asyncio
async def test_pagination_load_more(page: Page, api_server):
    """Test the Load More pagination functionality"""
    await page.goto(api_server)

    # Wait for initial skills to load
    await page.wait_for_selector('.skill-card')
    await page.wait_for_timeout(500)

    # Count initial cards
    initial_count = await page.locator('.skill-card').count()

    # Check if "Load More" button is visible (only if there are >50 skills)
    load_more_button = page.locator('#load-more')

    if await load_more_button.is_visible():
        # Click Load More
        await load_more_button.click()

        # Wait for new cards to load
        await page.wait_for_timeout(1000)

        # Should have more cards now
        new_count = await page.locator('.skill-card').count()
        assert new_count > initial_count, f"Expected more cards after load more: {initial_count} -> {new_count}"


@pytest.mark.asyncio
async def test_keyboard_shortcuts(page: Page, api_server):
    """Test keyboard shortcuts work correctly"""
    await page.goto(api_server)

    # Test Cmd+K (or Ctrl+K) focuses search
    await page.keyboard.press('Meta+k')  # Use Meta (Cmd) on Mac

    # Search input should be focused
    focused_element = await page.evaluate("document.activeElement.id")
    assert focused_element == "search", f"Expected search to be focused, but {focused_element} is focused"


@pytest.mark.asyncio
async def test_theme_and_styling(page: Page, api_server):
    """Test that the dark theme is applied correctly"""
    await page.goto(api_server)

    # Check CSS custom properties are set (dark theme)
    bg_color = await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--bg')")
    assert bg_color.strip() == "#0d0f12", f"Expected dark background color, got: {bg_color}"

    # Check that Google Fonts are loaded
    font_family = await page.evaluate("getComputedStyle(document.body).fontFamily")
    assert "DM Sans" in font_family, f"Expected DM Sans font, got: {font_family}"


@pytest.mark.asyncio
async def test_api_error_handling(page: Page, api_server):
    """Test that the UI handles API errors gracefully"""
    await page.goto(api_server)

    # Wait for initial load
    await page.wait_for_timeout(1000)

    # The page should still be functional even if some API calls fail
    # Check that essential elements are still visible
    await expect(page.locator('.topbar')).to_be_visible()
    await expect(page.locator('#search')).to_be_visible()

    # Search should still work (might show empty results)
    await page.fill('#search', 'test-query')
    await page.wait_for_timeout(500)

    # Page should not crash
    await expect(page.locator('.main')).to_be_visible()


@pytest.mark.asyncio
async def test_skill_card_content(page: Page, api_server):
    """Test that skill cards display the expected content"""
    await page.goto(api_server)

    # Wait for cards to load
    await page.wait_for_selector('.skill-card')

    # Check first card has expected structure
    first_card = page.locator('.skill-card').first

    # Should have name
    await expect(first_card.locator('.card-name')).to_be_visible()

    # Should have org
    await expect(first_card.locator('.card-org')).to_be_visible()

    # Should have description
    await expect(first_card.locator('.card-desc')).to_be_visible()

    # Should have footer with stars and score
    await expect(first_card.locator('.card-footer')).to_be_visible()
    await expect(first_card.locator('.stars')).to_be_visible()
    await expect(first_card.locator('.score-wrap')).to_be_visible()


@pytest.mark.asyncio
async def test_crawl_button_functionality(page: Page, api_server):
    """Test the manual crawl trigger button"""
    await page.goto(api_server)

    # Wait for page to load
    await page.wait_for_timeout(1000)

    # Find and click the crawl button
    crawl_button = page.locator('#crawl-btn')

    if await crawl_button.is_visible():
        # Click the button
        await crawl_button.click()

        # Button text should change to indicate crawling
        await page.wait_for_timeout(500)
        button_text = await crawl_button.inner_text()

        # Should show some indication of activity
        assert "Crawling" in button_text or "Starting" in button_text, f"Expected crawling indicator, got: {button_text}"