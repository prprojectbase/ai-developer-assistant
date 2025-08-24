import asyncio
import logging
import base64
import tempfile
import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
from dataclasses import dataclass
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, ElementHandle, TimeoutError as PlaywrightTimeoutError
from ..config.settings import get_settings


@dataclass
class BrowserAction:
    """Browser action data structure"""
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    timeout: Optional[int] = None
    options: Optional[Dict[str, Any]] = None


class PlaywrightIntegration:
    """Playwright integration for browser automation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Browser state
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.pages: Dict[str, Page] = {}
        self.current_page_id: Optional[str] = None
        
        # Configuration
        self.headless = self.settings.playwright_headless
        self.default_timeout = self.settings.playwright_timeout
        
        # Screenshots and recordings
        self.screenshot_dir = Path("./screenshots")
        self.recording_dir = Path("./recordings")
        
    async def initialize(self) -> None:
        """Initialize the Playwright integration"""
        self.logger.info("Initializing Playwright Integration...")
        
        # Create directories for screenshots and recordings
        self.screenshot_dir.mkdir(exist_ok=True)
        self.recording_dir.mkdir(exist_ok=True)
        
        # Initialize Playwright
        self.playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        
        # Create initial page
        await self.create_page()
        
        self.logger.info("Playwright Integration initialized successfully")
    
    async def stop(self) -> None:
        """Stop the Playwright integration"""
        self.logger.info("Stopping Playwright Integration...")
        
        # Close all pages
        for page_id, page in self.pages.items():
            try:
                await page.close()
            except Exception as e:
                self.logger.error(f"Error closing page {page_id}: {e}")
        
        self.pages.clear()
        
        # Close browser
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
        
        # Stop Playwright
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                self.logger.error(f"Error stopping Playwright: {e}")
        
        self.logger.info("Playwright Integration stopped")
    
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser action"""
        action_type = action.get("type")
        
        try:
            if action_type == "navigate":
                return await self.navigate_to_url(action["url"])
            
            elif action_type == "click":
                return await self.click_element(
                    action["selector"],
                    action.get("timeout"),
                    action.get("options", {})
                )
            
            elif action_type == "type":
                return await self.type_text(
                    action["selector"],
                    action["text"],
                    action.get("timeout"),
                    action.get("options", {})
                )
            
            elif action_type == "fill":
                return await self.fill_form(
                    action["selector"],
                    action["value"],
                    action.get("timeout"),
                    action.get("options", {})
                )
            
            elif action_type == "screenshot":
                return await self.take_screenshot(
                    action.get("selector"),
                    action.get("filename"),
                    action.get("options", {})
                )
            
            elif action_type == "get_text":
                return await self.get_element_text(
                    action["selector"],
                    action.get("timeout")
                )
            
            elif action_type == "get_attribute":
                return await self.get_element_attribute(
                    action["selector"],
                    action["attribute"],
                    action.get("timeout")
                )
            
            elif action_type == "wait_for":
                return await self.wait_for_element(
                    action["selector"],
                    action.get("timeout"),
                    action.get("state", "visible")
                )
            
            elif action_type == "wait_for_navigation":
                return await self.wait_for_navigation(
                    action.get("timeout"),
                    action.get("url")
                )
            
            elif action_type == "execute_script":
                return await self.execute_javascript(
                    action["script"],
                    action.get("args", [])
                )
            
            elif action_type == "get_page_title":
                return await self.get_page_title()
            
            elif action_type == "get_page_url":
                return await self.get_page_url()
            
            elif action_type == "get_page_content":
                return await self.get_page_content()
            
            elif action_type == "find_elements":
                return await self.find_elements(
                    action["selector"],
                    action.get("timeout")
                )
            
            elif action_type == "hover":
                return await self.hover_element(
                    action["selector"],
                    action.get("timeout"),
                    action.get("options", {})
                )
            
            elif action_type == "scroll":
                return await self.scroll_page(
                    action.get("direction", "down"),
                    action.get("amount")
                )
            
            elif action_type == "switch_tab":
                return await self.switch_tab(action["tab_index"])
            
            elif action_type == "create_tab":
                return await self.create_page(action.get("url"))
            
            elif action_type == "close_tab":
                return await self.close_page(action.get("page_id"))
            
            elif action_type == "get_tabs":
                return await self.get_pages()
            
            elif action_type == "download_file":
                return await self.download_file(
                    action["selector"],
                    action.get("timeout")
                )
            
            elif action_type == "upload_file":
                return await self.upload_file(
                    action["selector"],
                    action["file_path"],
                    action.get("timeout")
                )
            
            elif action_type == "handle_alert":
                return await self.handle_alert(
                    action.get("accept", True),
                    action.get("prompt_text")
                )
            
            else:
                return {"error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing browser action {action_type}: {e}")
            return {"error": str(e)}
    
    async def navigate_to_url(self, url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Navigate to a URL"""
        page = await self._get_current_page()
        
        try:
            await page.goto(url, timeout=timeout or self.default_timeout)
            
            return {
                "success": True,
                "url": url,
                "final_url": page.url,
                "title": await page.title()
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Navigation timeout for URL: {url}"}
        except Exception as e:
            return {"error": f"Navigation failed: {str(e)}"}
    
    async def click_element(self, selector: str, timeout: Optional[int] = None, 
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Click on an element"""
        page = await self._get_current_page()
        
        try:
            element = await page.wait_for_selector(selector, timeout=timeout or self.default_timeout)
            await element.click(**options or {})
            
            return {
                "success": True,
                "selector": selector,
                "action": "click"
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Click failed: {str(e)}"}
    
    async def type_text(self, selector: str, text: str, timeout: Optional[int] = None,
                       options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Type text into an element"""
        page = await self._get_current_page()
        
        try:
            element = await page.wait_for_selector(selector, timeout=timeout or self.default_timeout)
            await element.type(text, **options or {})
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "action": "type"
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Type failed: {str(e)}"}
    
    async def fill_form(self, selector: str, value: str, timeout: Optional[int] = None,
                       options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fill a form field"""
        page = await self._get_current_page()
        
        try:
            element = await page.wait_for_selector(selector, timeout=timeout or self.default_timeout)
            await element.fill(value, **options or {})
            
            return {
                "success": True,
                "selector": selector,
                "value": value,
                "action": "fill"
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Fill failed: {str(e)}"}
    
    async def take_screenshot(self, selector: Optional[str] = None, 
                            filename: Optional[str] = None,
                            options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Take a screenshot"""
        page = await self._get_current_page()
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = self.screenshot_dir / filename
            
            # Take screenshot
            if selector:
                element = await page.wait_for_selector(selector)
                screenshot_bytes = await element.screenshot(**options or {})
            else:
                screenshot_bytes = await page.screenshot(**options or {})
            
            # Save screenshot
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot_bytes)
            
            # Convert to base64 for return
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return {
                "success": True,
                "filename": filename,
                "path": str(screenshot_path),
                "base64": screenshot_base64,
                "selector": selector
            }
            
        except Exception as e:
            return {"error": f"Screenshot failed: {str(e)}"}
    
    async def get_element_text(self, selector: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Get text content of an element"""
        page = await self._get_current_page()
        
        try:
            element = await page.wait_for_selector(selector, timeout=timeout or self.default_timeout)
            text = await element.text_content()
            
            return {
                "success": True,
                "selector": selector,
                "text": text
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Get text failed: {str(e)}"}
    
    async def get_element_attribute(self, selector: str, attribute: str, 
                                  timeout: Optional[int] = None) -> Dict[str, Any]:
        """Get attribute value of an element"""
        page = await self._get_current_page()
        
        try:
            element = await page.wait_for_selector(selector, timeout=timeout or self.default_timeout)
            value = await element.get_attribute(attribute)
            
            return {
                "success": True,
                "selector": selector,
                "attribute": attribute,
                "value": value
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Get attribute failed: {str(e)}"}
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None,
                              state: str = "visible") -> Dict[str, Any]:
        """Wait for an element to be in a specific state"""
        page = await self._get_current_page()
        
        try:
            await page.wait_for_selector(selector, timeout=timeout or self.default_timeout, state=state)
            
            return {
                "success": True,
                "selector": selector,
                "state": state
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found or not {state}: {selector}"}
        except Exception as e:
            return {"error": f"Wait for element failed: {str(e)}"}
    
    async def wait_for_navigation(self, timeout: Optional[int] = None, 
                                 url: Optional[str] = None) -> Dict[str, Any]:
        """Wait for navigation to complete"""
        page = await self._get_current_page()
        
        try:
            if url:
                await page.wait_for_url(url, timeout=timeout or self.default_timeout)
            else:
                await page.wait_for_load_state("networkidle", timeout=timeout or self.default_timeout)
            
            return {
                "success": True,
                "current_url": page.url,
                "title": await page.title()
            }
            
        except PlaywrightTimeoutError:
            return {"error": "Navigation timeout"}
        except Exception as e:
            return {"error": f"Wait for navigation failed: {str(e)}"}
    
    async def execute_javascript(self, script: str, args: List[Any] = None) -> Dict[str, Any]:
        """Execute JavaScript code"""
        page = await self._get_current_page()
        
        try:
            result = await page.evaluate(script, args or [])
            
            return {
                "success": True,
                "script": script,
                "result": result
            }
            
        except Exception as e:
            return {"error": f"JavaScript execution failed: {str(e)}"}
    
    async def get_page_title(self) -> Dict[str, Any]:
        """Get the current page title"""
        page = await self._get_current_page()
        
        try:
            title = await page.title()
            
            return {
                "success": True,
                "title": title
            }
            
        except Exception as e:
            return {"error": f"Get title failed: {str(e)}"}
    
    async def get_page_url(self) -> Dict[str, Any]:
        """Get the current page URL"""
        page = await self._get_current_page()
        
        try:
            url = page.url
            
            return {
                "success": True,
                "url": url
            }
            
        except Exception as e:
            return {"error": f"Get URL failed: {str(e)}"}
    
    async def get_page_content(self) -> Dict[str, Any]:
        """Get the current page HTML content"""
        page = await self._get_current_page()
        
        try:
            content = await page.content()
            
            return {
                "success": True,
                "content": content
            }
            
        except Exception as e:
            return {"error": f"Get content failed: {str(e)}"}
    
    async def find_elements(self, selector: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Find all elements matching a selector"""
        page = await self._get_current_page()
        
        try:
            elements = await page.query_selector_all(selector)
            
            elements_info = []
            for i, element in enumerate(elements):
                element_info = {
                    "index": i,
                    "tag_name": await element.evaluate("el => el.tagName"),
                    "text": await element.text_content(),
                    "is_visible": await element.is_visible()
                }
                elements_info.append(element_info)
            
            return {
                "success": True,
                "selector": selector,
                "count": len(elements),
                "elements": elements_info
            }
            
        except Exception as e:
            return {"error": f"Find elements failed: {str(e)}"}
    
    async def hover_element(self, selector: str, timeout: Optional[int] = None,
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Hover over an element"""
        page = await self._get_current_page()
        
        try:
            element = await page.wait_for_selector(selector, timeout=timeout or self.default_timeout)
            await element.hover(**options or {})
            
            return {
                "success": True,
                "selector": selector,
                "action": "hover"
            }
            
        except PlaywrightTimeoutError:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Hover failed: {str(e)}"}
    
    async def scroll_page(self, direction: str = "down", amount: Optional[int] = None) -> Dict[str, Any]:
        """Scroll the page"""
        page = await self._get_current_page()
        
        try:
            if direction == "down":
                if amount:
                    await page.evaluate(f"window.scrollBy(0, {amount})")
                else:
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == "up":
                if amount:
                    await page.evaluate(f"window.scrollBy(0, -{amount})")
                else:
                    await page.evaluate("window.scrollBy(0, -window.innerHeight)")
            elif direction == "top":
                await page.evaluate("window.scrollTo(0, 0)")
            elif direction == "bottom":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            return {
                "success": True,
                "direction": direction,
                "amount": amount
            }
            
        except Exception as e:
            return {"error": f"Scroll failed: {str(e)}"}
    
    async def create_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new page/tab"""
        if not self.browser:
            return {"error": "Browser not initialized"}
        
        try:
            page = await self.browser.new_page()
            page_id = f"page_{len(self.pages)}"
            
            self.pages[page_id] = page
            self.current_page_id = page_id
            
            # Set default timeout
            page.set_default_timeout(self.default_timeout)
            
            # Navigate to URL if provided
            if url:
                await page.goto(url)
            
            return {
                "success": True,
                "page_id": page_id,
                "url": url or "about:blank"
            }
            
        except Exception as e:
            return {"error": f"Create page failed: {str(e)}"}
    
    async def switch_tab(self, tab_index: int) -> Dict[str, Any]:
        """Switch to a specific tab"""
        page_ids = list(self.pages.keys())
        
        if tab_index < 0 or tab_index >= len(page_ids):
            return {"error": f"Invalid tab index: {tab_index}"}
        
        page_id = page_ids[tab_index]
        self.current_page_id = page_id
        
        return {
            "success": True,
            "page_id": page_id,
            "tab_index": tab_index
        }
    
    async def close_page(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        """Close a specific page"""
        if not page_id:
            page_id = self.current_page_id
        
        if page_id not in self.pages:
            return {"error": f"Page not found: {page_id}"}
        
        try:
            await self.pages[page_id].close()
            del self.pages[page_id]
            
            # Switch to another page if available
            if self.current_page_id == page_id:
                self.current_page_id = next(iter(self.pages.keys()), None)
            
            return {
                "success": True,
                "page_id": page_id
            }
            
        except Exception as e:
            return {"error": f"Close page failed: {str(e)}"}
    
    async def get_pages(self) -> Dict[str, Any]:
        """Get information about all open pages"""
        pages_info = []
        
        for i, (page_id, page) in enumerate(self.pages.items()):
            pages_info.append({
                "page_id": page_id,
                "tab_index": i,
                "url": page.url,
                "title": await page.title(),
                "is_current": page_id == self.current_page_id
            })
        
        return {
            "success": True,
            "pages": pages_info,
            "current_page_id": self.current_page_id
        }
    
    async def download_file(self, selector: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Download a file by clicking a download link"""
        page = await self._get_current_page()
        
        try:
            # Set up download handler
            async with page.expect_download(timeout=timeout or self.default_timeout) as download_info:
                await page.click(selector)
            
            download = await download_info
            
            # Get download information
            download_path = await download.path()
            suggested_filename = download.suggested_filename
            
            # Copy to recordings directory
            final_path = self.recording_dir / suggested_filename
            await download.save_as(final_path)
            
            return {
                "success": True,
                "filename": suggested_filename,
                "path": str(final_path),
                "url": download.url
            }
            
        except Exception as e:
            return {"error": f"Download failed: {str(e)}"}
    
    async def upload_file(self, selector: str, file_path: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Upload a file"""
        page = await self._get_current_page()
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Set up file chooser
            async with page.expect_file_chooser(timeout=timeout or self.default_timeout) as file_chooser_info:
                await page.click(selector)
            
            file_chooser = await file_chooser_info
            await file_chooser.set_files(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "selector": selector
            }
            
        except Exception as e:
            return {"error": f"Upload failed: {str(e)}"}
    
    async def handle_alert(self, accept: bool = True, prompt_text: Optional[str] = None) -> Dict[str, Any]:
        """Handle browser alerts"""
        page = await self._get_current_page()
        
        try:
            # Set up alert handler
            async def handle_dialog(dialog):
                if prompt_text is not None:
                    await dialog.fill(prompt_text)
                
                if accept:
                    await dialog.accept()
                else:
                    await dialog.dismiss()
            
            page.on("dialog", handle_dialog)
            
            return {
                "success": True,
                "accept": accept,
                "prompt_text": prompt_text
            }
            
        except Exception as e:
            return {"error": f"Handle alert failed: {str(e)}"}
    
    async def _get_current_page(self) -> Page:
        """Get the current page"""
        if not self.current_page_id or self.current_page_id not in self.pages:
            # Create a new page if none exists
            await self.create_page()
        
        return self.pages[self.current_page_id]