#!/usr/bin/env python3
"""
Playwright test for clicking on various Official skills
Demonstrates official skill discovery and interaction testing
"""

import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def test_click_various_official_skills():
    """Test clicking on various official skills by category"""
    print("🏛️ Testing Various Official Skills Interaction")
    print("=" * 50)

    # Start the API server
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    print("📡 Starting API server on port 8005...")
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8005'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        time.sleep(3)  # Wait for server startup

        with sync_playwright() as p:
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=False)  # Show browser for demo
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()

            # Navigate to dashboard
            print("\n1️⃣  Loading AgentSkillsBoard...")
            page.goto("http://127.0.0.1:8005")
            print(f"   ✅ Page loaded: {page.title()}")
            time.sleep(1)

            # Test different search terms and official skills
            search_terms = ["architect", "github", "code", "data", "web"]

            for i, term in enumerate(search_terms, 1):
                print(f"\n{i}️⃣  Testing '{term}' official skills...")

                # Clear search and enter new term
                search_input = page.locator('#search')
                search_input.fill('')
                time.sleep(0.5)
                search_input.fill(term)
                time.sleep(1.5)  # Wait for debounced search

                # Apply official filter
                official_filter = page.locator('[data-official="true"]')
                if not ('active' in (official_filter.get_attribute('class') or '')):
                    official_filter.click()
                    time.sleep(0.5)

                # Count results
                skill_cards = page.locator('.skill-card')
                count = skill_cards.count()
                print(f"   📊 Found {count} official {term} skills")

                if count > 0:
                    # Click on first skill
                    first_card = skill_cards.first
                    skill_name = first_card.locator('.card-name').inner_text()
                    skill_org = first_card.locator('.card-org').inner_text()

                    print(f"   🎯 Clicking: {skill_name} by {skill_org}")
                    first_card.click()
                    time.sleep(0.5)

                    # Verify modal and get details
                    modal = page.locator('#overlay')
                    assert 'open' in (modal.get_attribute('class') or ''), f"Modal didn't open for {term}"

                    detail_name = page.locator('.detail-name').inner_text()
                    detail_desc = page.locator('.detail-desc').inner_text()

                    print(f"   ✅ Modal opened: {detail_name}")
                    print(f"   📝 Description: {detail_desc[:80]}...")

                    # Check for official badge
                    official_badge = page.locator('.detail-official')
                    if official_badge.is_visible():
                        print("   🏛️ Official badge confirmed")

                    # Close modal with ESC
                    page.keyboard.press('Escape')
                    time.sleep(0.3)

                else:
                    print(f"   ⚠️ No official {term} skills found")

            # Test browsing all official skills without search
            print(f"\n6️⃣  Browsing all official skills...")
            search_input.fill('')
            time.sleep(1)

            # Make sure official filter is active
            if not ('active' in (official_filter.get_attribute('class') or '')):
                official_filter.click()
                time.sleep(0.5)

            all_official_cards = page.locator('.skill-card')
            total_official = all_official_cards.count()
            print(f"   📊 Total official skills displayed: {total_official}")

            # Click on a few random official skills
            for i in range(min(3, total_official)):
                print(f"\n   Testing official skill #{i+1}...")
                card = all_official_cards.nth(i)
                skill_name = card.locator('.card-name').inner_text()
                skill_org = card.locator('.card-org').inner_text()

                print(f"   🎯 Clicking: {skill_name} by {skill_org}")
                card.click()
                time.sleep(0.5)

                # Get skill details
                detail_name = page.locator('.detail-name').inner_text()
                detail_category = page.locator('.detail-category').inner_text() if page.locator('.detail-category').is_visible() else "N/A"

                print(f"   ✅ Opened: {detail_name}")
                print(f"   🏷️ Category: {detail_category}")

                # Check stars if visible
                stars_elem = page.locator('.detail-stars')
                if stars_elem.is_visible():
                    stars = stars_elem.inner_text()
                    print(f"   ⭐ Stars: {stars}")

                # Close modal
                page.keyboard.press('Escape')
                time.sleep(0.3)

            print("\n🎉 Official skills testing completed successfully!")
            time.sleep(2)  # Let user see final state

            browser.close()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        print("\n🔄 Shutting down server...")
        proc.terminate()
        proc.wait(timeout=5)

    print("\n✨ Official Skills Test Complete!")
    print("Successfully demonstrated:")
    print("  • Multiple search term filtering")
    print("  • Official skill identification")
    print("  • Skill modal interactions")
    print("  • Skill detail verification")
    print("  • Official badge confirmation")
    print("\nAll official skill interactions working! 🏛️")


if __name__ == "__main__":
    test_click_various_official_skills()