import urllib.parse
import httpx
import feedparser
import re
import html
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=15.0)

    async def get_rate_limit(self) -> Dict[str, Any]:
        return {
            "requests_per_minute": 30,
            "cooldown_seconds": 2.0
        }

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("https://www.reddit.com/r/forhire/new.rss?limit=1", follow_redirects=True)
            return resp.status_code == 200
        except Exception:
            return False

    async def discover(self, campaign: Any, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        raw_events = []
        subs = ["forhire", "freelance_forhire", "jobbit", "techjobs"]
        
        for sub in subs:
            try:
                url = f"https://www.reddit.com/r/{sub}/new.rss?limit=50"
                if cursor:
                    url += f"&after={cursor}"
                    
                resp = await self.client.get(url, follow_redirects=True)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        title = entry.title
                        t_lower = title.lower()
                        if "[for hire]" in t_lower or "for hire" in t_lower or "hire me" in t_lower:
                            continue
                        if not any(k in t_lower for k in ["[hiring]", "hiring", "looking for", "need a", "paid"]):
                            continue
                        
                        link = getattr(entry, 'link', '')
                        if not link or "/comments/" not in link:
                            continue

                        raw_events.append({
                            "external_id": f"reddit-{entry.id if hasattr(entry, 'id') else link}",
                            "raw_payload": dict(entry),
                        })
            except Exception as e:
                print(f"Reddit Discover Error for r/{sub}: {e}")
                
        return raw_events

    async def fetch(self, external_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Fetch is not required for Reddit RSS since discover returns full payload.")

    async def normalize(self, raw_data: Dict[str, Any]) -> UnifiedSignal:
        payload = raw_data.get("raw_payload", {})
        
        # Parse Dates
        pub_date = datetime.now(timezone.utc)
        if payload.get("published_parsed"):
            pub_date = datetime.fromtimestamp(time.mktime(payload["published_parsed"]), timezone.utc)
            
        # Clean HTML
        desc = payload.get("description", "")
        clean_desc = re.sub(r'<[^>]+>', ' ', desc)
        clean_desc = html.unescape(" ".join(clean_desc.split()))
        
        link = payload.get("link", "")
        author = payload.get("author", "Reddit Client").replace("/u/", "")

        return UnifiedSignal(
            source=self.source_name,
            source_type=self.source_type,
            external_id=raw_data["external_id"],
            external_url=link,
            content=SignalContent(
                title=payload.get("title", ""),
                body=clean_desc[:2000]
            ),
            author=SignalAuthor(
                username=author
            ),
            published_at=pub_date,
            raw_event_id=uuid4(),
            content_hash=str(hash(clean_desc[:2000]))
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

