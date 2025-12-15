#!/usr/bin/env python3
"""
Test script for the DoorDash scraper.

This script demonstrates how to:
1. Dump HTML from a DoorDash restaurant page for selector inspection
2. Parse menu items once selectors are confirmed

Run with: python test_scraper.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper import DoorDashScraper, StealthBrowser


# Sample DoorDash URLs for Austin burger joints
# These are example URLs - replace with actual restaurant URLs
SAMPLE_URLS = [
    # Austin burger restaurants on DoorDash
    "https://www.doordash.com/store/p-terry's-burger-stand-austin-25611/",
    "https://www.doordash.com/store/hopdoddy-burger-bar-austin-85/",
    "https://www.doordash.com/store/shake-shack-austin-1128547/",
]


async def test_debug_dump():
    """
    Test the debug_dump functionality to save HTML for inspection.

    This allows us to examine the current DOM structure and determine
    the correct CSS selectors for menu items, prices, and categories.
    """
    print("=" * 60)
    print("DoorDash Scraper - Debug Dump Test")
    print("=" * 60)

    # Use the first sample URL
    url = SAMPLE_URLS[0]
    print(f"\nTarget URL: {url}")
    print("-" * 60)

    browser = StealthBrowser(headless=True)
    scraper = DoorDashScraper(browser)

    try:
        await browser.start()

        print("\nStarting debug dump...")
        print("This will navigate to the page and save the HTML.")
        print("Please wait, this may take 30-60 seconds...\n")

        output_file = await scraper.debug_dump(url, "debug_doordash.html")

        print("\n" + "=" * 60)
        print("DEBUG DUMP COMPLETE")
        print("=" * 60)
        print(f"\nHTML dumped to: {output_file}")
        print("\nNext steps:")
        print("1. Open 'debug_doordash.html' in a browser")
        print("2. Use browser DevTools to inspect the DOM structure")
        print("3. Look for patterns to identify:")
        print("   - Menu item containers")
        print("   - Item names (usually h3 or span elements)")
        print("   - Item prices (often in span with $ prefix)")
        print("   - Category headers (usually h2 elements)")
        print("   - Item descriptions (usually p elements)")
        print("\n4. Update the SELECTORS in doordash_scraper.py")
        print("5. Re-run with parse_items() to verify extraction")

    except Exception as e:
        print(f"\nError during debug dump: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.stop()


async def test_parse_items():
    """
    Test parsing menu items from a DoorDash page.

    Note: Run test_debug_dump() first to verify selectors are correct
    for the current DOM structure.
    """
    print("=" * 60)
    print("DoorDash Scraper - Parse Items Test")
    print("=" * 60)

    url = SAMPLE_URLS[0]
    print(f"\nTarget URL: {url}")
    print("-" * 60)

    browser = StealthBrowser(headless=True)
    scraper = DoorDashScraper(browser)

    try:
        await browser.start()

        print("\nScraping menu items...")
        result = await scraper.scrape(url)

        if result.success:
            print(f"\nRestaurant: {result.restaurant_name}")
            print(f"Platform: {result.platform}")
            print(f"Scraped at: {result.scraped_at}")
            print(f"Items found: {len(result.items)}")

            if result.items:
                print("\nSample items:")
                for i, item in enumerate(result.items[:10]):
                    print(f"  {i+1}. {item.name}")
                    print(f"     Price: ${item.price}")
                    if item.category:
                        print(f"     Category: {item.category}")
                    if item.description:
                        print(f"     Description: {item.description[:50]}...")
            else:
                print("\nNo items extracted!")
                print("This likely means the selectors need to be updated.")
                print("Run test_debug_dump() and inspect the HTML first.")
        else:
            print(f"\nScraping failed: {result.error_message}")

    except Exception as e:
        print(f"\nError during parsing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.stop()


async def main():
    """Main entry point for the test script."""
    print("\nDoorDash Scraper Test Script")
    print("============================\n")
    print("Options:")
    print("  1. Run debug_dump (saves HTML for inspection)")
    print("  2. Run parse test (extracts menu items)")
    print("  3. Run both")
    print()

    # Default to debug dump for initial testing
    choice = "1"

    if len(sys.argv) > 1:
        choice = sys.argv[1]

    if choice == "1":
        await test_debug_dump()
    elif choice == "2":
        await test_parse_items()
    elif choice == "3":
        await test_debug_dump()
        print("\n" + "=" * 60 + "\n")
        await test_parse_items()
    else:
        print(f"Unknown option: {choice}")
        print("Usage: python test_scraper.py [1|2|3]")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# =============================================================================
# COMMENTED OUT: Full parsing logic to be implemented after selectors confirmed
# =============================================================================
#
# Once you've run debug_dump() and identified the correct selectors,
# update the SELECTORS dictionary in doordash_scraper.py and then
# uncomment and modify the parsing logic as needed.
#
# Example of expected output after proper selector configuration:
#
# async def test_full_scrape():
#     """Full scrape test with proper selectors."""
#     scraper = DoorDashScraper()
#
#     try:
#         result = await scraper.scrape(SAMPLE_URLS[0])
#
#         if result.success:
#             for item in result.items:
#                 print(f"Item: {item.name}")
#                 print(f"  Price: ${item.price}")
#                 print(f"  Category: {item.category}")
#                 print(f"  Available: {item.is_available}")
#
#             # Save to database
#             from services import ingest_menu_data
#             await ingest_menu_data(competitor_id="some-uuid", data=result)
#
#     finally:
#         await scraper.close()
