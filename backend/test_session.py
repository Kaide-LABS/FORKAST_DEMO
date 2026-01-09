#!/usr/bin/env python3
"""
Test script for Browserless.io session management.

Tests:
1. Session tracking (age, remaining time)
2. Proactive session renewal
3. UberEats scrape with session logging

Run with: python test_session.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scraper.stealth_browser import AsyncStealthBrowser, BrowserSessionExpiredError
from scraper.ubereats_scraper import UberEatsScraper


async def test_session_tracking():
    """Test basic session tracking functionality."""
    print("=" * 60)
    print("Test 1: Session Tracking")
    print("=" * 60)

    browser = AsyncStealthBrowser(headless=True)

    try:
        # Before starting - no session
        print(f"\nBefore start:")
        print(f"  Session age: {browser.get_session_age():.1f}s")
        print(f"  Remaining time: {browser.get_remaining_time():.1f}s")
        print(f"  Is fresh (30s): {browser.is_session_fresh(30)}")

        # Start browser
        print("\nStarting browser...")
        await browser.start()

        # Immediately after start
        print(f"\nAfter start:")
        print(f"  Session age: {browser.get_session_age():.1f}s")
        print(f"  Remaining time: {browser.get_remaining_time():.1f}s")
        print(f"  Is fresh (30s): {browser.is_session_fresh(30)}")
        print(f"  Is fresh (50s): {browser.is_session_fresh(50)}")

        # Wait a bit and check again
        print("\nWaiting 5 seconds...")
        await asyncio.sleep(5)

        print(f"\nAfter 5 seconds:")
        print(f"  Session age: {browser.get_session_age():.1f}s")
        print(f"  Remaining time: {browser.get_remaining_time():.1f}s")

        print("\n[PASS] Session tracking works correctly")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.stop()


async def test_ensure_fresh_session():
    """Test proactive session renewal."""
    print("\n" + "=" * 60)
    print("Test 2: Ensure Fresh Session")
    print("=" * 60)

    browser = AsyncStealthBrowser(headless=True)

    try:
        # Start browser
        print("\nStarting browser...")
        await browser.start()
        initial_age = browser.get_session_age()
        print(f"Initial session age: {initial_age:.1f}s")

        # Request more time than available (should trigger reconnect)
        print("\nTesting ensure_fresh_session(required_time=65)...")
        print("(This should reconnect since we only have 60s total)")
        await browser.ensure_fresh_session(required_time=65)

        new_age = browser.get_session_age()
        print(f"After ensure_fresh_session:")
        print(f"  Session age: {new_age:.1f}s")
        print(f"  Remaining time: {browser.get_remaining_time():.1f}s")

        if new_age < initial_age + 2:  # Allow for some time passage
            print("\n[PASS] Session was renewed (age reset)")
        else:
            print("\n[WARN] Session may not have been renewed")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.stop()


async def test_ubereats_scrape():
    """Test UberEats scraper with session management."""
    print("\n" + "=" * 60)
    print("Test 3: UberEats Scrape with Session Management")
    print("=" * 60)

    # Sample Uber Eats URL - Chick-fil-A New Orleans
    url = "https://www.ubereats.com/store/chick-fil-a-1200-poydras-street-101/4mK_3OqOSkqk9NRpiLB6Bw?diningMode=DELIVERY"

    print(f"\nTarget URL: {url}")
    print("-" * 60)

    scraper = UberEatsScraper()

    try:
        print("\nScraping menu (watch for session logs)...")
        result = await scraper.scrape(url)

        if result.success:
            print(f"\n[PASS] Scrape successful!")
            print(f"  Restaurant: {result.restaurant_name}")
            print(f"  Items found: {len(result.items)}")

            if result.items:
                print("\n  Sample items:")
                for item in result.items[:5]:
                    print(f"    - {item.name}: ${item.price}")
        else:
            print(f"\n[FAIL] Scrape failed: {result.error_message}")

    except BrowserSessionExpiredError as e:
        print(f"\n[FAIL] Session expired: {e}")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await scraper.close()


async def main():
    """Run all tests."""
    print("\nBrowserless.io Session Management Tests")
    print("=" * 60)

    # Check for BROWSERLESS_TOKEN
    import os
    token = os.getenv("BROWSERLESS_TOKEN")
    if token:
        print(f"BROWSERLESS_TOKEN: {'*' * 8}...{token[-4:]}")
    else:
        print("BROWSERLESS_TOKEN: Not set (will use local browser)")

    # Run tests
    await test_session_tracking()
    await test_ensure_fresh_session()
    await test_ubereats_scrape()

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
