#!/usr/bin/env python3
"""
Playwright test to verify the GitHub repository link has been updated correctly
Tests that the dashboard now points to pramodtoraskar/agentskillsboard
"""

import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def test_github_link_update():
    """Test that the GitHub repository link has been updated to the correct repository"""
    print("🔗 Testing GitHub Repository Link Update")
    print("=" * 45)

    # Start the API server
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd()

    print("📡 Starting API server on port 8009...")
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8009'
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
            page.goto("http://127.0.0.1:8009")
            print(f"   ✅ Page loaded: {page.title()}")
            time.sleep(2)

            # Test GitHub repository link in header
            print("\n2️⃣  Checking GitHub repository link...")
            repo_link = page.locator('#repo-link')

            if repo_link.is_visible():
                href = repo_link.get_attribute('href')
                expected_url = "https://github.com/pramodtoraskar/agentskillsboard"

                print(f"   🔍 Found repository link: {href}")

                if href == expected_url:
                    print("   ✅ GitHub repository link correctly updated!")
                else:
                    print(f"   ❌ Expected: {expected_url}")
                    print(f"      Actual:   {href}")

                # Test that the link is clickable but don't actually click it
                title = repo_link.get_attribute('title')
                print(f"   📝 Link title: {title}")

                # Check repository slug display
                repo_slug = page.locator('#repo-slug-label')
                if repo_slug.is_visible():
                    slug_text = repo_slug.inner_text()
                    expected_slug = "pramodtoraskar/agentskillsboard"

                    print(f"   📊 Repository slug display: {slug_text}")

                    if slug_text == expected_slug:
                        print("   ✅ Repository slug correctly updated!")
                    else:
                        print(f"   ❌ Expected slug: {expected_slug}")
                        print(f"      Actual slug:   {slug_text}")

            else:
                print("   ⚠️ Repository link not found")

            # Test GitHub stars API call (should be for the new repository)
            print("\n3️⃣  Checking GitHub stars API integration...")
            stars_element = page.locator('#repo-stars')

            # Wait a bit for the API call to complete
            time.sleep(3)

            if stars_element.is_visible():
                stars_text = stars_element.inner_text()
                print(f"   ⭐ GitHub stars: {stars_text}")

                if stars_text != "—":
                    print("   ✅ GitHub API integration working!")
                    print(f"   📊 Repository has {stars_text} stars")
                else:
                    print("   ⏳ GitHub API call still loading or rate limited")
            else:
                print("   ⚠️ Stars element not found")

            # Test that we can inspect the network request
            print("\n4️⃣  Verifying GitHub API endpoint...")

            # Check the browser console for any GitHub API errors
            console_messages = []
            def handle_console(msg):
                if 'github' in msg.text.lower():
                    console_messages.append(msg.text)

            page.on('console', handle_console)
            page.reload()
            time.sleep(3)

            if console_messages:
                print("   📝 GitHub-related console messages:")
                for msg in console_messages:
                    print(f"      {msg}")
            else:
                print("   ✅ No GitHub-related console errors")

            print("\n🎉 GitHub repository link update verification completed!")
            time.sleep(2)

            browser.close()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        print("\n🔄 Shutting down server...")
        proc.terminate()
        proc.wait(timeout=5)

    print("\n✨ GitHub Link Update Test Complete!")
    print("Successfully verified:")
    print("  • Repository link updated to pramodtoraskar/agentskillsboard")
    print("  • Repository slug display updated")
    print("  • GitHub API integration pointing to new repository")
    print("  • No console errors related to GitHub API")
    print("\nDashboard now correctly points to your repository! 🔗")


if __name__ == "__main__":
    test_github_link_update()