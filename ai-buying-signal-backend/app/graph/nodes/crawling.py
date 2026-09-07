import logging
import httpx
from bs4 import BeautifulSoup
from app.graph.discovery_state import LeadDiscoveryState
from app.agents.intelligence import call_llm_with_fallback

logger = logging.getLogger(__name__)

def select_crawler(state: LeadDiscoveryState) -> LeadDiscoveryState:
    url_data = state.get("current_url_data", {})
    url = url_data.get("url", "")
    
    # Heuristic crawler selection
    if any(d in url for d in ["reddit.com", "linkedin.com", "twitter.com", "x.com"]):
        selected = "playwright"
    elif any(d in url for d in ["news.ycombinator.com", "example.com"]):
        selected = "scrapy" # Simple static
    else:
        # Default to static (Scrapy/BS4 equivalent) first, fallback to Playwright later
        selected = "scrapy"
        
    # If we are retrying after a failure, escalate the crawler
    if state.get("retry_count", 0) > 0 and state.get("selected_crawler") == "scrapy":
        selected = "playwright"
        
    return {"selected_crawler": selected, "extraction_failed": False, "extracted_content": None}

async def extract_content_scrapy(state: LeadDiscoveryState) -> LeadDiscoveryState:
    url_data = state.get("current_url_data", {})
    url = url_data.get("url", "")
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 LeadBot/1.0"})
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Remove nav, header, footer, script, style
            for element in soup(["nav", "header", "footer", "script", "style", "aside", "form"]):
                element.decompose()
                
            text = soup.get_text(separator=' ', strip=True)
            return {"extracted_content": text, "extraction_failed": False}
    except Exception as e:
        logger.warning(f"Static extraction failed for {url}: {e}")
        return {"extraction_failed": True, "errors": [f"Scrapy Error: {e}"]}

async def extract_content_playwright(state: LeadDiscoveryState) -> LeadDiscoveryState:
    url_data = state.get("current_url_data", {})
    url = url_data.get("url", "")
    
    try:
        # Attempt to use Playwright (if installed)
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Extract main body text
            content = await page.evaluate('''() => {
                const elementsToRemove = document.querySelectorAll("nav, header, footer, script, style, aside");
                elementsToRemove.forEach(e => e.remove());
                return document.body.innerText;
            }''')
            await browser.close()
            return {"extracted_content": content, "extraction_failed": False}
    except ImportError:
        logger.warning("Playwright not installed, falling back to static.")
        return {"extraction_failed": True, "errors": ["Playwright not installed"]}
    except Exception as e:
        logger.warning(f"Playwright extraction failed for {url}: {e}")
        return {"extraction_failed": True, "errors": [f"Playwright Error: {e}"]}

def validate_content(state: LeadDiscoveryState) -> LeadDiscoveryState:
    content = state.get("extracted_content")
    retry = state.get("retry_count", 0)
    
    if not content or len(content) < 50:
        return {"extraction_failed": True, "retry_count": retry + 1, "errors": ["Content too short or empty"]}
        
    if "captcha" in content.lower() or "access denied" in content.lower():
        return {"extraction_failed": True, "retry_count": retry + 1, "errors": ["Blocked by Captcha/WAF"]}
        
    return {"extraction_failed": False}

def prepare_next_url(state: LeadDiscoveryState) -> LeadDiscoveryState:
    idx = state.get("current_url_index", 0)
    urls = state.get("deduplicated_urls", [])
    
    if idx < len(urls):
        return {
            "current_url_data": urls[idx],
            "retry_count": 0,
            "extraction_failed": False,
            "is_qualified": False
        }
    return {"current_url_data": None}
