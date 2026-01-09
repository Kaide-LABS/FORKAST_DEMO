"""
Global browser pool for Playwright.

Initializes browser at application startup to avoid slow startup on each request.
"""

from __future__ import annotations

import threading
from typing import Optional, TYPE_CHECKING

# Only import for type hints - actual import is lazy
if TYPE_CHECKING:
    from playwright.sync_api import Browser, Playwright


class BrowserPool:
    """
    Singleton browser pool that maintains a warm Playwright instance.

    Initialized at app startup to avoid the 4+ minute cold start penalty.
    """

    _instance: Optional['BrowserPool'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> 'BrowserPool':
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def initialize(self) -> None:
        """Initialize Playwright and launch browser. Call this at app startup."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            print("BrowserPool: Initializing Playwright...")
            # Import playwright only when needed (lazy import)
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            print("BrowserPool: Launching browser...")
            self._browser = self._playwright.chromium.launch(
                headless=True,
                timeout=180000,  # 3 minute timeout for browser launch
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--disable-gpu",
                ]
            )
            self._initialized = True
            print("BrowserPool: Browser ready!")

    def get_browser(self) -> Browser:
        """Get the browser instance. Initializes if not already done."""
        if not self._initialized:
            self.initialize()
        return self._browser

    def shutdown(self) -> None:
        """Shutdown browser and playwright."""
        with self._lock:
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None

            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

            self._initialized = False
            print("BrowserPool: Shutdown complete")


# Global singleton
browser_pool = BrowserPool.get_instance()


def get_browser() -> Browser:
    """Get the global browser instance."""
    return browser_pool.get_browser()


def initialize_browser() -> None:
    """Initialize browser at app startup."""
    browser_pool.initialize()


def shutdown_browser() -> None:
    """Shutdown browser at app shutdown."""
    browser_pool.shutdown()
