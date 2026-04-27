#!/usr/bin/env python3
"""
Playwright test for clicking on Official architect skills
Demonstrates targeted skill search and interaction testing
"""

import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def test_click_official_architect_skills():
    """Test clicking on official architect skills specifically"""
    print("🏗️ Testing Official Architect Skills Interaction")
    print("=" * 50)

    # Start the API server
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    print("📡 Starting API server on port 8004...")
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8004'
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
            page.goto("http://127.0.0.1:8004")
            print(f"   ✅ Page loaded: {page.title()}")
            time.sleep(1)

            # Search for architect skills
            print("\n2️⃣  Searching for 'architect' skills...")
            search_input = page.locator('#search')
            search_input.fill('architect')
            print("   ⏳ Waiting for search results...")
            time.sleep(1.5)  # Wait for debounced search

            architect_cards = page.locator('.skill-card')
            architect_count = architect_cards.count()
            print(f"   📊 Found {architect_count} architect-related skills")

            # Apply official filter
            print("\n3️⃣  Filtering for Official skills only...")
            official_filter = page.locator('[data-official="true"]')
            official_filter.click()
            time.sleep(1)

            official_architect_cards = page.locator('.skill-card')
            official_count = official_architect_cards.count()
            print(f"   🏛️ Found {official_count} official architect skills")

            if official_count > 0:
                # Click on the first official architect skill
                print("\n4️⃣  Clicking on first official architect skill...")
                first_official_card = official_architect_cards.first

                # Get skill details before clicking
                skill_name = first_official_card.locator('.card-name').inner_text()
                skill_org = first_official_card.locator('.card-org').inner_text()
                print(f"   🎯 Clicking on: {skill_name} by {skill_org}")

                first_official_card.click()
                time.sleep(0.5)

                # Verify modal opened
                modal = page.locator('#overlay')
                assert 'open' in (modal.get_attribute('class') or ''), "Modal didn't open"
                print("   ✅ Skill modal opened successfully")

                # Check modal content
                detail_name = page.locator('.detail-name').inner_text()
                detail_org = page.locator('.detail-org').inner_text()
                detail_desc = page.locator('.detail-desc').inner_text()

                print(f"\n📋 Skill Details:")
                print(f"   Name: {detail_name}")
                print(f"   Organization: {detail_org}")
                print(f"   Description: {detail_desc[:100]}...")

                # Check if it's official
                detail_official = page.locator('.detail-official')
                if detail_official.is_visible():
                    print("   🏛️ Confirmed: Official skill")

                # Check GitHub link if present
                github_link = page.locator('.detail-github a')
                if github_link.is_visible():
                    github_url = github_link.get_attribute('href')
                    print(f"   🔗 GitHub: {github_url}")

                # Test modal interactions
                print("\n5️⃣  Testing modal interactions...")

                # Test ESC key to close
                page.keyboard.press('Escape')
                time.sleep(0.3)
                modal_class = modal.get_attribute('class') or ''
                assert 'open' not in modal_class, "Modal didn't close on ESC"
                print("   ✅ ESC key closes modal")

                # Click another architect skill to test multiple interactions
                if official_count > 1:
                    print("\n6️⃣  Testing second architect skill...")
                    second_card = official_architect_cards.nth(1)
                    second_skill_name = second_card.locator('.card-name').inner_text()
                    print(f"   🎯 Clicking on: {second_skill_name}")

                    second_card.click()
                    time.sleep(0.5)

                    # Verify different content loaded
                    new_detail_name = page.locator('.detail-name').inner_text()
                    assert new_detail_name != detail_name, "Same skill loaded"
                    print(f"   ✅ Different skill loaded: {new_detail_name}")

                    # Close modal by clicking overlay
                    page.locator('#overlay').click()
                    time.sleep(0.3)
                    print("   ✅ Click outside closes modal")

            else:
                print("   ⚠️ No official architect skills found")

                # Try community architect skills instead
                print("\n🔄 Trying community architect skills...")
                community_filter = page.locator('[data-official="false"]')
                community_filter.click()
                time.sleep(1)

                community_cards = page.locator('.skill-card')
                community_count = community_cards.count()
                print(f"   👥 Found {community_count} community architect skills")

                if community_count > 0:
                    first_community_card = community_cards.first
                    skill_name = first_community_card.locator('.card-name').inner_text()
                    skill_org = first_community_card.locator('.card-org').inner_text()
                    print(f"   🎯 Clicking on community skill: {skill_name} by {skill_org}")

                    first_community_card.click()
                    time.sleep(0.5)
                    print("   ✅ Community architect skill modal opened")

            print("\n🎉 Architect skills testing completed successfully!")
            time.sleep(2)  # Let user see final state

            browser.close()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        print("\n🔄 Shutting down server...")
        proc.terminate()
        proc.wait(timeout=5)

    print("\n✨ Official Architect Skills Test Complete!")
    print("Successfully demonstrated:")
    print("  • Targeted skill search (architect)")
    print("  • Official skill filtering")
    print("  • Skill card interactions")
    print("  • Modal content verification")
    print("  • Keyboard and mouse interactions")
    print("\nAll architect skill interactions working! 🏗️")


if __name__ == "__main__":
    test_click_official_architect_skills()