"""
Uber Eats menu scraper using async Playwright.

Scrapes menu items, prices, and categories from Uber Eats restaurant pages.
"""

import asyncio
import random
import re
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass, field

import json

from bs4 import BeautifulSoup

from .stealth_browser import AsyncStealthBrowser, BrowserSessionExpiredError


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
    Async Uber Eats menu scraper using Playwright with stealth measures.
    """

    def __init__(self, browser=None):
        # browser parameter kept for compatibility but ignored
        self._browser: Optional[AsyncStealthBrowser] = None

    async def _get_browser(self) -> AsyncStealthBrowser:
        """Get or create a browser instance."""
        if self._browser is None:
            self._browser = AsyncStealthBrowser(headless=True)
            await self._browser.start()
        return self._browser

    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.stop()
            self._browser = None

    async def _scroll_page(self, page, max_scrolls: int = 5) -> None:
        """Fast scroll to load lazy content. Optimized for 60s session limit."""
        scroll_height = await page.evaluate("document.body.scrollHeight")

        current_position = 0
        scroll_count = 0
        while current_position < scroll_height and scroll_count < max_scrolls:
            scroll_amount = 3000  # Very big jumps for speed
            current_position += scroll_amount
            scroll_count += 1

            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await asyncio.sleep(0.02)  # Minimal scroll delay

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > scroll_height:
                scroll_height = new_height

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")

    async def _dismiss_cookie_banner(self, page) -> None:
        """Try to dismiss cookie consent banner if present."""
        try:
            accept_btn = await page.query_selector('button:has-text("Accept"), button:has-text("Got it"), [data-testid="cookie-banner-accept"]')
            if accept_btn:
                await accept_btn.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape menu items from an Uber Eats restaurant page."""
        import time
        start_time = time.time()

        browser = await self._get_browser()

        # Ensure we have enough session time for a scrape (45s navigation + buffer)
        await browser.ensure_fresh_session(required_time=50)
        print(f"Session remaining: {browser.get_remaining_time():.1f}s")

        result = ScrapeResult(
            restaurant_name="Unknown",
            platform="ubereats",
            items=[],
        )

        async with browser.get_page() as page:
            try:
                print(f"Navigating to: {url}")
                # Reduced timeout for Browserless free tier (60s session limit)
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                remaining_time = browser.get_remaining_time()
                print(f"Page loaded in {time.time() - start_time:.1f}s (session: {remaining_time:.1f}s left)")

                # Check if we have enough time to continue
                if remaining_time < 5:
                    print(f"Session time critically low ({remaining_time:.1f}s), getting content immediately")
                else:
                    # Dismiss cookie banner if present (skip if time is low)
                    if remaining_time > 15:
                        await self._dismiss_cookie_banner(page)

                    # Scroll to load menu items (skip if time is low)
                    if remaining_time > 10:
                        print("Scrolling to load menu items...")
                        # Reduce scrolls if time is limited
                        max_scrolls = 5 if remaining_time > 20 else 2
                        await self._scroll_page(page, max_scrolls=max_scrolls)
                    else:
                        print(f"Skipping scroll due to low session time ({remaining_time:.1f}s)")

                # Get HTML and parse - do this as quickly as possible
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
                # Check if this is a session expiry error and re-raise as specific exception
                if browser._is_session_expired_error(e):
                    raise BrowserSessionExpiredError(f"Session expired during scrape: {e}")

        return result

    def _parse_menu_html(self, html: str) -> list[ScrapedMenuItem]:
        """Parse menu items from Uber Eats HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Try JSON-LD extraction first
        items = self._extract_from_json_ld(soup)
        if items:
            print(f"Extracted {len(items)} items from JSON-LD data")
            return items

        # Fall back to HTML parsing
        print("JSON-LD not found, falling back to HTML parsing")
        return self._parse_menu_from_html(soup)

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> list[ScrapedMenuItem]:
        """Extract menu items from JSON-LD structured data."""
        items = []
        position = 0

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if not isinstance(data, dict):
                    continue

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
        """Fallback HTML parsing for menu items."""
        items = []
        position = 0
        seen_names = set()

        price_pattern = re.compile(r'[£$](\d+(?:\.\d{2})?)')

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

            img = element.find('img')
            if img and img.get('alt'):
                name = img['alt'].strip()

            if not name:
                h3 = element.find('h3')
                if h3:
                    name = h3.get_text(strip=True)

            if not name:
                for span in element.find_all('span'):
                    text = span.get_text(strip=True)
                    if text and 3 < len(text) < 80 and not text.startswith(('£', '$', '#')):
                        name = text
                        break

            if not name or len(name) < 2:
                return None

            price = Decimal("0.00")
            text_content = element.get_text()
            price_match = price_pattern.search(text_content)
            if price_match:
                price = Decimal(price_match.group(1))

            description = None
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


# Backward compatibility alias
SyncUberEatsScraper = UberEatsScraper
