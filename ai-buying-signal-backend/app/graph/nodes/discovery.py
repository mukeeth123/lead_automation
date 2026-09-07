import json
import httpx
import logging
from typing import Dict, Any
from app.graph.discovery_state import LeadDiscoveryState
from app.agents.intelligence import call_llm_with_fallback

logger = logging.getLogger(__name__)

async def generate_queries(state: LeadDiscoveryState) -> LeadDiscoveryState:
    raw_query = state.get("search_queries", [""])[0]
    
    # Read the keyword database to inject into the LLM
    import os
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "agents", "keyword_database.md")
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            keyword_db = f.read()
    except Exception as e:
        logger.error(f"Failed to load keyword database: {e}")
        keyword_db = ""
    
    prompt = f"""You are an expert B2B lead generation query builder.
The user wants to find leads matching this natural language request: "{raw_query}"

Using the following proven Lead Intelligence Keyword Database as inspiration, generate 5 highly targeted, exact search engine queries. 
CRITICAL: You MUST use advanced search operators like quotes ("exact phrase") and site exclusions (-jobs) to ensure we find actual people asking for help, NOT agency landing pages or SEO lists.
Example: ["\"need an AI development company\" -jobs -course", "\"looking for a development partner\" AI automation", "site:linkedin.com/posts \"we are still doing this manually\""]

=== KEYWORD DATABASE ===
{keyword_db[:3000]}
========================

Return ONLY a valid JSON array of 5 strings. No markdown formatting.
"""
    try:
        full_prompt = "You return valid JSON.\n" + prompt
        messages = [{"role": "user", "content": full_prompt}]
        response = await call_llm_with_fallback(messages)
        queries = json.loads(response)
        if not isinstance(queries, list):
            queries = [str(q) for q in queries.values()]
        return {"search_queries": queries}
    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        fallback = [f'"{raw_query}"']
        return {"search_queries": fallback, "errors": [f"Query gen error: {e}"]}

async def discover_searxng(state: LeadDiscoveryState) -> LeadDiscoveryState:
    queries = state.get("search_queries", [])
    urls = []
    
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            for q in queries:
                try:
                    results = list(ddgs.text(q, max_results=10))
                    for r in results:
                        urls.append({
                            "url": r.get("href"),
                            "source": "searxng",
                            "title": r.get("title", ""),
                            "snippet": r.get("body", "")
                        })
                except Exception as e:
                    logger.error(f"DDG search error for {q}: {e}")
    except Exception as e:
        logger.error(f"DDGS init error: {e}")
        
    return {"discovered_urls": urls}

def merge_and_deduplicate(state: LeadDiscoveryState) -> LeadDiscoveryState:
    all_urls = state.get("discovered_urls", [])
    seen = set()
    deduped = []
    
    for item in all_urls:
        url = item.get("url", "")
        # Very basic canonicalization (strip query params if not reddit/hn item)
        canonical = url
        if "reddit.com" not in url and "news.ycombinator.com" not in url:
            canonical = url.split("?")[0].split("#")[0]
            
        if canonical not in seen:
            seen.add(canonical)
            deduped.append(item)
            
    # Also initialize the batch processing tracking here
    return {
        "deduplicated_urls": deduped,
        "current_url_index": 0,
        "errors": []
    }
