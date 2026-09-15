import urllib.parse
import httpx
import feedparser
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.connectors.base import BaseConnector
from app.schemas.unified import UnifiedSignal, SignalContent, SignalAuthor

class RedditConnector(BaseConnector):
    source_name = "reddit"
    source_type = "forum"

    def __init__(self):
        self.headers = {
            'User-Agent': 'OSYS Lead Intelligence Platform/1.0 (+https://osys.com)'
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=15.0)

    async def get_rate_limit(self) -> Dict[str, Any]:
        return {
            "requests_per_minute": 30, # Reddit's unauthenticated limit is typically ~10-30 RPM
            "cooldown_seconds": 2.0
        }

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("https://www.reddit.com/r/forhire.rss?limit=1")
            return resp.status_code == 200
        except Exception:
            return False

    async def discover(self, campaign: Any, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        In Phase 1, we simulate discovering raw signals using hardcoded queries.
        In later phases, `campaign` will contain dynamic intelligence.
        """
        raw_events = []
        queries = ["flair_name:\"Hiring\""]
        
        for query in queries:
            try:
                encoded_q = urllib.parse.quote_plus(query)
                url = f"https://www.reddit.com/r/forhire/search.rss?q={encoded_q}&restrict_sr=1&sort=new&limit=50"
                if cursor:
                    url += f"&after={cursor}"
                    
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        raw_events.append({
                            "external_id": f"reddit-{entry.id}",
                            "raw_payload": dict(entry),
                        })
            except Exception as e:
                print(f"Reddit Discover Error: {e}")
                
        return raw_events

    async def fetch(self, external_id: str) -> Dict[str, Any]:
        """
        For RSS, the discover phase usually returns the complete object.
        If we needed full comments, we would hit the Reddit JSON API here.
        """
        raise NotImplementedError("Fetch is not required for Reddit RSS since discover returns full payload.")

    async def normalize(self, raw_data: Dict[str, Any]) -> UnifiedSignal:
        payload = raw_data.get("raw_payload", {})
        
        # Parse Dates
        pub_date = datetime.now(timezone.utc)
        if payload.get("published_parsed"):
            pub_date = datetime.fromtimestamp(time.mktime(payload["published_parsed"]), timezone.utc)
            
        # Clean HTML
        desc = payload.get("description", "")
        clean_desc = re.sub(r'<[^>]+>', '', desc)
        
        return UnifiedSignal(
            source=self.source_name,
            source_type=self.source_type,
            external_id=raw_data["external_id"],
            external_url=payload.get("link", ""),
            content=SignalContent(
                title=payload.get("title", ""),
                body=clean_desc[:2000]
            ),
            author=SignalAuthor(
                username=payload.get("author", "Reddit User")
            ),
            published_at=pub_date,
            raw_event_id=uuid4(), # To be associated properly in the pipeline
            content_hash=str(hash(clean_desc[:2000]))
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
