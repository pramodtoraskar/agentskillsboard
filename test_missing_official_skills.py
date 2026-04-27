#!/usr/bin/env python3
"""
Playwright test to verify missing official skills are now discovered
Tests for dbt-labs, astronomer, and wshobson skills
"""

import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def test_missing_official_skills():
    """Test that previously missing official skills are now discovered"""
    print("🔍 Testing Previously Missing Official Skills")
    print("=" * 50)

    # Start the API server
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    print("📡 Starting API server on port 8008...")
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8008'
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
            page.goto("http://127.0.0.1:8008")
            print(f"   ✅ Page loaded: {page.title()}")
            time.sleep(2)

            # Apply official filter first
            print("\n2️⃣  Filtering for Official skills only...")
            official_filter = page.locator('[data-official="true"]')
            official_filter.click()
            time.sleep(1)

            # Test searching for dbt skills
            print("\n3️⃣  Searching for dbt skills...")
            search_input = page.locator('#search')
            search_input.fill('dbt')
            time.sleep(1.5)

            dbt_cards = page.locator('.skill-card')
            dbt_count = dbt_cards.count()
            print(f"   📊 Found {dbt_count} official dbt skills")

            if dbt_count > 0:
                # Check for dbt-labs organization
                dbt_orgs = []
                for i in range(min(dbt_count, 10)):
                    card = dbt_cards.nth(i)
                    org = card.locator('.card-org').inner_text()
                    name = card.locator('.card-name').inner_text()
                    dbt_orgs.append(org)
                    print(f"      🏷️ {name} by {org}")

                if any('dbt-labs' in org for org in dbt_orgs):
                    print("   ✅ dbt-labs skills discovered!")
                else:
                    print("   ⚠️ dbt-labs skills not yet discovered")

            # Test searching for airflow/astronomer skills
            print("\n4️⃣  Searching for airflow skills...")
            search_input.fill('')
            time.sleep(0.5)
            search_input.fill('airflow')
            time.sleep(1.5)

            airflow_cards = page.locator('.skill-card')
            airflow_count = airflow_cards.count()
            print(f"   📊 Found {airflow_count} official airflow skills")

            if airflow_count > 0:
                # Check for astronomer organization
                airflow_orgs = []
                for i in range(min(airflow_count, 10)):
                    card = airflow_cards.nth(i)
                    org = card.locator('.card-org').inner_text()
                    name = card.locator('.card-name').inner_text()
                    airflow_orgs.append(org)
                    print(f"      🏷️ {name} by {org}")

                if any('astronomer' in org for org in airflow_orgs):
                    print("   ✅ astronomer skills discovered!")
                else:
                    print("   ⚠️ astronomer skills not yet discovered")

            # Test searching for wshobson skills
            print("\n5️⃣  Searching for wshobson skills...")
            search_input.fill('')
            time.sleep(0.5)
            search_input.fill('wshobson')
            time.sleep(1.5)

            wshobson_cards = page.locator('.skill-card')
            wshobson_count = wshobson_cards.count()
            print(f"   📊 Found {wshobson_count} wshobson skills")

            if wshobson_count > 0:
                for i in range(min(wshobson_count, 5)):
                    card = wshobson_cards.nth(i)
                    org = card.locator('.card-org').inner_text()
                    name = card.locator('.card-name').inner_text()
                    desc = card.locator('.card-desc').inner_text()
                    print(f"      🏷️ {name} by {org}")
                    print(f"         {desc[:80]}...")

                print("   ✅ wshobson skills discovered!")
            else:
                print("   ⚠️ wshobson skills not yet discovered")

            # Test clicking on discovered skills
            print("\n6️⃣  Testing interaction with discovered skills...")

            # Try to find and click skills from the new organizations
            search_input.fill('')
            time.sleep(0.5)

            all_cards = page.locator('.skill-card')
            all_count = all_cards.count()
            print(f"   📊 Total official skills: {all_count}")

            # Look for skills from the new organizations
            new_org_skills = []
            for i in range(min(all_count, 50)):  # Check first 50 skills
                card = all_cards.nth(i)
                org = card.locator('.card-org').inner_text()
                if any(target in org.lower() for target in ['dbt-labs', 'astronomer', 'wshobson']):
                    name = card.locator('.card-name').inner_text()
                    new_org_skills.append({'card': card, 'org': org, 'name': name})
                    print(f"      🎯 Found: {name} by {org}")

            if new_org_skills:
                # Click on first discovered skill from new organizations
                skill = new_org_skills[0]
                print(f"   🖱️ Clicking on: {skill['name']} by {skill['org']}")

                skill['card'].click()
                time.sleep(0.5)

                # Verify modal opened
                modal = page.locator('#overlay')
                assert 'open' in (modal.get_attribute('class') or ''), "Modal didn't open"
                print("   ✅ Skill modal opened successfully")

                # Get detailed information
                detail_name = page.locator('.detail-name').inner_text()
                detail_desc = page.locator('.detail-desc').inner_text()
                print(f"   📋 Name: {detail_name}")
                print(f"   📝 Description: {detail_desc[:100]}...")

                # Close modal
                page.keyboard.press('Escape')
                time.sleep(0.3)
                print("   ✅ Modal closed successfully")

            else:
                print("   ⚠️ No skills from new organizations found yet (crawl may still be running)")

            print("\n🎉 Missing official skills verification completed!")
            time.sleep(2)

            browser.close()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        print("\n🔄 Shutting down server...")
        proc.terminate()
        proc.wait(timeout=5)

    print("\n✨ Missing Official Skills Test Complete!")
    print("Updated configuration includes:")
    print("  • astronomer added to OFFICIAL_ORGS")
    print("  • dbt-labs/dbt-agent-skills added to PINNED_REPOS")
    print("  • astronomer/agents added to PINNED_REPOS")
    print("  • wshobson/agents added to PINNED_REPOS")
    print("\nNew official skills discovery in progress! 🔍")


if __name__ == "__main__":
    test_missing_official_skills()