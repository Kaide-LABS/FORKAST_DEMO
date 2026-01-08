"""
Stealth browser wrapper using Browserless.io for fast, reliable scraping.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Optional, Callable, TypeVar, Awaitable, TYPE_CHECKING
from contextlib import asynccontextmanager

T = TypeVar('T')

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright


class BrowserlessRateLimitError(Exception):
    """Raised when Browserless.io rate limit is hit."""
    pass


class BrowserConnectionError(Exception):
    """Raised when browser connection fails."""
    pass


class BrowserSessionExpiredError(Exception):
    """Raised when Browserless session has expired (60s timeout)."""
    pass


# Pool of realistic user agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


class AsyncStealthBrowser:
    """
    An async stealth browser using Browserless.io for fast browser access.
    Falls back to local Playwright if no Browserless token is configured.
    """

    def __init__(self, headless: bool = True):
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browserless_token = os.getenv("BROWSERLESS_TOKEN")

        # Session management for Browserless.io 60s timeout
        self._session_created_at: Optional[float] = None
        self._session_timeout_seconds: int = 60
        self._session_buffer_seconds: int = 20  # Reconnect when 20s remaining
        self._reconnect_delay_seconds: float = 2.0  # Delay between reconnections

    def _get_random_user_agent(self) -> str:
        return random.choice(USER_AGENTS)

    def _get_random_viewport(self) -> dict:
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
        ]
        return random.choice(viewports)

    def get_session_age(self) -> float:
        """Returns seconds since session was created. Returns 0 if no session."""
        if self._session_created_at is None:
            return 0.0
        return time.time() - self._session_created_at

    def get_remaining_time(self) -> float:
        """Returns estimated seconds until session expires. Returns 0 if no session."""
        if self._session_created_at is None:
            return 0.0
        elapsed = time.time() - self._session_created_at
        remaining = self._session_timeout_seconds - elapsed
        return max(0.0, remaining)

    def is_session_fresh(self, required_time: int = 30) -> bool:
        """Check if session has at least required_time seconds remaining."""
        if not self._browserless_token:
            return True  # Local browser has no timeout
        if self._browser is None:
            return False  # No session
        return self.get_remaining_time() >= required_time

    async def ensure_fresh_session(self, required_time: int = 30) -> None:
        """
        Ensure session has at least required_time seconds remaining.
        If session is too old, reconnect to get a fresh 60s session.
        """
        if not self._browserless_token:
            # Local browser - just ensure it's started
            await self.start()
            return

        if self._browser is None:
            await self.start()
            return

        remaining = self.get_remaining_time()
        if remaining < required_time:
            print(f"Session has only {remaining:.1f}s remaining, reconnecting for fresh session...")
            await self.stop()
            await asyncio.sleep(self._reconnect_delay_seconds)  # Brief delay to avoid rate limits
            await self.start()
            print(f"Fresh session created with {self.get_remaining_time():.1f}s remaining")

    def _is_session_expired_error(self, error: Exception) -> bool:
        """
        Check if an error indicates the Browserless session has expired.
        Returns True for session expiry, False for other errors.
        """
        error_str = str(error).lower()
        session_expired_patterns = [
            "target closed",
            "protocol error",
            "session closed",
            "browser has been closed",
            "connection closed",
            "page closed",
            "context closed",
            "websocket error",
            "net::err_connection_closed",
        ]
        return any(pattern in error_str for pattern in session_expired_patterns)

    async def with_session_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        max_retries: int = 2,
        required_time: int = 30
    ) -> T:
        """
        Execute an operation with automatic session reconnection on expiry.

        Args:
            operation: Async callable to execute
            max_retries: Maximum number of reconnection attempts
            required_time: Ensure this many seconds remain before operation

        Returns:
            Result of the operation

        Raises:
            BrowserSessionExpiredError: If all retries exhausted
            Other exceptions: Re-raised from operation
        """
        # Ensure we have a fresh session before starting
        await self.ensure_fresh_session(required_time)

        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                if self._is_session_expired_error(e):
                    if attempt < max_retries:
                        print(f"Session expired during operation (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        print(f"Reconnecting in {self._reconnect_delay_seconds}s...")
                        await self.stop()
                        await asyncio.sleep(self._reconnect_delay_seconds)
                        await self.start()
                        continue
                    else:
                        raise BrowserSessionExpiredError(
                            f"Session expired after {max_retries + 1} attempts. Last error: {e}"
                        )
                # Non-session error, re-raise immediately
                raise

    async def start(self) -> None:
        """Connect to Browserless.io or launch local browser."""
        if self._browser is not None:
            return

        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()

        if self._browserless_token:
            # Use Browserless.io - much faster!
            # timeout=60000 is max for free tier (60 seconds)
            # Retry with exponential backoff for rate limits
            max_retries = 3
            base_delay = 5  # seconds

            for attempt in range(max_retries):
                try:
                    print(f"Connecting to Browserless.io (attempt {attempt + 1}/{max_retries})...")
                    ws_url = f"wss://chrome.browserless.io?token={self._browserless_token}&timeout=60000"
                    self._browser = await self._playwright.chromium.connect_over_cdp(
                        ws_url,
                        timeout=60000  # 60 second connection timeout
                    )
                    self._session_created_at = time.time()
                    print(f"Connected to Browserless.io! Session timeout: {self._session_timeout_seconds}s")
                    return
                except Exception as e:
                    error_str = str(e).lower()

                    if "429" in str(e) or "too many requests" in error_str:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"Rate limited, waiting {delay}s before retry...")
                            await asyncio.sleep(delay)
                            continue
                        raise BrowserlessRateLimitError(
                            "Browserless.io rate limit exceeded. Please wait a moment and try again."
                        )
                    elif "400" in str(e) or "bad request" in error_str:
                        raise BrowserConnectionError(
                            "Invalid Browserless.io configuration. Check your token."
                        )
                    else:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"Connection failed: {e}, retrying in {delay}s...")
                            await asyncio.sleep(delay)
                            continue
                        raise BrowserConnectionError(f"Failed to connect to Browserless.io: {e}")
        else:
            # Fallback to local browser (slow in containers)
            print("No BROWSERLESS_TOKEN found, launching local browser...")
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                timeout=300000,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            # Track session for local browser too (no timeout, but useful for logging)
            self._session_created_at = time.time()
            self._session_timeout_seconds = 999999  # No practical timeout for local
            print("Local browser ready!")

    async def stop(self) -> None:
        """Disconnect/close browser."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._session_created_at = None
        print("Browser closed")

    async def _get_browser(self) -> Browser:
        if self._browser is None:
            await self.start()
        return self._browser

    async def create_context(self) -> BrowserContext:
        """Create a new browser context with stealth settings."""
        browser = await self._get_browser()

        user_agent = self._get_random_user_agent()
        viewport = self._get_random_viewport()

        context = await browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale="en-US",
            timezone_id="America/Chicago",
            color_scheme="light",
            java_script_enabled=True,
        )

        # Stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        return context

    async def new_page(self, context: Optional[BrowserContext] = None) -> Page:
        if context is None:
            context = await self.create_context()

        page = await context.new_page()

        await page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

        return page

    @asynccontextmanager
    async def get_page(self):
        """Async context manager for getting a stealth page."""
        context = None
        page = None
        try:
            context = await self.create_context()
            page = await self.new_page(context)
            yield page
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass


# Aliases
StealthBrowser = AsyncStealthBrowser
SyncStealthBrowser = AsyncStealthBrowser
