import asyncio
import os
import random
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from .stealth_browser import StealthBrowser


# Cookie storage path
COOKIES_FILE = Path(__file__).parent / ".doordash_cookies.json"


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
    DoorDash menu scraper using Playwright with stealth measures and authentication.

    Requires environment variables:
    - DOORDASH_EMAIL: DoorDash account email
    - DOORDASH_PASSWORD: DoorDash account password
    """

    LOGIN_URL = "https://identity.doordash.com/auth/user/login"

    def __init__(self, browser: Optional[StealthBrowser] = None):
        self._browser = browser
        self._owns_browser = browser is None
        self._context = None
        self._is_logged_in = False

    async def _get_browser(self) -> StealthBrowser:
        """Get or create a browser instance."""
        if self._browser is None:
            self._browser = StealthBrowser(headless=True)
            await self._browser.start()
        return self._browser

    async def close(self) -> None:
        """Close the browser if we own it."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._owns_browser and self._browser:
            await self._browser.stop()
            self._browser = None

    async def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """Add random delay to appear more human-like."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _scroll_page(self, page: Page) -> None:
        """Scroll through the page to load lazy content."""
        scroll_height = await page.evaluate("document.body.scrollHeight")

        current_position = 0
        while current_position < scroll_height:
            scroll_amount = random.randint(300, 500)
            current_position += scroll_amount

            await page.evaluate(f"window.scrollTo(0, {current_position})")
            await self._random_delay(0.3, 0.7)

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height > scroll_height:
                scroll_height = new_height

        await page.evaluate("window.scrollTo(0, 0)")
        await self._random_delay(0.5, 1.0)

    def _save_cookies(self, cookies: list) -> None:
        """Save cookies to file for reuse."""
        try:
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f)
            print(f"Cookies saved to {COOKIES_FILE}")
        except Exception as e:
            print(f"Failed to save cookies: {e}")

    def _load_cookies(self) -> Optional[list]:
        """Load cookies from file if available."""
        try:
            if COOKIES_FILE.exists():
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                print(f"Loaded {len(cookies)} cookies from file")
                return cookies
        except Exception as e:
            print(f"Failed to load cookies: {e}")
        return None

    async def _check_if_logged_in(self, page: Page) -> bool:
        """Check if we're currently logged into DoorDash."""
        try:
            # Try to find logged-in indicators
            # DoorDash shows account menu when logged in
            account_indicator = await page.query_selector('[data-testid="AccountMenu"], [aria-label*="Account"], [data-testid="user-avatar"]')
            if account_indicator:
                return True

            # Check for login button (indicates NOT logged in)
            login_button = await page.query_selector('button:has-text("Sign In"), a:has-text("Sign In"), button:has-text("Log In")')
            if login_button:
                return False

            return False
        except Exception:
            return False

    async def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Log into DoorDash account.

        Args:
            email: DoorDash email (or uses DOORDASH_EMAIL env var)
            password: DoorDash password (or uses DOORDASH_PASSWORD env var)

        Returns:
            True if login successful, False otherwise
        """
        email = email or os.environ.get("DOORDASH_EMAIL")
        password = password or os.environ.get("DOORDASH_PASSWORD")

        if not email or not password:
            print("DoorDash credentials not provided")
            return False

        browser = await self._get_browser()

        # Create a persistent context
        if self._context is None:
            self._context = await browser.create_context()

            # Try to load saved cookies
            saved_cookies = self._load_cookies()
            if saved_cookies:
                await self._context.add_cookies(saved_cookies)
                print("Added saved cookies to context")

        page = await self._context.new_page()

        try:
            # First check if already logged in by visiting DoorDash
            print("Checking login status...")
            await page.goto("https://www.doordash.com", wait_until="domcontentloaded", timeout=60000)
            await self._random_delay(2.0, 3.0)

            if await self._check_if_logged_in(page):
                print("Already logged in via cookies!")
                self._is_logged_in = True
                await page.close()
                return True

            # Need to log in
            print(f"Navigating to login page...")
            await page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            await self._random_delay(2.0, 4.0)

            # Fill in email
            print("Entering email...")
            email_input = await page.wait_for_selector('input[type="email"], input[name="email"], input[autocomplete="email"]', timeout=15000)
            if email_input:
                await email_input.click()
                await self._random_delay(0.3, 0.5)
                await email_input.fill(email)
                await self._random_delay(0.5, 1.0)

            # Fill in password
            print("Entering password...")
            password_input = await page.wait_for_selector('input[type="password"], input[name="password"]', timeout=10000)
            if password_input:
                await password_input.click()
                await self._random_delay(0.3, 0.5)
                await password_input.fill(password)
                await self._random_delay(0.5, 1.0)

            # Click submit button
            print("Submitting login form...")
            submit_button = await page.query_selector('button[type="submit"], button:has-text("Sign In"), button:has-text("Log In"), button:has-text("Continue")')
            if submit_button:
                await submit_button.click()
            else:
                # Try pressing Enter
                await page.keyboard.press("Enter")

            # Wait for navigation/login to complete
            print("Waiting for login to complete...")
            await self._random_delay(3.0, 5.0)

            # Check for successful login - should redirect to DoorDash
            try:
                await page.wait_for_url("**/doordash.com/**", timeout=30000)
                print("Redirected to DoorDash!")
            except PlaywrightTimeout:
                # Check if we're still on login page (might have error)
                current_url = page.url
                print(f"Current URL after login attempt: {current_url}")

                # Check for error messages
                error_elem = await page.query_selector('[data-testid="error-message"], .error, [role="alert"]')
                if error_elem:
                    error_text = await error_elem.text_content()
                    print(f"Login error: {error_text}")
                    await page.close()
                    return False

            # Verify we're logged in
            await self._random_delay(2.0, 3.0)
            if await self._check_if_logged_in(page):
                print("Login successful!")
                self._is_logged_in = True

                # Save cookies for future use
                cookies = await self._context.cookies()
                self._save_cookies(cookies)

                await page.close()
                return True
            else:
                print("Login verification failed")
                await page.close()
                return False

        except Exception as e:
            print(f"Login error: {e}")
            try:
                await page.close()
            except:
                pass
            return False

    async def scrape(self, url: str) -> ScrapeResult:
        """
        Scrape menu items from a DoorDash restaurant page.

        Will attempt to login if not already authenticated.

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

        # Ensure we're logged in
        if not self._is_logged_in:
            print("Not logged in, attempting login...")
            login_success = await self.login()
            if not login_success:
                print("Login failed, attempting scrape without auth...")

        # Create context if not exists
        if self._context is None:
            self._context = await browser.create_context()
            saved_cookies = self._load_cookies()
            if saved_cookies:
                await self._context.add_cookies(saved_cookies)

        page = await self._context.new_page()

        try:
            print(f"Navigating to restaurant page: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await self._random_delay(3.0, 5.0)

            # Scroll to load all menu items
            print("Scrolling to load menu items...")
            await self._scroll_page(page)
            await self._random_delay(1.0, 2.0)

            # Get HTML and parse
            html = await page.content()

            # Try to get restaurant name
            try:
                name_elem = await page.query_selector('h1, [data-testid="StoreHeader"] span')
                if name_elem:
                    result.restaurant_name = await name_elem.text_content() or "Unknown"
            except:
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
        finally:
            await page.close()

        return result

    def _parse_menu_html(self, html: str) -> list[ScrapedMenuItem]:
        """
        Parse menu items from DoorDash HTML.
        """
        soup = BeautifulSoup(html, "html.parser")
        items = []
        position = 0
        current_category = None

        # DoorDash menu structure: categories with items inside
        # Look for menu sections/categories

        # Try to find category headers and their items
        for section in soup.find_all(['section', 'div'], attrs={'data-testid': True}):
            testid = section.get('data-testid', '')

            # Check if this is a category header
            if 'category' in testid.lower() or 'header' in testid.lower():
                header = section.find(['h2', 'h3', 'span'])
                if header:
                    current_category = header.get_text(strip=True)
                    continue

        # Look for menu item elements with various patterns
        item_selectors = [
            '[data-testid*="MenuItem"]',
            '[data-testid*="menu-item"]',
            '[data-anchor-id*="MenuItem"]',
            'button[data-testid]',  # Menu items are often buttons
        ]

        seen_names = set()  # Avoid duplicates

        for selector in item_selectors:
            for element in soup.select(selector):
                item = self._extract_item_from_element(element, position, current_category)
                if item and item.name not in seen_names:
                    # Filter out UI elements
                    if not self._is_ui_element(item.name):
                        items.append(item)
                        seen_names.add(item.name)
                        position += 1

        # Fallback: look for price patterns and work backwards
        if len(items) < 3:
            import re
            for element in soup.find_all(string=re.compile(r'\$\d+\.\d{2}')):
                parent = element.find_parent(['div', 'button', 'a'])
                if parent:
                    item = self._extract_item_from_element(parent, position, current_category)
                    if item and item.name not in seen_names and not self._is_ui_element(item.name):
                        items.append(item)
                        seen_names.add(item.name)
                        position += 1

        return items

    def _is_ui_element(self, name: str) -> bool:
        """Check if name looks like a UI element rather than menu item."""
        ui_patterns = [
            'sign up', 'log in', 'sign in', 'group order', 'see more', 'see less',
            'items in cart', 'delivery fee', 'view cart', 'checkout', 'add to cart',
            'schedule', 'asap', 'pickup only', 'delivery', 'featured', 'popular',
            'most ordered', 'previous', 'next', '$0 delivery', 'promo', 'free delivery'
        ]
        name_lower = name.lower().strip()

        # Too short is suspicious
        if len(name_lower) < 3:
            return True

        # Check against patterns
        for pattern in ui_patterns:
            if pattern in name_lower:
                return True

        # Pure numbers or very short
        if name_lower.replace('$', '').replace('.', '').isdigit():
            return True

        return False

    def _extract_item_from_element(self, element, position: int, category: Optional[str] = None) -> Optional[ScrapedMenuItem]:
        """Extract menu item data from a BeautifulSoup element."""
        import re

        try:
            # Try to find name - usually in h3, h4, or prominent span
            name = None
            for tag in ['h3', 'h4', 'span', 'p']:
                name_elem = element.find(tag)
                if name_elem:
                    text = name_elem.get_text(strip=True)
                    # Name should be reasonable length
                    if text and 3 < len(text) < 100:
                        name = text
                        break

            if not name:
                # Try getting first significant text
                all_text = element.get_text(separator='|', strip=True)
                parts = [p.strip() for p in all_text.split('|') if p.strip()]
                for part in parts:
                    if 3 < len(part) < 100 and not part.startswith('$'):
                        name = part
                        break

            if not name:
                return None

            # Try to find price
            price = Decimal("0.00")
            price_text = element.get_text()
            price_match = re.search(r'\$(\d+(?:\.\d{2})?)', price_text)
            if price_match:
                price = Decimal(price_match.group(1))

            # Try to find description
            description = None
            desc_elem = element.find('p') or element.find(class_=re.compile(r'description|desc', re.I))
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if desc_text and desc_text != name:
                    description = desc_text

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

    async def debug_dump(self, url: str, output_file: str = "debug_doordash.html") -> str:
        """
        Navigate to a DoorDash restaurant page and dump the full HTML for inspection.
        """
        browser = await self._get_browser()
        output_path = Path(output_file)

        # Ensure logged in
        if not self._is_logged_in:
            await self.login()

        if self._context is None:
            self._context = await browser.create_context()

        page = await self._context.new_page()

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
        finally:
            await page.close()
