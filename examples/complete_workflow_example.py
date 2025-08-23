#!/usr/bin/env python3
"""
Example: Complete AI Developer Assistant Workflow

This script demonstrates a complete workflow using the AI Developer Assistant,
combining multiple modules to solve a real-world development task.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.main_agent import AIDeveloperAssistant
from modules.task_manager import TaskPriority


async def main():
    """Demonstrate complete AI Developer Assistant workflow"""
    print("🤖 Complete AI Developer Assistant Workflow Example")
    print("=" * 60)
    print("This example demonstrates creating a web scraper project from scratch")
    print("using multiple AI-powered modules working together.")
    print("=" * 60)
    
    # Initialize the assistant
    assistant = AIDeveloperAssistant()
    await assistant.initialize()
    
    try:
        print("\n🚀 Starting AI Developer Assistant...")
        
        # Example 1: Create project structure
        print("\n1. 📁 Creating project structure...")
        
        # Create project directory
        mkdir_task = {
            "name": "Create Project Directory",
            "description": "Create main project directory",
            "type": "file_operation",
            "parameters": {
                "type": "create_directory",
                "path": "web_scraper_project"
            }
        }
        
        result = await assistant.task_manager.create_task(mkdir_task)
        if result["success"]:
            print("✅ Project directory created")
        else:
            print(f"❌ Error creating directory: {result.get('error', 'Unknown error')}")
        
        # Create subdirectories
        subdirs = ["src", "tests", "data", "docs"]
        for subdir in subdirs:
            subdir_task = {
                "name": f"Create {subdir} Directory",
                "description": f"Create {subdir} subdirectory",
                "type": "file_operation",
                "parameters": {
                    "type": "create_directory",
                    "path": f"web_scraper_project/{subdir}"
                }
            }
            
            result = await assistant.task_manager.create_task(subdir_task)
            if result["success"]:
                print(f"✅ Created {subdir}/ directory")
        
        await asyncio.sleep(2)  # Wait for tasks to complete
        
        # Example 2: Generate project files using AI
        print("\n2. 🧠 Generating project files with AI...")
        
        # Generate main Python file
        generate_main_task = {
            "name": "Generate Main Scraper",
            "description": "Generate main web scraper Python file",
            "type": "generate_code",
            "parameters": {
                "prompt": "Create a Python web scraper that extracts article titles and URLs from a news website. Use requests and BeautifulSoup. Include error handling and rate limiting.",
                "language": "python"
            },
            "priority": TaskPriority.HIGH
        }
        
        result = await assistant.task_manager.create_task(generate_main_task)
        if result["success"]:
            print("✅ Main scraper generation task created")
        else:
            print(f"❌ Error creating generation task: {result.get('error', 'Unknown error')}")
        
        # Generate requirements file
        generate_req_task = {
            "name": "Generate Requirements",
            "description": "Generate requirements.txt file",
            "type": "generate_code",
            "parameters": {
                "prompt": "Create a requirements.txt file for a web scraping project with requests, beautifulsoup4, pandas, and pytest",
                "language": "text"
            }
        }
        
        result = await assistant.task_manager.create_task(generate_req_task)
        if result["success"]:
            print("✅ Requirements generation task created")
        
        await asyncio.sleep(5)  # Wait for AI generation
        
        # Example 3: Save generated files
        print("\n3. 💾 Saving generated files...")
        
        # Save main scraper (simulated - in real scenario, would get from AI response)
        main_code = '''import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url, delay=1):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraper/1.0)'
        })
    
    def get_page(self, url):
        """Fetch a web page with error handling"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_articles(self, html):
        """Extract article titles and URLs from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # Find article links (adjust selectors based on target website)
        for article in soup.find_all('article'):
            title_elem = article.find(['h1', 'h2', 'h3'])
            link_elem = article.find('a')
            
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href')
                
                if url:
                    # Make URL absolute
                    if not url.startswith('http'):
                        url = urljoin(self.base_url, url)
                    
                    articles.append({
                        'title': title,
                        'url': url
                    })
        
        return articles
    
    def scrape_articles(self, max_pages=5):
        """Scrape articles from multiple pages"""
        all_articles = []
        
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/page/{page}" if page > 1 else self.base_url
            
            logger.info(f"Scraping page {page}: {url}")
            
            html = self.get_page(url)
            if html:
                articles = self.extract_articles(html)
                all_articles.extend(articles)
                
                # Rate limiting
                time.sleep(self.delay)
            else:
                logger.warning(f"Failed to fetch page {page}")
        
        return all_articles
    
    def save_to_csv(self, articles, filename):
        """Save articles to CSV file"""
        df = pd.DataFrame(articles)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(articles)} articles to {filename}")

if __name__ == "__main__":
    # Example usage
    scraper = WebScraper("https://example-news-website.com")
    articles = scraper.scrape_articles(max_pages=3)
    
    if articles:
        scraper.save_to_csv(articles, "articles.csv")
        print(f"Scraped {len(articles)} articles")
    else:
        print("No articles found")
'''
        
        save_main_task = {
            "name": "Save Main Scraper",
            "description": "Save main scraper code to file",
            "type": "file_operation",
            "parameters": {
                "type": "write_file",
                "path": "web_scraper_project/src/scraper.py",
                "content": main_code
            }
        }
        
        result = await assistant.task_manager.create_task(save_main_task)
        if result["success"]:
            print("✅ Main scraper saved")
        
        # Save requirements
        requirements_content = """requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
pytest>=7.4.0
lxml>=4.9.0
"""
        
        save_req_task = {
            "name": "Save Requirements",
            "description": "Save requirements to file",
            "type": "file_operation",
            "parameters": {
                "type": "write_file",
                "path": "web_scraper_project/requirements.txt",
                "content": requirements_content
            }
        }
        
        result = await assistant.task_manager.create_task(save_req_task)
        if result["success"]:
            print("✅ Requirements saved")
        
        await asyncio.sleep(2)
        
        # Example 4: Analyze generated code
        print("\n4. 🔍 Analyzing generated code...")
        
        analyze_task = {
            "name": "Analyze Scraper Code",
            "description": "Analyze the generated scraper code for improvements",
            "type": "analyze_code",
            "parameters": {
                "code": main_code,
                "language": "python"
            }
        }
        
        result = await assistant.task_manager.create_task(analyze_task)
        if result["success"]:
            print("✅ Code analysis task created")
        
        await asyncio.sleep(3)
        
        # Example 5: Create test file
        print("\n5. 🧪 Creating test file...")
        
        test_code = '''import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper import WebScraper

class TestWebScraper:
    def test_init(self):
        """Test scraper initialization"""
        scraper = WebScraper("https://example.com")
        assert scraper.base_url == "https://example.com"
        assert scraper.delay == 1
        assert 'User-Agent' in scraper.session.headers
    
    @patch('requests.Session.get')
    def test_get_page_success(self, mock_get):
        """Test successful page fetch"""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = WebScraper("https://example.com")
        result = scraper.get_page("https://example.com")
        
        assert result == "<html><body>Test</body></html>"
        mock_get.assert_called_once_with("https://example.com")
    
    @patch('requests.Session.get')
    def test_get_page_error(self, mock_get):
        """Test page fetch error"""
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")
        
        scraper = WebScraper("https://example.com")
        result = scraper.get_page("https://example.com")
        
        assert result is None
    
    def test_extract_articles(self):
        """Test article extraction"""
        html = """
        <html>
            <body>
                <article>
                    <h2>Test Article 1</h2>
                    <a href="/article1">Read more</a>
                </article>
                <article>
                    <h3>Test Article 2</h3>
                    <a href="https://example.com/article2">Read more</a>
                </article>
            </body>
        </html>
        """
        
        scraper = WebScraper("https://example.com")
        articles = scraper.extract_articles(html)
        
        assert len(articles) == 2
        assert articles[0]['title'] == "Test Article 1"
        assert articles[0]['url'] == "https://example.com/article1"
        assert articles[1]['title'] == "Test Article 2"
        assert articles[1]['url'] == "https://example.com/article2"
    
    @patch('time.sleep')
    @patch.object(WebScraper, 'get_page')
    def test_scrape_articles(self, mock_get_page, mock_sleep):
        """Test article scraping"""
        mock_get_page.return_value = "<html><body><article><h2>Test</h2><a href='/test'>Link</a></article></body></html>"
        
        scraper = WebScraper("https://example.com", delay=0)
        articles = scraper.scrape_articles(max_pages=2)
        
        assert len(articles) == 2
        assert mock_get_page.call_count == 2
        assert mock_sleep.call_count == 2
'''
        
        save_test_task = {
            "name": "Save Test File",
            "description": "Save test file for the scraper",
            "type": "file_operation",
            "parameters": {
                "type": "write_file",
                "path": "web_scraper_project/tests/test_scraper.py",
                "content": test_code
            }
        }
        
        result = await assistant.task_manager.create_task(save_test_task)
        if result["success"]:
            print("✅ Test file saved")
        
        await asyncio.sleep(2)
        
        # Example 6: Create documentation
        print("\n6. 📚 Creating documentation...")
        
        docs_content = """# Web Scraper Project

A Python web scraping project that extracts article titles and URLs from news websites.

## Features

- Rate limiting to avoid overwhelming servers
- Error handling for network issues
- CSV export functionality
- Configurable scraping parameters
- Comprehensive test coverage

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from src.scraper import WebScraper

# Initialize scraper
scraper = WebScraper("https://example-news-site.com", delay=2)

# Scrape articles
articles = scraper.scrape_articles(max_pages=5)

# Save to CSV
scraper.save_to_csv(articles, "articles.csv")
```

## Configuration

- `base_url`: The base URL of the website to scrape
- `delay`: Delay between requests in seconds (default: 1)
- `max_pages`: Maximum number of pages to scrape

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## License

MIT License
"""
        
        save_docs_task = {
            "name": "Save Documentation",
            "description": "Save project documentation",
            "type": "file_operation",
            "parameters": {
                "type": "write_file",
                "path": "web_scraper_project/README.md",
                "content": docs_content
            }
        }
        
        result = await assistant.task_manager.create_task(save_docs_task)
        if result["success"]:
            print("✅ Documentation saved")
        
        await asyncio.sleep(2)
        
        # Example 7: Run terminal commands
        print("\n7. 💻 Running terminal commands...")
        
        # Check project structure
        ls_task = {
            "name": "List Project Files",
            "description": "List files in project directory",
            "type": "terminal_command",
            "parameters": {
                "command": "find web_scraper_project -type f | sort",
                "cwd": "."
            }
        }
        
        result = await assistant.task_manager.create_task(ls_task)
        if result["success"]:
            print("✅ File listing task created")
        
        # Check Python syntax
        syntax_task = {
            "name": "Check Python Syntax",
            "description": "Check Python syntax of generated files",
            "type": "terminal_command",
            "parameters": {
                "command": "python -m py_compile web_scraper_project/src/scraper.py",
                "cwd": "."
            }
        }
        
        result = await assistant.task_manager.create_task(syntax_task)
        if result["success"]:
            print("✅ Syntax check task created")
        
        await asyncio.sleep(3)
        
        # Example 8: Create VS Code workspace
        print("\n8. 💻 Creating VS Code workspace...")
        
        vscode_settings = {
            "python.pythonPath": "${workspaceFolder}/venv/bin/python",
            "python.linting.enabled": true,
            "python.linting.pylintEnabled": true,
            "python.formatting.provider": "black",
            "editor.formatOnSave": true,
            "files.associations": {
                "*.py": "python"
            }
        }
        
        create_vscode_task = {
            "name": "Create VS Code Settings",
            "description": "Create VS Code workspace settings",
            "type": "file_operation",
            "parameters": {
                "type": "create_directory",
                "path": "web_scraper_project/.vscode"
            }
        }
        
        result = await assistant.task_manager.create_task(create_vscode_task)
        
        save_vscode_task = {
            "name": "Save VS Code Settings",
            "description": "Save VS Code settings file",
            "type": "file_operation",
            "parameters": {
                "type": "write_file",
                "path": "web_scraper_project/.vscode/settings.json",
                "content": json.dumps(vscode_settings, indent=2)
            }
        }
        
        result = await assistant.task_manager.create_task(save_vscode_task)
        if result["success"]:
            print("✅ VS Code workspace created")
        
        await asyncio.sleep(2)
        
        # Example 9: Generate project summary
        print("\n9. 📊 Generating project summary...")
        
        # Get project statistics
        stats_task = {
            "name": "Get Project Stats",
            "description": "Get project file statistics",
            "type": "terminal_command",
            "parameters": {
                "command": "find web_scraper_project -name '*.py' -exec wc -l {} + | tail -1",
                "cwd": "."
            }
        }
        
        result = await assistant.task_manager.create_task(stats_task)
        if result["success"]:
            print("✅ Project statistics task created")
        
        await asyncio.sleep(2)
        
        # Example 10: Final project overview
        print("\n10. 🎯 Final project overview...")
        
        # List all created files
        final_ls_task = {
            "name": "Final File Listing",
            "description": "List all project files with details",
            "type": "file_operation",
            "parameters": {
                "type": "read_directory_tree",
                "path": "web_scraper_project"
            }
        }
        
        result = await assistant.task_manager.create_task(final_ls_task)
        if result["success"]:
            print("✅ Final overview task created")
        
        # Wait for all remaining tasks to complete
        print("\n⏳ Waiting for all tasks to complete...")
        await asyncio.sleep(5)
        
        # Display final status
        print("\n" + "=" * 60)
        print("🎉 PROJECT COMPLETION SUMMARY")
        print("=" * 60)
        
        # Get task manager statistics
        stats = await assistant.task_manager.get_statistics()
        if stats["success"]:
            stat_data = stats["statistics"]
            print(f"📊 Total tasks created: {stat_data['total_tasks']}")
            print(f"✅ Tasks completed: {stat_data['completed_tasks']}")
            print(f"❌ Tasks failed: {stat_data['failed_tasks']}")
            print(f"⏱️  Average execution time: {stat_data['average_execution_time']:.2f}s")
        
        # Show final project structure
        print("\n📁 Final Project Structure:")
        try:
            result = await assistant.file_ops.list_directory("web_scraper_project")
            if result["success"]:
                for item in result["items"]:
                    if item["type"] == "directory":
                        print(f"   📁 {item['name']}/")
                        # List subdirectory contents
                        sub_result = await assistant.file_ops.list_directory(f"web_scraper_project/{item['name']}")
                        if sub_result["success"]:
                            for sub_item in sub_result["items"]:
                                print(f"      📄 {sub_item['name']} ({sub_item['size']} bytes)")
                    else:
                        print(f"   📄 {item['name']} ({item['size']} bytes)")
        except Exception as e:
            print(f"   Error listing project structure: {e}")
        
        print("\n🚀 Your web scraper project is ready!")
        print("   Next steps:")
        print("   1. cd web_scraper_project")
        print("   2. python -m venv venv")
        print("   3. source venv/bin/activate  (or venv\\Scripts\\activate on Windows)")
        print("   4. pip install -r requirements.txt")
        print("   5. python src/scraper.py")
        print("   6. pytest tests/")
        
    finally:
        # Clean up
        await assistant.stop()
    
    print("\n✅ Complete AI Developer Assistant workflow finished!")


if __name__ == "__main__":
    asyncio.run(main())