#!/usr/bin/env python3
"""
Playwright test comparing Official vs Community architect skills
Demonstrates filtering and comparison testing
"""

import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def test_architect_official_vs_community():
    """Compare official vs community architect skills"""
    print("⚖️ Testing Official vs Community Architect Skills")
    print("=" * 55)

    # Start the API server
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    print("📡 Starting API server on port 8006...")
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8006'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        time.sleep(3)  # Wait for server startup

        with sync_playwright() as p:
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={'width': 1400, 'height': 800})
            page = context.new_page()

            # Navigate to dashboard
            print("\n1️⃣  Loading AgentSkillsBoard...")
            page.goto("http://127.0.0.1:8006")
            print(f"   ✅ Page loaded: {page.title()}")
            time.sleep(1)

            # Search for architect skills
            print("\n2️⃣  Searching for 'architect' skills...")
            search_input = page.locator('#search')
            search_input.fill('architect')
            time.sleep(1.5)

            all_architect_cards = page.locator('.skill-card')
            total_architects = all_architect_cards.count()
            print(f"   📊 Total architect skills found: {total_architects}")

            # Test Official architect skills
            print("\n3️⃣  Testing Official architect skills...")
            official_filter = page.locator('[data-official="true"]')
            official_filter.click()
            time.sleep(1)

            official_cards = page.locator('.skill-card')
            official_count = official_cards.count()
            print(f"   🏛️ Official architect skills: {official_count}")

            if official_count > 0:
                # Sample official architect skills
                for i in range(min(3, official_count)):
                    card = official_cards.nth(i)
                    name = card.locator('.card-name').inner_text()
                    org = card.locator('.card-org').inner_text()
                    desc = card.locator('.card-desc').inner_text()

                    print(f"\n   📋 Official Architect Skill #{i+1}:")
                    print(f"      Name: {name}")
                    print(f"      Org: {org}")
                    print(f"      Desc: {desc[:60]}...")

                    # Click to see details
                    card.click()
                    time.sleep(0.5)

                    # Get detailed info
                    detail_name = page.locator('.detail-name').inner_text()
                    detail_desc = page.locator('.detail-desc').inner_text()

                    print(f"      🔍 Full Description: {detail_desc[:100]}...")

                    # Check for GitHub link
                    github_link = page.locator('.detail-github a')
                    if github_link.is_visible():
                        github_url = github_link.get_attribute('href')
                        print(f"      🔗 GitHub: {github_url}")

                    # Close modal
                    page.keyboard.press('Escape')
                    time.sleep(0.3)

            # Test Community architect skills
            print(f"\n4️⃣  Testing Community architect skills...")
            community_filter = page.locator('[data-official="false"]')
            community_filter.click()
            time.sleep(1)

            community_cards = page.locator('.skill-card')
            community_count = community_cards.count()
            print(f"   👥 Community architect skills: {community_count}")

            if community_count > 0:
                # Sample community architect skills
                for i in range(min(3, community_count)):
                    card = community_cards.nth(i)
                    name = card.locator('.card-name').inner_text()
                    org = card.locator('.card-org').inner_text()
                    desc = card.locator('.card-desc').inner_text()

                    print(f"\n   📋 Community Architect Skill #{i+1}:")
                    print(f"      Name: {name}")
                    print(f"      Org: {org}")
                    print(f"      Desc: {desc[:60]}...")

                    # Click to see details
                    card.click()
                    time.sleep(0.5)

                    # Get detailed info
                    detail_name = page.locator('.detail-name').inner_text()
                    detail_desc = page.locator('.detail-desc').inner_text()

                    print(f"      🔍 Full Description: {detail_desc[:100]}...")

                    # Check for stars (community skills often have visible stars)
                    stars_elem = page.locator('.detail-stars')
                    if stars_elem.is_visible():
                        stars = stars_elem.inner_text()
                        print(f"      ⭐ Stars: {stars}")

                    # Close modal
                    page.keyboard.press('Escape')
                    time.sleep(0.3)

            # Show comparison summary
            print(f"\n5️⃣  Architect Skills Summary:")
            print(f"   📊 Total: {total_architects}")
            print(f"   🏛️ Official: {official_count}")
            print(f"   👥 Community: {community_count}")
            print(f"   📈 Official %: {official_count/total_architects*100:.1f}%")
            print(f"   📈 Community %: {community_count/total_architects*100:.1f}%")

            # Test switching back and forth between filters
            print(f"\n6️⃣  Testing filter switching...")
            print("   🔄 Switching to Official...")
            official_filter.click()
            time.sleep(0.5)
            official_active = 'active' in (official_filter.get_attribute('class') or '')
            print(f"   ✅ Official filter active: {official_active}")

            print("   🔄 Switching to Community...")
            community_filter.click()
            time.sleep(0.5)
            community_active = 'active' in (community_filter.get_attribute('class') or '')
            print(f"   ✅ Community filter active: {community_active}")

            print("   🔄 Clearing filters (show all)...")
            # Click "All" to show both
            all_filter = page.locator('[data-official=""]')
            if all_filter.is_visible():
                all_filter.click()
                time.sleep(0.5)
                final_count = page.locator('.skill-card').count()
                print(f"   📊 Total architect skills shown: {final_count}")

            print("\n🎉 Architect skills comparison completed!")
            time.sleep(2)

            browser.close()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        print("\n🔄 Shutting down server...")
        proc.terminate()
        proc.wait(timeout=5)

    print("\n✨ Architect Skills Comparison Complete!")
    print("Successfully demonstrated:")
    print("  • Official vs Community skill filtering")
    print("  • Detailed skill inspection")
    print("  • Filter state management")
    print("  • Statistical comparison")
    print("  • Modal interaction patterns")
    print(f"\nArchitect skill ecosystem fully tested! ⚖️")


if __name__ == "__main__":
    test_architect_official_vs_community()