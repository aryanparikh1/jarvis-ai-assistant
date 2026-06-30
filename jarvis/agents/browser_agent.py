"""
Browser Agent — Playwright-powered browser automation
"""

import asyncio
from typing import Optional
from PySide6.QtCore import QObject, Signal
from jarvis.utils.logger import logger
from jarvis.core.permission_system import permissions


class BrowserAgent(QObject):
    """
    Playwright-based browser automation agent.
    Supports Chrome and Edge via chromium.
    """

    action_completed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._browser = None
        self._page = None
        self._playwright = None

    async def launch(self, headless: bool = False, browser: str = "chromium"):
        """Launch the browser."""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            launcher = getattr(self._playwright, browser)
            self._browser = await launcher.launch(headless=headless)
            self._page = await self._browser.new_page()
            logger.info(f"Browser launched: {browser}")
            return True
        except Exception as e:
            logger.error(f"Browser launch error: {e}")
            self.error_occurred.emit(str(e))
            return False

    async def navigate(self, url: str) -> str:
        """Navigate to a URL."""
        if not self._ensure_browser():
            return "Browser not running"
        if not permissions.can_execute("browser_navigate", f"Navigate to: {url}"):
            return "Navigation denied"
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            title = await self._page.title()
            self.action_completed.emit(f"Navigated to: {title}")
            return f"Navigated to '{title}' ({url})"
        except Exception as e:
            return f"Navigation error: {e}"

    async def click(self, selector: str) -> str:
        """Click an element."""
        if not self._ensure_browser():
            return "Browser not running"
        if not permissions.can_execute("browser_click", f"Click: {selector}"):
            return "Click denied"
        try:
            await self._page.click(selector, timeout=5000)
            return f"Clicked: {selector}"
        except Exception as e:
            return f"Click error: {e}"

    async def type_text(self, selector: str, text: str) -> str:
        """Type text into an input."""
        if not self._ensure_browser():
            return "Browser not running"
        try:
            await self._page.fill(selector, text)
            return f"Typed '{text}' into {selector}"
        except Exception as e:
            return f"Type error: {e}"

    async def get_page_text(self) -> str:
        """Extract visible text from the current page."""
        if not self._ensure_browser():
            return "Browser not running"
        try:
            text = await self._page.inner_text("body")
            return text[:3000] if len(text) > 3000 else text
        except Exception as e:
            return f"Extract error: {e}"

    async def screenshot(self, path: str = "screenshot.png") -> str:
        """Take a screenshot of the current page."""
        if not self._ensure_browser():
            return "Browser not running"
        try:
            await self._page.screenshot(path=path, full_page=False)
            return f"Screenshot saved: {path}"
        except Exception as e:
            return f"Screenshot error: {e}"

    async def search_google(self, query: str) -> str:
        """Navigate to Google and search."""
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return await self.navigate(url)

    async def close(self):
        """Close the browser."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self._browser = None
            self._page = None
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Browser close error: {e}")

    def _ensure_browser(self) -> bool:
        return self._browser is not None and self._page is not None

    def run_async(self, coro):
        """Run an async browser action from sync context."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


# Singleton
browser_agent = BrowserAgent()
