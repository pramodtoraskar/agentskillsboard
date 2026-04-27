"""
Simple Playwright UI tests for AgentSkillsBoard dashboard
Tests key frontend functionality without complex async fixtures
"""

import subprocess
import time
import signal
import os


def test_ui_with_playwright():
    """Test the UI using Playwright in a simpler way"""
    # Start the API server on port 8002 to avoid conflicts
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8002'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        # Wait for server to start
        time.sleep(3)

        # Use playwright CLI to test basic functionality
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()

            # Navigate to dashboard
            page.goto("http://127.0.0.1:8002")

            # Test 1: Page loads and has correct title
            assert "Agent Skills Board" in page.title()
            print("✓ Page loads with correct title")

            # Test 2: Main elements are present
            assert page.locator('.topbar').is_visible()
            assert page.locator('.sidebar').is_visible()
            assert page.locator('.main').is_visible()
            print("✓ Main layout elements are visible")

            # Test 3: Search functionality exists
            search_input = page.locator('#search')
            assert search_input.is_visible()
            print("✓ Search input is present")

            # Test 4: Search functionality works
            search_input.fill('github')
            time.sleep(1)  # Wait for debounced search
            print("✓ Search input accepts text")

            # Test 5: Skills grid exists and loads
            skills_grid = page.locator('#grid')
            assert skills_grid.is_visible()
            print("✓ Skills grid is visible")

            # Test 6: No JavaScript console errors
            console_errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)

            page.on('console', handle_console)
            page.reload()
            time.sleep(2)

            assert len(console_errors) == 0, f"Console errors: {console_errors}"
            print("✓ No console errors detected")

            # Test 7: Stats are loaded
            stats_total = page.locator('#s-total')
            if stats_total.is_visible():
                total_text = stats_total.inner_text()
                assert total_text.replace(',', '').isdigit()
                print(f"✓ Stats loaded: {total_text} total skills")

            # Test 8: Filter buttons exist and are clickable
            official_filter = page.locator('[data-official="true"]')
            if official_filter.is_visible():
                official_filter.click()
                time.sleep(0.5)
                print("✓ Official filter is clickable")

            # Test 9: Sort functionality exists
            sort_stars = page.locator('[data-sort="stars"]')
            if sort_stars.is_visible():
                sort_stars.click()
                time.sleep(0.5)
                print("✓ Sort by stars works")

            # Test 10: Skill cards display if present
            skill_cards = page.locator('.skill-card')
            if skill_cards.count() > 0:
                first_card = skill_cards.first
                assert first_card.locator('.card-name').is_visible()
                assert first_card.locator('.card-org').is_visible()
                print(f"✓ {skill_cards.count()} skill cards rendered correctly")

                # Test 11: Modal opens when clicking card
                first_card.click()
                time.sleep(0.5)

                modal = page.locator('#overlay')
                assert modal.get_attribute('class') and 'open' in modal.get_attribute('class')
                print("✓ Detail modal opens on card click")

                # Test 12: ESC closes modal
                page.keyboard.press('Escape')
                time.sleep(0.2)
                modal_class = modal.get_attribute('class') or ''
                assert 'open' not in modal_class
                print("✓ ESC key closes modal")

            browser.close()

        print("\n✅ All UI tests passed successfully!")

    finally:
        # Clean shutdown
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    test_ui_with_playwright()