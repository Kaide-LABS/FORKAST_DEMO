"""
Uber Eats menu scraper using Playwright.

Scrapes menu items, prices, and categories from Uber Eats restaurant pages.
"""

import asyncio
import random
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import json

from bs4 import BeautifulSoup
from playwright.async_api import Page

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
    platform: str = "ubereats"
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    items: list[ScrapedMenuItem] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class UberEatsScraper:
    """
    Uber Eats menu scraper using Playwright with stealth measures.

    No login required - restaurant pages are publicly accessible.
    """

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

    async def _random_delay(self, min_sec: float = 0.1, max_sec: float = 0.3) -> None:
        """Minimal delay for server-side scraping."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _scroll_page(self, page: Page, max_scrolls: int = 10) -> None:
        """Fast scroll to load lazy content. Minimal scrolls for speed."""
        scroll_height = await page.evaluate("document.body.scrollHeight")

        current_position = 0
        scroll_count = 0
        while current_position < scroll_height and scroll_count < max_scrolls:
            scroll_amount = 1500  # Big jumps for speed
            current_position += scroll_amount
            scroll_count += 1

            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await asyncio.sleep(0.05)  # Minimal scroll delay

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > scroll_height:
                scroll_height = new_height

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")

    async def _dismiss_cookie_banner(self, page: Page) -> None:
        """Try to dismiss cookie consent banner if present."""
        try:
            # Look for common accept buttons
            accept_btn = await page.query_selector('button:has-text("Accept"), button:has-text("Got it"), [data-testid="cookie-banner-accept"]')
            if accept_btn:
                await accept_btn.click()
                await self._random_delay(0.5, 1.0)
        except Exception:
            pass  # Ignore if no cookie banner

    async def scrape(self, url: str) -> ScrapeResult:
        """
        Scrape menu items from an Uber Eats restaurant page.

        Args:
            url: Uber Eats restaurant URL

        Returns:
            ScrapeResult with scraped menu items
        """
        browser = await self._get_browser()
        result = ScrapeResult(
            restaurant_name="Unknown",
            platform="ubereats",
            items=[],
        )

        async with browser.get_page() as page:
            try:
                print(f"Navigating to: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(0.5)  # Brief wait for JS

                # Dismiss cookie banner if present
                await self._dismiss_cookie_banner(page)

                # Scroll to load all menu items
                print("Scrolling to load menu items...")
                await self._scroll_page(page)
                await asyncio.sleep(0.3)  # Brief pause after scroll

                # Get HTML and parse
                html = await page.content()

                # Try to get restaurant name from h1
                try:
                    h1 = await page.query_selector('h1')
                    if h1:
                        result.restaurant_name = await h1.text_content() or "Unknown"
                except Exception:
                    pass

                items = self._parse_menu_html(html)
                result.items = items
                result.success = len(items) > 0

                if not items:
                    result.error_message = "No menu items found"
                else:
                    print(f"Found {len(items)} menu items")

            except Exception as e:
                result.success = False
                result.error_message = str(e)
                print(f"Scrape error: {e}")

        return result

    def _parse_menu_html(self, html: str) -> list[ScrapedMenuItem]:
        """
        Parse menu items from Uber Eats HTML.

        First tries JSON-LD structured data (most reliable),
        then falls back to HTML parsing.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Try JSON-LD extraction first (most reliable for categories)
        items = self._extract_from_json_ld(soup)
        if items:
            print(f"Extracted {len(items)} items from JSON-LD data")
            return items

        # Fall back to HTML parsing
        print("JSON-LD not found, falling back to HTML parsing")
        return self._parse_menu_from_html(soup)

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> list[ScrapedMenuItem]:
        """
        Extract menu items from JSON-LD structured data (schema.org format).

        This captures the actual category names from the restaurant's menu.
        """
        items = []
        position = 0

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if not isinstance(data, dict):
                    continue

                # Look for hasMenu -> hasMenuSection structure
                menu = data.get('hasMenu')
                if not menu or 'hasMenuSection' not in menu:
                    continue

                for section in menu['hasMenuSection']:
                    category = section.get('name', 'Uncategorized')
                    menu_items = section.get('hasMenuItem', [])

                    for menu_item in menu_items:
                        name = menu_item.get('name')
                        if not name:
                            continue

                        # Extract price from offers
                        price = Decimal("0.00")
                        offers = menu_item.get('offers', {})
                        if isinstance(offers, dict):
                            price_str = offers.get('price', '0')
                            try:
                                price = Decimal(str(price_str))
                            except:
                                pass

                        description = menu_item.get('description')

                        items.append(ScrapedMenuItem(
                            name=name,
                            price=price,
                            category=category,
                            description=description,
                            position=position,
                        ))
                        position += 1

                if items:
                    return items

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error parsing JSON-LD: {e}")
                continue

        return items

    def _parse_menu_from_html(self, soup: BeautifulSoup) -> list[ScrapedMenuItem]:
        """
        Fallback HTML parsing for menu items.
        """
        items = []
        position = 0
        seen_names = set()

        # Detect currency (£ for UK, $ for US)
        price_pattern = re.compile(r'[£$](\d+(?:\.\d{2})?)')

        # Find all catalog sections
        catalog_sections = soup.find_all(attrs={'data-testid': 'store-catalog-section-vertical-grid'})

        for section in catalog_sections:
            category = None
            parent = section.parent
            for _ in range(5):
                if parent is None:
                    break
                title_elem = parent.find(attrs={'data-testid': 'catalog-section-title'})
                if title_elem:
                    category = title_elem.get_text(strip=True)
                    break
                parent = parent.parent

            store_items = section.find_all(attrs={'data-testid': re.compile(r'^store-item-')})

            for element in store_items:
                item = self._extract_item_from_element(element, position, price_pattern, category)
                if item and item.name not in seen_names:
                    if not self._is_ui_element(item.name):
                        items.append(item)
                        seen_names.add(item.name)
                        position += 1

        # If no sections found, find all store items directly
        if not items:
            store_items = soup.find_all(attrs={'data-testid': re.compile(r'^store-item-')})
            for element in store_items:
                item = self._extract_item_from_element(element, position, price_pattern, None)
                if item and item.name not in seen_names:
                    if not self._is_ui_element(item.name):
                        items.append(item)
                        seen_names.add(item.name)
                        position += 1

        return items

    def _is_ui_element(self, name: str) -> bool:
        """Check if name looks like a UI element rather than menu item."""
        ui_patterns = [
            'sign up', 'log in', 'sign in', 'view cart', 'checkout',
            'delivery fee', 'service fee', 'get it delivered',
            'enter your address', 'group order', 'schedule',
        ]
        name_lower = name.lower().strip()

        if len(name_lower) < 3:
            return True

        for pattern in ui_patterns:
            if pattern in name_lower:
                return True

        return False

    def _extract_item_from_element(self, element, position: int, price_pattern, category: Optional[str] = None) -> Optional[ScrapedMenuItem]:
        """Extract menu item data from a BeautifulSoup element."""
        try:
            name = None

            # Method 1: Get name from image alt attribute
            img = element.find('img')
            if img and img.get('alt'):
                name = img['alt'].strip()

            # Method 2: Get from h3 if no image alt
            if not name:
                h3 = element.find('h3')
                if h3:
                    name = h3.get_text(strip=True)

            # Method 3: Try first significant span
            if not name:
                for span in element.find_all('span'):
                    text = span.get_text(strip=True)
                    if text and 3 < len(text) < 80 and not text.startswith(('£', '$', '#')):
                        name = text
                        break

            if not name or len(name) < 2:
                return None

            # Extract price
            price = Decimal("0.00")
            text_content = element.get_text()
            price_match = price_pattern.search(text_content)
            if price_match:
                price = Decimal(price_match.group(1))

            # Try to get description (usually in a smaller text element)
            description = None
            # Look for calorie info or description text
            cal_match = re.search(r'(\d+)\s*Cal', text_content)
            if cal_match:
                description = f"{cal_match.group(1)} calories"

            return ScrapedMenuItem(
                name=name,
                price=price,
                category=category,
                description=description,
                position=position,
            )

        except Exception as e:
            print(f"Error extracting item: {e}")
            return None

    async def debug_dump(self, url: str, output_file: str = "debug_ubereats.html") -> str:
        """
        Navigate to an Uber Eats restaurant page and dump the full HTML for inspection.
        """
        browser = await self._get_browser()
        output_path = Path(output_file)

        async with browser.get_page() as page:
            try:
                print(f"Navigating to: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await self._random_delay(3.0, 5.0)
                await self._scroll_page(page)

                html_content = await page.content()
                output_path.write_text(html_content, encoding="utf-8")
                print(f"HTML dumped to: {output_path.absolute()}")

                return str(output_path.absolute())

            except Exception as e:
                error_html = f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"
                output_path.write_text(error_html, encoding="utf-8")
                print(f"Error during dump: {e}")
                return str(output_path.absolute())
