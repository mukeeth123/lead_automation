import json
import httpx
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class CompanyEnrichmentAgent:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def _fetch_url_content(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.extract()
                    text = soup.get_text(separator=' ', strip=True)
                    return text[:3000]
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
        return ""

    async def _search_web(self, query: str, num_results: int = 3) -> list:
        import urllib.request
        import urllib.parse
        from bs4 import BeautifulSoup
        url = f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}'
        req = urllib.request.Request(url, headers={'User-Agent': self.headers['User-Agent']})
        results = []
        try:
            html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href')
                if href and href.startswith('//duckduckgo.com/l/?uddg='):
                    actual_url = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                    if actual_url not in results:
                        results.append(actual_url)
                if len(results) >= num_results:
                    break
        except Exception as e:
            logger.error(f"DDG scrape error: {e}")
        return results

    async def search_and_analyze(self, query: str):
        search_query = f"{query} company official website"
        logger.info(f"Searching DDGS for: {search_query}")
        
        search_results = []
        try:
            urls = await self._search_web(search_query, 5)
            for url in urls:
                if url and not any(x in url for x in ["linkedin.com/in/", "facebook.com", "instagram.com", "tracxn.com", "crunchbase.com"]):
                    search_results.append(url)
                    if len(search_results) >= 2:
                        break
        except Exception as e:
            logger.error(f"Search failed: {e}")
            
        news_query = f'"{query}" company (news OR funding OR profit OR earnings) "2025" OR "2026"'
        logger.info(f"Searching DDGS for news: {news_query}")
        news_results = []
        try:
            urls = await self._search_web(news_query, 3)
            for url in urls:
                if url:
                    news_results.append(url)
        except Exception as e:
            logger.error(f"News Search failed: {e}")
            
        website_text = ""
        official_website = None
        if search_results:
            official_website = search_results[0]
            website_text = await self._fetch_url_content(official_website)
            
        news_text = ""
        for n_url in news_results:
            if n_url != official_website:
                news_text += f"\n--- News Source ({n_url}) ---\n"
                news_text += await self._fetch_url_content(n_url)
                
        import datetime
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
        # 3. Analyze with Groq
        prompt = f"""You are an expert sales engineer and technical architect evaluating a prospective company for an agency that builds:
1. AI Agents & LLM Automations
2. Voice AI Systems
3. Enterprise Custom Software Platforms

Target Company / Query: {query}
Current Date: {current_date}
Found Website: {official_website}
Scraped Website Content:
{website_text if website_text else "(No website content found.)"}

Scraped Recent News / Funding Data:
{news_text if news_text else "(No recent news found.)"}

Task:
Analyze this company and return a JSON object scoring them as an Ideal Customer Profile (ICP). 
Give higher scores (80-100) to companies in USA/Europe, non-tech traditional industries (law, logistics, real estate, ecommerce) that likely have manual workflows ripe for AI automation, or tech startups scaling rapidly. 

CRITICAL RULE FOR LATEST UPDATES:
Only extract news, funding, or product launches from the "Scraped Recent News" that occurred in 2025 or 2026. DO NOT hallucinate or include old news from 2021, 2022, 2023, or 2024. If there is no explicit recent news in the text provided, output exactly: ["No major news or funding announced recently."]

CRITICAL RULE FOR MULTIPLE COMPANIES / AMBIGUITY:
If the search results reveal multiple different companies that share this exact name, OR if the company name is very generic, do not just pick one randomly. Instead, explicitly mention the different companies found in the "description" field so the sales person is aware of the ambiguity (e.g. "Note: There are two companies named X. 1) A medical device company in Ireland and 2) A software company in NY. I am evaluating the medical device company."). Base the rest of your pitch on the one that seems most likely to be a B2B enterprise client.

Make sure the information provided is extremely actionable, specific, and easy for a sales person to read quickly before jumping on a cold call.

Return ONLY JSON matching this exact structure (no markdown tags like ```json):
{{
    "name": "Exact Full Company Name",
    "industry": "Primary Industry",
    "location": "City, Country (if known, else 'Unknown')",
    "description": "Thorough description of exactly what they do, their core offerings, and market focus. (Include disambiguation here if multiple companies share the name).",
    "tech_stack": ["List", "of", "likely", "technologies"],
    "key_executives": "E.g., CEO: Jane Doe, CTO: John Smith (if found, else 'Unknown')",
    "company_size": "E.g., 50-200 employees or 'Seed Stage' (if found, else 'Unknown')",
    "icp_score": 85,
    "latest_updates": [
        "Recent news from 2025/2026 ONLY, e.g., 'Raised $50M Series B in August 2026'",
        "Financial news, e.g., 'Reported 20% YoY profit growth'"
    ],
    "sales_triggers": [
        "Hiring for specific roles (e.g. AI Engineers)",
        "Recently expanded into new markets",
        "Just acquired another company"
    ],
    "pain_points": [
        "Specific manual workflow or pain point 1",
        "Specific manual workflow or pain point 2"
    ],
    "pitch_recommendations": [
        "Pitch 1: Detail a specific AI agent or platform you could build for them",
        "Pitch 2: ...",
        "Pitch 3: ..."
    ]
}}
"""
        
        try:
            from app.agents.intelligence import groq_client, GROQ_MODEL
            response = await groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert sales engineer analyzing companies."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            analysis = json.loads(response.choices[0].message.content)
            if official_website and analysis:
                analysis["website"] = official_website
            
            analysis["raw_context"] = f"Website Data:\n{website_text}\n\nNews Data:\n{news_text}"
            return analysis
        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return None
