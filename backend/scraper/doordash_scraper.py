import asyncio
import random
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from .stealth_browser import StealthBrowser


@dataclass
class ScrapedMenuItem:
    """Data class for a scraped menu item."""
    name: str
    price: Decimal
    category: Optional[str] = None
    description: Optional[str] = None
    is_available: bool = True
    position: int = 0


@dataclass
class ScrapeResult:
    """Result of a scraping operation."""
    restaurant_name: str
    platform: str = "doordash"
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    items: list[ScrapedMenuItem] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class DoorDashScraper:
    """
    DoorDash menu scraper using Playwright with stealth measures.

    Note: Before parsing, use debug_dump() to inspect the current DOM structure
    and update selectors as needed, since DoorDash frequently changes their UI.
    """

    # These selectors are placeholders - use debug_dump() to find current ones
    # Updated selectors will need to be determined from the actual HTML dump
    SELECTORS = {
        "restaurant_name": "[data-testid='StoreHeader'] h1, .StoreHeader__name, h1",
        "menu_section": "[data-testid='MenuSection'], .menu-section, section",
        "category_name": "[data-testid='CategoryHeader'], .category-header h2, h2",
        "menu_item": "[data-testid='MenuItem'], .menu-item, [data-anchor-id]",
        "item_name": "[data-testid='MenuItemName'], .menu-item-name, h3, span",
        "item_price": "[data-testid='MenuItemPrice'], .menu-item-price, span[class*='price']",
        "item_description": "[data-testid='MenuItemDescription'], .menu-item-description, p",
    }

    def __init__(self, browser: Optional[StealthBrowser] = None):
        self._browser = browser
        self._owns_browser = browser is None

    async def _get_browser(self) -> StealthBrowser:
        """Get or create a browser instance."""
        if self._browser is None:
            self._browser = StealthBrowser(headless=True)
            await self._browser.start()
        return self._browser

    async def close(self) -> None:
        """Close the browser if we own it."""
        if self._owns_browser and self._browser:
            await self._browser.stop()
            self._browser = None

    async def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """Add random delay to appear more human-like."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _scroll_page(self, page: Page) -> None:
        """Scroll through the page to load lazy content."""
        # Get page height
        scroll_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")

        current_position = 0
        while current_position < scroll_height:
            # Scroll in chunks
            scroll_amount = random.randint(300, 500)
            current_position += scroll_amount

            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await self._random_delay(0.3, 0.7)

            # Check if height changed (dynamic loading)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > scroll_height:
                scroll_height = new_height

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await self._random_delay(0.5, 1.0)

    async def debug_dump(self, url: str, output_file: str = "debug_doordash.html") -> str:
        """
        Navigate to a DoorDash restaurant page and dump the full HTML for inspection.

        Use this to determine the correct CSS selectors for menu items, prices, etc.
        The DOM structure may change frequently, so this helps identify current selectors.

        Args:
            url: DoorDash restaurant URL (e.g., https://www.doordash.com/store/restaurant-name-123)
            output_file: Path to save the HTML dump

        Returns:
            Path to the saved HTML file
        """
        browser = await self._get_browser()
        output_path = Path(output_file)

        async with browser.get_page() as page:
            print(f"Navigating to: {url}")

            try:
                # Navigate with extended timeout
                await page.goto(url, wait_until="networkidle", timeout=60000)
                print("Page loaded, waiting for content...")

                # Wait a bit for JS to render
                await self._random_delay(3.0, 5.0)

                # Scroll to load lazy content
                print("Scrolling to load all content...")
                await self._scroll_page(page)

                # Wait for menu content to be visible
                try:
                    await page.wait_for_selector(
                        "[data-testid], [data-anchor-id], .menu, section",
                        timeout=10000
                    )
                except PlaywrightTimeout:
                    print("Warning: Could not find expected menu selectors, dumping page anyway")

                # Get the full HTML
                html_content = await page.content()

                # Save to file
                output_path.write_text(html_content, encoding="utf-8")
                print(f"HTML dumped to: {output_path.absolute()}")

                # Also try to identify some useful elements
                await self._print_potential_selectors(page)

                return str(output_path.absolute())

            except Exception as e:
                error_html = f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"
                output_path.write_text(error_html, encoding="utf-8")
                print(f"Error during scrape: {e}")
                return str(output_path.absolute())

    async def _print_potential_selectors(self, page: Page) -> None:
        """Print potential selectors found on the page for debugging."""
        print("\n--- Potential Selectors Found ---")

        # Check for common DoorDash patterns
        checks = [
            ("data-testid attributes", "[data-testid]"),
            ("data-anchor-id attributes", "[data-anchor-id]"),
            ("h1 elements", "h1"),
            ("h2 elements", "h2"),
            ("h3 elements", "h3"),
            ("Spans with price patterns", "span"),
            ("Sections", "section"),
            ("Buttons", "button"),
        ]

        for name, selector in checks:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"  {name}: {count} found")
                    # Get first few examples
                    if count <= 5:
                        for i in range(count):
                            element = page.locator(selector).nth(i)
                            text = await element.text_content()
                            if text:
                                text = text.strip()[:50]
                                print(f"    - {text}")
            except Exception:
                pass

        print("--- End of Selectors ---\n")

    async def scrape(self, url: str) -> ScrapeResult:
        """
        Scrape menu items from a DoorDash restaurant page.

        Note: Run debug_dump() first to verify/update selectors for current DOM structure.

        Args:
            url: DoorDash restaurant URL

        Returns:
            ScrapeResult with scraped menu items
        """
        browser = await self._get_browser()
        result = ScrapeResult(
            restaurant_name="Unknown",
            platform="doordash",
            items=[],
        )

        async with browser.get_page() as page:
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await self._random_delay(2.0, 4.0)
                await self._scroll_page(page)

                # Get HTML and parse
                html = await page.content()
                items = self._parse_menu_html(html)
                result.items = items
                result.success = True

            except Exception as e:
                result.success = False
                result.error_message = str(e)

        return result

    def _parse_menu_html(self, html: str) -> list[ScrapedMenuItem]:
        """
        Parse menu items from HTML.

        This is a placeholder implementation. After running debug_dump(),
        update the selectors and parsing logic based on actual DOM structure.
        """
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # This parsing logic needs to be updated based on debug_dump() output
        # The following is a generic attempt that may not work with current DOM

        # Try to find menu items using various patterns
        position = 0

        # Pattern 1: Look for data-testid elements
        for element in soup.select("[data-testid*='MenuItem'], [data-testid*='menu-item']"):
            item = self._extract_item_from_element(element, position)
            if item:
                items.append(item)
                position += 1

        # Pattern 2: Look for elements with price patterns
        if not items:
            for element in soup.find_all(attrs={"data-anchor-id": True}):
                item = self._extract_item_from_element(element, position)
                if item:
                    items.append(item)
                    position += 1

        return items

    def _extract_item_from_element(self, element, position: int) -> Optional[ScrapedMenuItem]:
        """Extract menu item data from a BeautifulSoup element."""
        try:
            # Try to find name
            name_elem = (
                element.select_one("h3") or
                element.select_one("h4") or
                element.select_one("[class*='name']") or
                element.select_one("span")
            )
            if not name_elem:
                return None

            name = name_elem.get_text(strip=True)
            if not name or len(name) < 2:
                return None

            # Try to find price
            price = Decimal("0.00")
            price_text = element.get_text()
            import re
            price_match = re.search(r'\$(\d+(?:\.\d{2})?)', price_text)
            if price_match:
                price = Decimal(price_match.group(1))

            # Try to find description
            description = None
            desc_elem = element.select_one("p, [class*='description']")
            if desc_elem:
                description = desc_elem.get_text(strip=True)

            return ScrapedMenuItem(
                name=name,
                price=price,
                description=description,
                position=position,
            )

        except Exception:
            return None
