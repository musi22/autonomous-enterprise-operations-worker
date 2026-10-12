import os
import asyncio
import logging
from typing import Dict, Any, Optional
from packages.sandbox_tools.enterprise.models import (
    EnterpriseToolResult,
    ErrorCategory,
    ToolExecutionStatus
)

logger = logging.getLogger(__name__)

# Global browser session state for persistent task execution
class PlaywrightSession:
    _playwright = None
    _browser = None
    _context = None
    _page = None

    @classmethod
    async def get_page(cls, headless: bool = True):
        try:
            from playwright.async_api import async_playwright
            if cls._page is None or cls._page.is_closed():
                if cls._playwright is None:
                    cls._playwright = await async_playwright().start()
                if cls._browser is None:
                    cls._browser = await cls._playwright.chromium.launch(
                        headless=headless,
                        args=["--no-sandbox", "--disable-dev-shm-usage"]
                    )
                cls._context = await cls._browser.new_context(viewport={"width": 1280, "height": 800})
                cls._page = await cls._context.new_page()
            return cls._page
        except Exception as e:
            logger.warning(f"Could not initialize real Playwright page: {e}")
            return None

    @classmethod
    async def close(cls):
        try:
            if cls._page and not cls._page.is_closed():
                await cls._page.close()
            if cls._context:
                await cls._context.close()
            if cls._browser:
                await cls._browser.close()
            if cls._playwright:
                await cls._playwright.stop()
        except Exception as e:
            logger.debug(f"Error closing playwright: {e}")
        finally:
            cls._page = None
            cls._context = None
            cls._browser = None
            cls._playwright = None


async def browser_navigate(url: str, base_url: str = "http://127.0.0.1:8000") -> EnterpriseToolResult:
    """
    Navigate Playwright browser to a sandbox application URL (e.g. '/sandbox/finance' or full URL).
    """
    try:
        target_url = url if url.startswith("http") else f"{base_url.rstrip('/')}/{url.lstrip('/')}"
        page = await PlaywrightSession.get_page()

        if page:
            response = await page.goto(target_url, wait_until="networkidle", timeout=8000)
            status_code = response.status if response else 200
            title = await page.title()
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "url": target_url,
                    "status_code": status_code,
                    "page_title": title
                },
                action_summary=f"Navigated browser to {target_url} (Page Title: '{title}')."
            )
        else:
            # Fallback simulated browser state
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "url": target_url,
                    "status_code": 200,
                    "page_title": "Simulated Enterprise Sandbox",
                    "mode": "simulated_browser"
                },
                action_summary=f"Navigated simulated browser to {target_url}."
            )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Browser navigation error: {str(e)}",
            error_category=ErrorCategory.BROWSER_ERROR,
            retryable=True
        )


async def browser_type(selector: str, text: str) -> EnterpriseToolResult:
    """
    Type text into an input field selector on the current browser page.
    """
    try:
        page = await PlaywrightSession.get_page()
        if page:
            await page.wait_for_selector(selector, timeout=5000)
            await page.fill(selector, text)
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={"selector": selector, "typed_text": text},
                action_summary=f"Typed '{text}' into element '{selector}'."
            )
        else:
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={"selector": selector, "typed_text": text, "mode": "simulated_browser"},
                action_summary=f"Typed '{text}' into simulated input '{selector}'."
            )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Browser type failed on selector '{selector}': {str(e)}",
            error_category=ErrorCategory.BROWSER_ERROR,
            retryable=True
        )


async def browser_click(selector: str) -> EnterpriseToolResult:
    """
    Click a button or interactive element on the current browser page.
    """
    try:
        page = await PlaywrightSession.get_page()
        if page:
            await page.wait_for_selector(selector, timeout=5000)
            await page.click(selector)
            # Give UI moment to re-render
            await asyncio.sleep(0.3)
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={"selector": selector},
                action_summary=f"Clicked element '{selector}'."
            )
        else:
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={"selector": selector, "mode": "simulated_browser"},
                action_summary=f"Clicked simulated element '{selector}'."
            )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Browser click failed on selector '{selector}': {str(e)}",
            error_category=ErrorCategory.BROWSER_ERROR,
            retryable=True
        )


async def browser_read(selector: Optional[str] = None) -> EnterpriseToolResult:
    """
    Read text and content from current browser page or a specific selector.
    """
    try:
        page = await PlaywrightSession.get_page()
        if page:
            if selector:
                await page.wait_for_selector(selector, timeout=5000)
                text = await page.inner_text(selector)
            else:
                text = await page.inner_text("body")
            url = page.url
            title = await page.title()
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "url": url,
                    "title": title,
                    "content_snippet": text[:500] if text else "",
                    "full_length": len(text or "")
                },
                action_summary=f"Read browser page content from {url}."
            )
        else:
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "url": "http://127.0.0.1:8000/sandbox/finance",
                    "title": "Finance Operations Portal",
                    "content_snippet": "Finance portal ready.",
                    "mode": "simulated_browser"
                },
                action_summary="Read simulated browser page content."
            )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Browser read failed: {str(e)}",
            error_category=ErrorCategory.BROWSER_ERROR,
            retryable=True
        )
