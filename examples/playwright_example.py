#!/usr/bin/env python3
"""
Example: Playwright Integration

This script demonstrates how to use the Playwright Integration module
for browser automation and web interaction.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.playwright_integration import PlaywrightIntegration


async def main():
    """Demonstrate Playwright integration"""
    print("🌐 Playwright Integration Example")
    print("=" * 40)
    
    # Initialize Playwright
    playwright = PlaywrightIntegration()
    await playwright.initialize()
    
    try:
        # Example 1: Navigate to a website
        print("\n1. Navigating to example.com...")
        result = await playwright.navigate_to_url("https://example.com")
        if result["success"]:
            print(f"✅ Navigation successful")
            print(f"   URL: {result['final_url']}")
            print(f"   Title: {result['title']}")
        else:
            print(f"❌ Error: {result['error']}")
            return
        
        # Example 2: Take a screenshot
        print("\n2. Taking a screenshot...")
        result = await playwright.take_screenshot()
        if result["success"]:
            print(f"✅ Screenshot saved: {result['filename']}")
            print(f"   Path: {result['path']}")
            print(f"   Size: {len(result['base64'])} characters (base64)")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 3: Get page content
        print("\n3. Getting page content...")
        result = await playwright.get_page_content()
        if result["success"]:
            content = result["content"]
            print(f"✅ Page content retrieved ({len(content)} characters)")
            # Show first few lines
            lines = content.split('\n')[:10]
            print("   First 10 lines:")
            for i, line in enumerate(lines, 1):
                print(f"     {i}: {line[:80]}...")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 4: Find elements
        print("\n4. Finding elements on the page...")
        result = await playwright.find_elements("h1")
        if result["success"]:
            print(f"✅ Found {result['count']} h1 elements")
            for element in result["elements"]:
                print(f"   - {element['tag_name']}: {element['text'][:50]}...")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 5: Get element text
        print("\n5. Getting text from h1 element...")
        result = await playwright.get_element_text("h1")
        if result["success"]:
            print(f"✅ H1 text: {result['text']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 6: Navigate to a more interactive site
        print("\n6. Navigating to Wikipedia...")
        result = await playwright.navigate_to_url("https://en.wikipedia.org/wiki/Main_Page")
        if result["success"]:
            print(f"✅ Navigation successful")
            print(f"   Title: {result['title']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 7: Search for content
        print("\n7. Searching for 'Python' on Wikipedia...")
        
        # Wait for search input
        result = await playwright.wait_for_element("input[name='search']")
        if result["success"]:
            print("✅ Search input found")
            
            # Fill search form
            result = await playwright.fill_form("input[name='search']", "Python programming")
            if result["success"]:
                print("✅ Search form filled")
                
                # Submit search
                result = await playwright.click_element("input[name='go']")
                if result["success"]:
                    print("✅ Search submitted")
                    
                    # Wait for navigation
                    await asyncio.sleep(2)
                    
                    # Get new page title
                    result = await playwright.get_page_title()
                    if result["success"]:
                        print(f"✅ New page title: {result['title']}")
                else:
                    print(f"❌ Error submitting search: {result['error']}")
            else:
                print(f"❌ Error filling form: {result['error']}")
        else:
            print(f"❌ Error finding search input: {result['error']}")
        
        # Example 8: Take screenshot of search results
        print("\n8. Taking screenshot of search results...")
        result = await playwright.take_screenshot(filename="wikipedia_search.png")
        if result["success"]:
            print(f"✅ Screenshot saved: {result['filename']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 9: Create a new tab
        print("\n9. Creating a new tab...")
        result = await playwright.create_tab("https://httpbin.org/forms/post")
        if result["success"]:
            print(f"✅ New tab created: {result['page_id']}")
            
            # Fill out a form
            await asyncio.sleep(1)  # Wait for page to load
            
            result = await playwright.fill_form("input[name='custname']", "John Doe")
            if result["success"]:
                print("✅ Customer name filled")
            
            result = await playwright.fill_form("input[name='custtel']", "123-456-7890")
            if result["success"]:
                print("✅ Customer telephone filled")
            
            result = await playwright.fill_form("input[name='custemail']", "john@example.com")
            if result["success"]:
                print("✅ Customer email filled")
            
            # Take screenshot before submitting
            result = await playwright.take_screenshot(filename="form_before_submit.png")
            if result["success"]:
                print("✅ Form screenshot taken")
            
            # Submit form
            result = await playwright.click_element("input[type='submit']")
            if result["success"]:
                print("✅ Form submitted")
                await asyncio.sleep(2)
                
                # Take screenshot after submission
                result = await playwright.take_screenshot(filename="form_after_submit.png")
                if result["success"]:
                    print("✅ Form submission screenshot taken")
        else:
            print(f"❌ Error creating tab: {result['error']}")
        
        # Example 10: Manage tabs
        print("\n10. Managing tabs...")
        result = await playwright.get_pages()
        if result["success"]:
            print(f"✅ Open tabs: {len(result['pages'])}")
            for page in result['pages']:
                current_marker = " (current)" if page['is_current'] else ""
                print(f"   - {page['page_id']}: {page['title']}{current_marker}")
            
            # Switch to first tab
            if len(result['pages']) > 1:
                result = await playwright.switch_tab(0)
                if result["success"]:
                    print(f"✅ Switched to tab: {result['page_id']}")
        else:
            print(f"❌ Error getting pages: {result['error']}")
        
        # Example 11: Execute JavaScript
        print("\n11. Executing JavaScript...")
        js_code = """
        return {
            url: window.location.href,
            title: document.title,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        }
        """
        
        result = await playwright.execute_javascript(js_code)
        if result["success"]:
            js_result = result["result"]
            print("✅ JavaScript executed successfully:")
            print(f"   URL: {js_result['url']}")
            print(f"   Title: {js_result['title']}")
            print(f"   User Agent: {js_result['userAgent'][:50]}...")
            print(f"   Timestamp: {js_result['timestamp']}")
        else:
            print(f"❌ Error executing JavaScript: {result['error']}")
        
        # Example 12: Scroll the page
        print("\n12. Scrolling the page...")
        result = await playwright.scroll_page("down", 500)
        if result["success"]:
            print("✅ Page scrolled down")
            await asyncio.sleep(1)
            
            # Take screenshot after scrolling
            result = await playwright.take_screenshot(filename="after_scroll.png")
            if result["success"]:
                print("✅ Screenshot taken after scrolling")
        else:
            print(f"❌ Error scrolling: {result['error']}")
        
        # Example 13: Close tabs
        print("\n13. Closing tabs...")
        result = await playwright.get_pages()
        if result["success"]:
            for page in result['pages']:
                if not page['is_current']:  # Close non-current tabs first
                    result = await playwright.close_page(page['page_id'])
                    if result["success"]:
                        print(f"✅ Closed tab: {page['page_id']}")
            
            # Close current tab last
            result = await playwright.close_page()
            if result["success"]:
                print("✅ Closed current tab")
        else:
            print(f"❌ Error getting pages: {result['error']}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # Clean up
        await playwright.stop()
    
    print("\n✅ Playwright integration example completed!")


if __name__ == "__main__":
    asyncio.run(main())